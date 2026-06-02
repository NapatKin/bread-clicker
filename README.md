# 🍞 Bread Clicker — The Hard One

A punishingly hard idle clicker built with Python + Pygame.

## Features
- 12 buildings from Grain Seed → Bread Dimension
- 20+ upgrades (click, building, global, prestige)
- Prestige system — reset for permanent multipliers (costs 1 quadrillion bread minimum)
- News ticker, particle effects, milestone banners, bounce animation
- Auto-save every 10 seconds

## How to run

```bash
pip install -r requirements.txt
python bread_clicker.py
```

## Controls
| Input | Action |
|-------|--------|
| Click the bread | Bake bread |
| Click a building row | Buy that building |
| `1` / `2` | Switch tabs (Buildings / Upgrades) |
| Mouse scroll | Scroll lists |
| `Esc` | Save & quit |

## How hard is it?
- Prestige 1 requires **1 quadrillion** total bread
- Prestige 2 requires **10 quadrillion**, and so on
- Later upgrades cost up to **100 trillion** bread each
- Building costs scale at 1.15× per purchase

## Putting this on GitHub — step by step

1. **Create a new repo on GitHub**
   - Go to https://github.com/new
   - Name it `bread-clicker`, set it to Public, click **Create repository**

2. **Open a terminal in this folder**
   ```
   cd "C:\Users\napat\Downloads\bread clicker"
   ```

3. **Initialise git and push**
   ```bash
   git init
   git add bread_clicker.py requirements.txt .gitignore README.md
   git commit -m "Initial commit: Bread Clicker"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/bread-clicker.git
   git push -u origin main
   ```
   Replace `YOUR_USERNAME` with your actual GitHub username.

4. **Done!**  Your game is live at `https://github.com/YOUR_USERNAME/bread-clicker`
