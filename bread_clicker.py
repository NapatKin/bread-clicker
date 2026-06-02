import pygame
import sys
import json
import os
import math
import random
from dataclasses import dataclass, field
from typing import List

pygame.init()

# ── constants ──────────────────────────────────────────────────────────────────
W, H = 1280, 800
FPS = 60
SAVE_FILE = "save.json"

# colours
BG       = (30,  20,  10)
PANEL_L  = (50,  35,  15)
PANEL_R  = (40,  28,  12)
GOLD     = (255, 210,  60)
WHEAT    = (220, 180,  80)
CREAM    = (255, 245, 220)
BROWN    = (120,  70,  20)
DARK_BR  = ( 60,  35,   8)
RED      = (210,  50,  50)
GREEN    = ( 60, 180,  60)
BLUE     = ( 80, 140, 220)
PURPLE   = (160,  80, 220)
ORANGE   = (230, 130,  30)
GREY     = (140, 130, 120)
WHITE    = (255, 255, 255)
BLACK    = (  0,   0,   0)

# ── fonts ──────────────────────────────────────────────────────────────────────
F_HUGE  = pygame.font.SysFont("arial", 48, bold=True)
F_BIG   = pygame.font.SysFont("arial", 28, bold=True)
F_MED   = pygame.font.SysFont("arial", 20, bold=True)
F_SMALL = pygame.font.SysFont("arial", 15)
F_TINY  = pygame.font.SysFont("arial", 12)

# ── helpers ────────────────────────────────────────────────────────────────────
def fmt(n: float) -> str:
    tiers = [
        (1e63, "Vi"), (1e60, "No"), (1e57, "Oc"), (1e54, "Sp"), (1e51, "Sx"),
        (1e48, "Qi"), (1e45, "Qd"), (1e42, "Td"), (1e39, "Du"), (1e36, "Un"),
        (1e33, "De"), (1e30, "No"), (1e27, "Oc"), (1e24, "Sp"), (1e21, "Sx"),
        (1e18, "Qi"), (1e15, "Qd"), (1e12, "T"),  (1e9,  "B"),  (1e6,  "M"),
        (1e3,  "K"),
    ]
    for div, suffix in tiers:
        if n >= div:
            return f"{n/div:.2f}{suffix}"
    return f"{int(n):,}"

def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

# ── upgrade / building data ────────────────────────────────────────────────────
@dataclass
class Building:
    name:        str
    desc:        str
    base_cost:   float
    base_bps:    float   # bread per second
    count:       int = 0
    emoji:       str = "🏗"

    @property
    def cost(self) -> float:
        return self.base_cost * (1.15 ** self.count)

    @property
    def bps(self) -> float:
        return self.base_bps * self.count

BUILDINGS_TEMPLATE = [
    Building("Grain Seed",      "A tiny seed.  Barely anything.",               10,       0.1,  emoji="🌾"),
    Building("Wheat Field",     "Rows of golden wheat sway gently.",             100,      0.5,  emoji="🌿"),
    Building("Windmill",        "Grinds wheat into coarse flour.",               1_200,    4,    emoji="🌀"),
    Building("Bakery Oven",     "Stone oven.  Bakes all day.",                   10_000,   20,   emoji="🔥"),
    Building("Flour Mill",      "Industrial-grade milling.",                     1e5,      80,   emoji="⚙️"),
    Building("Bread Factory",   "Assembly line of loaves.",                      1e6,      300,  emoji="🏭"),
    Building("Grain Silo",      "Stores vast reserves of grain.",                1.2e7,    1_200,emoji="🏗"),
    Building("Bread Portal",    "Bread arrives from another dimension.",         1.5e8,    5_000,emoji="🌀"),
    Building("Yeast Lab",       "Bioengineered ultra-yeast.",                    2e9,      20_000,emoji="🧪"),
    Building("Bread Planet",    "Entire planet covered in baking bread.",        3e10,     80_000,emoji="🌍"),
    Building("Bread Star",      "Nuclear fusion powers endless baking.",         4e11,     300_000,emoji="⭐"),
    Building("Bread Dimension", "Reality itself is made of bread.",              5e12,     1e6,  emoji="🌌"),
]

@dataclass
class Upgrade:
    name:         str
    desc:         str
    cost:         float
    unlock_cond:  str   # eval'd against game state dict
    effect_desc:  str
    bought:       bool = False
    category:     str  = "click"   # click | building | global | prestige
    color:        tuple = field(default_factory=lambda: GOLD)

UPGRADES_TEMPLATE = [
    # ── click upgrades ─────────────────────────────────────────────────────────
    Upgrade("Calloused Hands",   "You click harder.",               100,       "bread>=50",       "+1 bread/click",      category="click",  color=WHEAT),
    Upgrade("Knead Mastery",     "Dough yields to your will.",       2_000,     "bread>=1000",     "+5 bread/click",      category="click",  color=WHEAT),
    Upgrade("Iron Fists",        "Fists of steel, bread of gold.",   30_000,    "bread>=15000",    "+20 bread/click",     category="click",  color=ORANGE),
    Upgrade("Bread Fury",        "Berserk clicking mode.",           500_000,   "bread>=250000",   "+50 bread/click",     category="click",  color=RED),
    Upgrade("Quantum Click",     "Each click is in superposition.", 1e7,       "bread>=5e6",      "+200 bread/click",    category="click",  color=BLUE),
    Upgrade("Bread Singularity", "Click transcends time.",          1e9,       "bread>=5e8",      "+1000 bread/click",   category="click",  color=PURPLE),
    Upgrade("Godly Kneading",    "You ARE the bread.",              1e11,      "bread>=5e10",     "+5000 bread/click",   category="click",  color=PURPLE),

    # ── building multipliers ────────────────────────────────────────────────────
    Upgrade("Fertilizer",     "Grain seeds x2.",              500,       "b_Grain_Seed>=1",       "Grain Seed x2",       category="building", color=GREEN),
    Upgrade("Wind Vanes",     "Windmills x2.",                5_000,     "b_Windmill>=5",         "Windmill x2",         category="building", color=GREEN),
    Upgrade("Brick Lining",   "Ovens x2.",                    50_000,    "b_Bakery_Oven>=5",      "Oven x2",             category="building", color=GREEN),
    Upgrade("Conveyor Belt",  "Factories x3.",                2e6,       "b_Bread_Factory>=10",   "Factory x3",          category="building", color=GREEN),
    Upgrade("Dimensional Rift","Portals x5.",                 5e8,       "b_Bread_Portal>=10",    "Portal x5",           category="building", color=BLUE),
    Upgrade("Stellar Core",   "Stars x5.",                   5e11,      "b_Bread_Star>=10",      "Star x5",             category="building", color=BLUE),

    # ── global multipliers ─────────────────────────────────────────────────────
    Upgrade("Sourdough Secret",  "All bps x1.5.",             1e4,       "total_bread>=5000",     "All BPS x1.5",        category="global", color=ORANGE),
    Upgrade("Artisan Yeast",     "All bps x2.",               1e6,       "total_bread>=5e5",      "All BPS x2",          category="global", color=ORANGE),
    Upgrade("Golden Loaf",       "All bps x2, click x2.",     1e8,       "total_bread>=5e7",      "BPS & Click x2",      category="global", color=GOLD),
    Upgrade("Bread Gospel",      "All bps x3.",               1e10,      "total_bread>=5e9",      "All BPS x3",          category="global", color=GOLD),
    Upgrade("Infinite Crumbs",   "All bps x5.",               1e12,      "total_bread>=5e11",     "All BPS x5",          category="global", color=PURPLE),
    Upgrade("Omega Gluten",      "Everything x10.",           1e14,      "total_bread>=5e13",     "Everything x10",      category="global", color=PURPLE),

    # ── prestige tier (very hard) ──────────────────────────────────────────────
    Upgrade("Ascended Crust",    "Prestige bonus x1.5.",      1e16,      "prestige>=1",           "Prestige x1.5",       category="prestige", color=PURPLE),
    Upgrade("Bread Nirvana",     "Prestige bonus x3.",        1e18,      "prestige>=3",           "Prestige x3",         category="prestige", color=PURPLE),
]

# ── particle system ────────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, text):
        self.x  = x + random.randint(-20, 20)
        self.y  = y
        self.vy = -2.5 - random.random() * 1.5
        self.vx = random.uniform(-0.6, 0.6)
        self.text = text
        self.life = 1.0
        self.color = GOLD

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.life -= 0.022

    def draw(self, surf):
        if self.life <= 0:
            return
        alpha = max(0, int(self.life * 255))
        col = (*self.color[:3], alpha)
        s = F_MED.render(self.text, True, self.color)
        s.set_alpha(alpha)
        surf.blit(s, (int(self.x), int(self.y)))

# ── news ticker messages ───────────────────────────────────────────────────────
NEWS = [
    "LOCAL BAKER DISAPPEARS AFTER MAKING 1 MILLION LOAVES",
    "SCIENTISTS BAFFLED: BREAD NOW APPEARS SPONTANEOUSLY",
    "WHEAT PRICES COLLAPSE AS BREAD FLOODS MARKET",
    "GOVERNMENT DECLARES BREAD NATIONAL CURRENCY",
    "PHILOSOPHER ASKS: IS THE BREAD BAKING US?",
    "BREAD DIMENSION DISCOVERED — PHYSICISTS RESIGN",
    "AREA MAN CLICKS BREAD FOR 18TH CONSECUTIVE HOUR",
    "YEAST ACHIEVES SENTIENCE, DEMANDS BETTER CONDITIONS",
    "BREAD PLANET VISIBLE FROM EARTH WITH NAKED EYE",
    "GLUTEN DECLARED CONTROLLED SUBSTANCE IN 12 COUNTRIES",
    "BREAD STAR GOES SUPERNOVA: UNIVERSE NOW SMELLS AMAZING",
    "LOCAL OVEN UNIONISES — DEMANDS LONGER REST PERIODS",
]

# ── main game class ────────────────────────────────────────────────────────────
class BreadClicker:
    def __init__(self):
        self.screen  = pygame.display.set_mode((W, H))
        pygame.display.set_caption("🍞  BREAD CLICKER  — THE HARD ONE")
        self.clock   = pygame.time.Clock()

        # game state
        self.bread        = 0.0
        self.total_bread  = 0.0
        self.prestige     = 0
        self.prestige_mult= 1.0
        self.click_power  = 1.0
        self.bps_mult     = 1.0

        self.buildings  = [Building(b.name, b.desc, b.base_cost, b.base_bps, emoji=b.emoji) for b in BUILDINGS_TEMPLATE]
        self.upgrades   = list(UPGRADES_TEMPLATE)  # shallow copy; bought flags start False

        # UI state
        self.particles    : List[Particle] = []
        self.btn_rect     = pygame.Rect(90, 260, 220, 220)
        self.btn_anim     = 0.0   # 0..1 press scale
        self.scroll_up    = 0     # building list scroll
        self.scroll_up2   = 0     # upgrade list scroll
        self.tab          = "buildings"  # buildings | upgrades

        # news ticker
        self.news_idx     = 0
        self.news_x       = W
        self.news_text    = NEWS[0]
        self.news_timer   = 0

        # milestone flash
        self.milestone_msg  = ""
        self.milestone_timer = 0

        # bread bounce
        self.bounce_y     = 0.0
        self.bounce_vel   = 0.0

        self.load()

    # ── save / load ────────────────────────────────────────────────────────────
    def save(self):
        data = {
            "bread":       self.bread,
            "total_bread": self.total_bread,
            "prestige":    self.prestige,
            "buildings":   [b.count for b in self.buildings],
            "upgrades":    [u.bought for u in self.upgrades],
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)

    def load(self):
        if not os.path.exists(SAVE_FILE):
            return
        try:
            with open(SAVE_FILE) as f:
                d = json.load(f)
            self.bread       = d.get("bread", 0)
            self.total_bread = d.get("total_bread", 0)
            self.prestige    = d.get("prestige", 0)
            for i, c in enumerate(d.get("buildings", [])):
                if i < len(self.buildings):
                    self.buildings[i].count = c
            for i, b in enumerate(d.get("upgrades", [])):
                if i < len(self.upgrades):
                    self.upgrades[i].bought = b
            self._recalc_multipliers()
        except Exception:
            pass  # corrupt save → start fresh

    # ── multiplier recalc ──────────────────────────────────────────────────────
    def _recalc_multipliers(self):
        self.click_power  = 1.0
        self.bps_mult     = 1.0
        self.prestige_mult= 1.0 + 0.1 * self.prestige

        b_counts = {("b_" + b.name.replace(" ", "_")): b.count for b in self.buildings}
        state = {"bread": self.bread, "total_bread": self.total_bread, "prestige": self.prestige, **b_counts}

        for u in self.upgrades:
            if not u.bought:
                continue
            eff = u.effect_desc
            if "+1 bread/click"    in eff: self.click_power += 1
            elif "+5 bread/click"  in eff: self.click_power += 5
            elif "+20 bread/click" in eff: self.click_power += 20
            elif "+50 bread/click" in eff: self.click_power += 50
            elif "+200 bread/click"in eff: self.click_power += 200
            elif "+1000 bread/click"in eff:self.click_power += 1000
            elif "+5000 bread/click"in eff:self.click_power += 5000
            elif "BPS x1.5"        in eff: self.bps_mult    *= 1.5
            elif "All BPS x2"      in eff: self.bps_mult    *= 2
            elif "All BPS x3"      in eff: self.bps_mult    *= 3
            elif "All BPS x5"      in eff: self.bps_mult    *= 5
            elif "Everything x10"  in eff: self.bps_mult    *= 10; self.click_power *= 10
            elif "BPS & Click x2"  in eff: self.bps_mult    *= 2;  self.click_power *= 2
            elif "Prestige x1.5"   in eff: self.prestige_mult *= 1.5
            elif "Prestige x3"     in eff: self.prestige_mult *= 3

        self.bps_mult *= self.prestige_mult

    # ── per-building multiplier (upgrades that double a specific building) ─────
    def _building_mult(self, b_name: str) -> float:
        key = b_name.replace(" ", "_")
        mult = 1.0
        for u in self.upgrades:
            if not u.bought:
                continue
            e = u.effect_desc
            if b_name in e or key in e:
                if "x2" in e: mult *= 2
                elif "x3" in e: mult *= 3
                elif "x5" in e: mult *= 5
        return mult

    # ── bps calculation ────────────────────────────────────────────────────────
    @property
    def bps(self) -> float:
        total = sum(b.base_bps * b.count * self._building_mult(b.name) for b in self.buildings)
        return total * self.bps_mult

    # ── clicking ──────────────────────────────────────────────────────────────
    def do_click(self, mx, my):
        if not self.btn_rect.collidepoint(mx, my):
            return
        gain = self.click_power * self.prestige_mult
        # small bonus: 1% of bps per click
        gain += self.bps * 0.01
        self.bread       += gain
        self.total_bread += gain
        self.btn_anim     = 0.3
        self.bounce_vel   = -6
        p = Particle(self.btn_rect.centerx, self.btn_rect.top, f"+{fmt(gain)}")
        self.particles.append(p)
        self._check_milestones()

    # ── prestige ───────────────────────────────────────────────────────────────
    def try_prestige(self):
        required = 1e15 * (10 ** self.prestige)
        if self.total_bread < required:
            self.milestone_msg   = f"Need {fmt(required)} total bread to prestige!"
            self.milestone_timer = 180
            return
        self.prestige    += 1
        self.bread        = 0
        self.total_bread  = 0
        for b in self.buildings:
            b.count = 0
        for u in self.upgrades:
            if u.category != "prestige":
                u.bought = False
        self._recalc_multipliers()
        self.milestone_msg   = f"✨ PRESTIGE {self.prestige}! Bonus x{self.prestige_mult:.2f}"
        self.milestone_timer = 300
        self.save()

    # ── milestones ─────────────────────────────────────────────────────────────
    MILESTONES = [1e3,1e4,1e5,1e6,1e7,1e8,1e9,1e10,1e12,1e14,1e15,1e18,1e21]
    _hit_milestones = set()

    def _check_milestones(self):
        for m in self.MILESTONES:
            if self.total_bread >= m and m not in self._hit_milestones:
                self._hit_milestones.add(m)
                self.milestone_msg   = f"🍞 {fmt(m)} total bread baked!"
                self.milestone_timer = 200

    # ── upgrade buying ─────────────────────────────────────────────────────────
    def try_buy_upgrade(self, idx: int):
        u = self.upgrades[idx]
        if u.bought or self.bread < u.cost:
            return
        b_counts = {("b_" + b.name.replace(" ", "_")): b.count for b in self.buildings}
        state = {"bread": self.bread, "total_bread": self.total_bread, "prestige": self.prestige, **b_counts}
        try:
            unlocked = eval(u.unlock_cond, {"__builtins__": {}}, state)
        except Exception:
            unlocked = False
        if not unlocked:
            return
        self.bread  -= u.cost
        u.bought     = True
        self._recalc_multipliers()
        self.milestone_msg   = f"Bought: {u.name}!"
        self.milestone_timer = 150
        self.save()

    # ── building buying ────────────────────────────────────────────────────────
    def try_buy_building(self, idx: int):
        b = self.buildings[idx]
        if self.bread < b.cost:
            return
        self.bread  -= b.cost
        b.count     += 1
        self._recalc_multipliers()
        self.save()

    # ── update ─────────────────────────────────────────────────────────────────
    _save_timer = 0
    _ms_since_last = 0

    def update(self, dt_ms: int):
        dt = dt_ms / 1000.0
        gain = self.bps * dt
        self.bread       += gain
        self.total_bread += gain
        self._check_milestones()

        # btn animation
        if self.btn_anim > 0:
            self.btn_anim = max(0, self.btn_anim - 0.04)

        # bread bounce physics
        self.bounce_vel += 0.8
        self.bounce_y   += self.bounce_vel
        if self.bounce_y > 0:
            self.bounce_y   = 0
            self.bounce_vel = 0

        # particles
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]

        # milestone timer
        if self.milestone_timer > 0:
            self.milestone_timer -= 1

        # news ticker
        self.news_x -= 2
        rendered_w = F_SMALL.size(self.news_text)[0]
        if self.news_x < -rendered_w:
            self.news_idx  = (self.news_idx + 1) % len(NEWS)
            self.news_text = NEWS[self.news_idx]
            self.news_x    = W

        # auto-save every 10s
        self._save_timer += dt_ms
        if self._save_timer >= 10_000:
            self._save_timer = 0
            self.save()

    # ── draw helpers ───────────────────────────────────────────────────────────
    def _draw_text(self, surf, text, font, color, x, y, center=False):
        s = font.render(str(text), True, color)
        if center:
            x -= s.get_width() // 2
        surf.blit(s, (x, y))

    def _draw_panel(self, surf, rect, color, border=2):
        pygame.draw.rect(surf, color, rect, border_radius=8)
        pygame.draw.rect(surf, GOLD, rect, border, border_radius=8)

    def _draw_btn(self, surf, rect, label, color, hover=False):
        c = lerp_color(color, WHITE, 0.15) if hover else color
        self._draw_panel(surf, rect, c)
        self._draw_text(surf, label, F_SMALL, WHITE, rect.centerx, rect.centery - 7, center=True)

    # ── main draw ──────────────────────────────────────────────────────────────
    def draw(self):
        surf = self.screen
        surf.fill(BG)
        mx, my = pygame.mouse.get_pos()

        # ── left panel (bread button area) ────────────────────────────────────
        left = pygame.Rect(0, 0, 320, H - 30)
        self._draw_panel(surf, left, PANEL_L)

        # bread count
        self._draw_text(surf, fmt(self.bread), F_HUGE, GOLD, 160, 18, center=True)
        self._draw_text(surf, "bread", F_MED, WHEAT, 160, 70, center=True)
        self._draw_text(surf, f"per sec: {fmt(self.bps)}", F_SMALL, CREAM, 160, 96, center=True)
        self._draw_text(surf, f"per click: {fmt(self.click_power * self.prestige_mult)}", F_SMALL, CREAM, 160, 114, center=True)
        self._draw_text(surf, f"total: {fmt(self.total_bread)}", F_TINY, GREY, 160, 132, center=True)

        # prestige info
        if self.prestige > 0:
            self._draw_text(surf, f"✨ Prestige {self.prestige}  (x{self.prestige_mult:.1f})", F_TINY, PURPLE, 160, 148, center=True)

        # bread button (animated)
        scale = 1.0 - self.btn_anim * 0.12
        bw = int(220 * scale)
        bh = int(220 * scale)
        bx = self.btn_rect.centerx - bw // 2
        by = int(self.btn_rect.centery + self.bounce_y) - bh // 2
        hover_btn = self.btn_rect.collidepoint(mx, my)

        # glow
        if hover_btn:
            glow_surf = pygame.Surface((bw + 30, bh + 30), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surf, (255, 210, 60, 40), (0, 0, bw+30, bh+30))
            surf.blit(glow_surf, (bx - 15, by - 15))

        # bread circle
        c = (180, 110, 30) if not hover_btn else (210, 140, 50)
        pygame.draw.ellipse(surf, c,           (bx, by, bw, bh))
        pygame.draw.ellipse(surf, (230, 170, 80), (bx+10, by+10, bw-20, bh//3))
        pygame.draw.ellipse(surf, DARK_BR,     (bx, by, bw, bh), 4)

        self._draw_text(surf, "🍞", F_HUGE, GOLD, self.btn_rect.centerx, by + bh//2 - 28, center=True)
        self._draw_text(surf, "CLICK", F_MED, CREAM, self.btn_rect.centerx, by + bh - 36, center=True)

        # prestige button
        p_req = 1e15 * (10 ** self.prestige)
        p_rect = pygame.Rect(20, 510, 280, 36)
        can_prestige = self.total_bread >= p_req
        pc = PURPLE if can_prestige else DARK_BR
        self._draw_panel(surf, p_rect, pc)
        label = f"PRESTIGE ({fmt(p_req)} needed)" if not can_prestige else "✨ PRESTIGE NOW!"
        self._draw_text(surf, label, F_TINY, WHITE if can_prestige else GREY, p_rect.centerx, p_rect.centery - 7, center=True)

        # milestone banner
        if self.milestone_timer > 0:
            alpha = min(255, self.milestone_timer * 3)
            ms_surf = F_MED.render(self.milestone_msg, True, GOLD)
            ms_surf.set_alpha(alpha)
            surf.blit(ms_surf, (160 - ms_surf.get_width()//2, 560))

        # particles
        for p in self.particles:
            p.draw(surf)

        # ── right panel ───────────────────────────────────────────────────────
        right_x = 330
        right_w  = W - right_x - 10
        right    = pygame.Rect(right_x, 0, right_w, H - 30)
        self._draw_panel(surf, right, PANEL_R)

        # tabs
        tab_w = right_w // 2
        for i, t in enumerate(["buildings", "upgrades"]):
            tr = pygame.Rect(right_x + i * tab_w, 0, tab_w, 36)
            tc = DARK_BR if self.tab != t else PANEL_R
            self._draw_panel(surf, tr, tc)
            self._draw_text(surf, t.upper(), F_MED, GOLD if self.tab == t else GREY, tr.centerx, 8, center=True)

        list_top   = 44
        row_h      = 72
        visible_h  = H - list_top - 50

        if self.tab == "buildings":
            self._draw_buildings(surf, right_x, list_top, right_w, row_h, visible_h, mx, my)
        else:
            self._draw_upgrades(surf, right_x, list_top, right_w, mx, my)

        # ── news ticker ───────────────────────────────────────────────────────
        ticker = pygame.Rect(0, H - 30, W, 30)
        pygame.draw.rect(surf, DARK_BR, ticker)
        pygame.draw.line(surf, GOLD, (0, H - 30), (W, H - 30), 1)
        news_s = F_SMALL.render("📰 " + self.news_text, True, WHEAT)
        surf.blit(news_s, (int(self.news_x), H - 24))

        pygame.display.flip()

    def _draw_buildings(self, surf, rx, top, rw, row_h, visible_h, mx, my):
        b_counts = {("b_" + b.name.replace(" ", "_")): b.count for b in self.buildings}
        state    = {"bread": self.bread, "total_bread": self.total_bread, "prestige": self.prestige, **b_counts}

        scroll_px = self.scroll_up * row_h
        clip = pygame.Rect(rx, top, rw, visible_h)
        surf.set_clip(clip)

        for i, b in enumerate(self.buildings):
            y = top + i * row_h - scroll_px
            if y + row_h < top or y > top + visible_h:
                continue
            row = pygame.Rect(rx + 4, y + 2, rw - 8, row_h - 4)
            can  = self.bread >= b.cost
            hover= row.collidepoint(mx, my)
            bg   = (70, 50, 18) if can else (40, 28, 10)
            if hover and can:
                bg = (90, 65, 22)
            self._draw_panel(surf, row, bg)

            # emoji + name
            self._draw_text(surf, b.emoji, F_BIG, WHITE, rx + 14, y + 8)
            self._draw_text(surf, b.name, F_MED, GOLD if can else GREY, rx + 58, y + 6)
            self._draw_text(surf, b.desc, F_TINY, CREAM, rx + 58, y + 26)
            # bps / cost
            self._draw_text(surf, f"BPS: {fmt(b.base_bps * self._building_mult(b.name))} each", F_TINY, GREEN, rx + 58, y + 42)
            cost_c = GOLD if can else RED
            self._draw_text(surf, f"Cost: {fmt(b.cost)}", F_SMALL, cost_c, rx + 58, y + 54)
            # count badge
            badge = pygame.Rect(rx + rw - 62, y + 14, 50, 32)
            self._draw_panel(surf, badge, DARK_BR)
            self._draw_text(surf, str(b.count), F_BIG, WHITE, badge.centerx, badge.centery - 10, center=True)

        surf.set_clip(None)

        # scroll arrows
        if self.scroll_up > 0:
            self._draw_text(surf, "▲ scroll up", F_TINY, GREY, rx + rw // 2, top - 14, center=True)
        max_scroll = max(0, len(self.buildings) - int(visible_h // row_h))
        if self.scroll_up < max_scroll:
            self._draw_text(surf, "▼ scroll down", F_TINY, GREY, rx + rw // 2, top + visible_h + 2, center=True)

    def _draw_upgrades(self, surf, rx, top, rw, mx, my):
        b_counts = {("b_" + b.name.replace(" ", "_")): b.count for b in self.buildings}
        state    = {"bread": self.bread, "total_bread": self.total_bread, "prestige": self.prestige, **b_counts}

        row_h    = 62
        visible_h= H - top - 50
        scroll_px= self.scroll_up2 * row_h
        clip = pygame.Rect(rx, top, rw, visible_h)
        surf.set_clip(clip)

        shown = 0
        for i, u in enumerate(self.upgrades):
            if u.bought:
                continue
            try:
                unlocked = eval(u.unlock_cond, {"__builtins__": {}}, state)
            except Exception:
                unlocked = False
            if not unlocked:
                continue
            y = top + shown * row_h - scroll_px
            shown += 1
            if y + row_h < top or y > top + visible_h:
                continue
            row  = pygame.Rect(rx + 4, y + 2, rw - 8, row_h - 4)
            can  = self.bread >= u.cost
            hover= row.collidepoint(mx, my)
            bg   = (55, 40, 80) if can else (40, 28, 55)
            if hover and can:
                bg = (75, 55, 100)
            self._draw_panel(surf, row, bg)
            pygame.draw.rect(surf, u.color, (rx+4, y+2, 5, row_h-4), border_radius=4)

            self._draw_text(surf, u.name, F_MED, u.color, rx+18, y+5)
            self._draw_text(surf, u.desc, F_TINY, CREAM,  rx+18, y+24)
            self._draw_text(surf, u.effect_desc, F_TINY, GREEN,  rx+18, y+38)
            cost_c = GOLD if can else RED
            self._draw_text(surf, f"Cost: {fmt(u.cost)}", F_SMALL, cost_c, rx+rw-130, y+20)

        if shown == 0:
            self._draw_text(surf, "No upgrades available yet.", F_MED, GREY, rx + rw//2, top + 80, center=True)
            self._draw_text(surf, "Bake more bread!", F_SMALL, GREY, rx + rw//2, top + 110, center=True)

        surf.set_clip(None)

    # ── event handling ─────────────────────────────────────────────────────────
    def handle_events(self):
        mx, my = pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.save()
                pygame.quit()
                sys.exit()

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.save()
                    pygame.quit()
                    sys.exit()
                # tab switch
                if ev.key == pygame.K_1: self.tab = "buildings"
                if ev.key == pygame.K_2: self.tab = "upgrades"

            if ev.type == pygame.MOUSEBUTTONDOWN:
                bx, by_ = ev.pos

                # bread click
                if self.btn_rect.collidepoint(bx, by_):
                    self.do_click(bx, by_)

                # prestige
                p_rect = pygame.Rect(20, 510, 280, 36)
                if p_rect.collidepoint(bx, by_):
                    self.try_prestige()

                # tab clicks
                tab_w = (W - 340) // 2
                if 0 <= by_ <= 36:
                    for i, t in enumerate(["buildings", "upgrades"]):
                        tr = pygame.Rect(330 + i * tab_w, 0, tab_w, 36)
                        if tr.collidepoint(bx, by_):
                            self.tab = t

                # building clicks
                if self.tab == "buildings":
                    row_h    = 72
                    visible_h= H - 94
                    list_top = 44
                    for i, b in enumerate(self.buildings):
                        y = list_top + i * row_h - self.scroll_up * row_h
                        row = pygame.Rect(334, y + 2, W - 344, row_h - 4)
                        if row.collidepoint(bx, by_):
                            self.try_buy_building(i)

                # upgrade clicks
                if self.tab == "upgrades":
                    b_counts = {("b_" + b.name.replace(" ", "_")): b.count for b in self.buildings}
                    state    = {"bread": self.bread, "total_bread": self.total_bread, "prestige": self.prestige, **b_counts}
                    row_h    = 62
                    list_top = 44
                    shown    = 0
                    for i, u in enumerate(self.upgrades):
                        if u.bought:
                            continue
                        try:
                            unlocked = eval(u.unlock_cond, {"__builtins__": {}}, state)
                        except Exception:
                            unlocked = False
                        if not unlocked:
                            continue
                        y = list_top + shown * row_h - self.scroll_up2 * row_h
                        shown += 1
                        row = pygame.Rect(334, y + 2, W - 344, row_h - 4)
                        if row.collidepoint(bx, by_):
                            self.try_buy_upgrade(i)

            if ev.type == pygame.MOUSEWHEEL:
                if mx > 320:
                    if self.tab == "buildings":
                        max_s = max(0, len(self.buildings) - 9)
                        self.scroll_up = max(0, min(max_s, self.scroll_up - ev.y))
                    else:
                        max_s = max(0, len(self.upgrades) - 9)
                        self.scroll_up2 = max(0, min(max_s, self.scroll_up2 - ev.y))

    # ── main loop ──────────────────────────────────────────────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update(dt)
            self.draw()


if __name__ == "__main__":
    game = BreadClicker()
    game.run()
