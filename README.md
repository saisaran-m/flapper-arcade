# 🐦 Forest Flapper Arcade

A beautifully crafted Flappy Bird-style arcade game built entirely in Python with Pygame. Features stunning hand-drawn pixel art, 4 unique game modes, dynamic weather, a day-night cycle, and procedurally generated sound effects.

## 🎮 Play & Download

[![Play Online in Browser](https://img.shields.io/badge/Play%20Online-Web%20Version-brightgreen?style=for-the-badge&logo=google-chrome&logoColor=white)](https://saisaran-m.github.io/flapper-arcade/)
[![Download Android APK](https://img.shields.io/badge/Download-Android%20APK-blue?style=for-the-badge&logo=android&logoColor=white)](https://github.com/saisaran-m/flapper-arcade/releases/download/latest/app-debug.apk)

---

## ✨ Features

### 🎮 4 Game Modes
- **🌲 Forest** — Lush nature with a dynamic 4-stage weather cycle: Morning (Clear), Evening (Sunset), Rain (Stormy overcast & lightning), and Wind (Gale-force sweeps with 1.35x speedup & turbulence). Includes an animated river.
- **🌃 Synthwave** — Retro neon aesthetic with scanline sun, grid mountains, and pulsing cyan/magenta pipes
- **🏙️ City** — Urban skyline with animated buildings, traffic, and industrial steel girder obstacles
- **❄️ Winter** — Snowy landscape with falling snowflakes, frost-tinted trees, and howling wind

### 🎯 Gameplay Systems
- **Difficulty Progression** — 4 tiers (Easy → Medium → Hard → Insane) with increasing speed and shrinking gaps
- **Flying Obstacles** — Animated birds and bats that fly across the screen at higher difficulties
- **Power-Ups** — Shield (absorbs one hit) and Slow-Mo (halves game speed for 5 seconds)
- **Coin Economy** — Collect coins mid-flight to unlock premium bird skins

### 🐦 Unlockable Skins
- Classic, Ninja, Mech, and Phoenix — each with unique particle trail effects

### 🔊 Procedural Audio
- All sounds synthesized from pure math — no external audio files needed
- Dynamic music intensity that scales with difficulty tier
- Mode-specific ambient soundscapes (forest wind, synthwave beats, city traffic, winter gale)

### 📊 Progression
- Persistent player profiles with lifetime coin tracking
- Local leaderboard with multiple player support
- High score tracking per player

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Pygame 2.0 or higher

### Installation

```bash
# Clone the repository
git clone https://github.com/saisaran-m/flapper-arcade.git
cd flapper-arcade

# Install dependencies
pip install pygame

# Generate sound effects (first time only)
python generate_sounds.py

# Run the game!
python main.py
```

### Controls
| Key | Action |
|-----|--------|
| `SPACE` / `Click` | Flap / Select |
| `V` | Cycle volume (50% → 100% → Mute → 20%) |
| `ESC` | Back to menu |

---

## 📁 Project Structure

```
flapper-arcade/
├── main.py              # Main game (all rendering, physics, UI)
├── generate_sounds.py   # Procedural sound synthesizer
├── assets/
│   └── sounds/          # Generated WAV files (created by generate_sounds.py)
├── .gitignore
└── README.md
```

---

## 🎨 Screenshots

*Start the game to see the beautiful visuals across all 4 modes!*

---

## 🛠️ Technical Highlights

- **Zero external assets** — Everything is drawn with Pygame primitives and math
- **Resizable window** with letterbox scaling (maintains aspect ratio)
- **Procedural sound synthesis** — Jump chirps, coin chimes, ambient loops, all from sine waves
- **3-layer parallax** backgrounds with mountains, trees, and cabins
- **Dynamic weather** — Rain particles with ground splash effects, lightning flashes
- **Smooth day-night cycle** — 4-minute full cycle with sun/moon orbit, sky gradient blending

---

## 📜 License

This project is open source under the [MIT License](LICENSE).

---

Made with ❤️ and Python 🐍
