# Contributing to CityBoy Booster

First off, thanks for taking the time to contribute! This project is completely open-source, and any help to make it better for the community is appreciated.

## Getting Started

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally: `git clone https://github.com/YOUR-USERNAME/CityBoyBooster.git`
3. Make sure you have the dependencies installed: `pip install customtkinter psutil`

## What Can I Add?

- **New Game Support**: If you know safe, non-bannable system tweaks or cache directories for games like Apex Legends, COD, or Overwatch, feel free to add a new tab! Just follow the `CTkFrame` patterns in `main.py`.
- **UI Enhancements**: Anything that improves the brutalist/hacker aesthetic of the `customtkinter` interface.
- **Under-the-hood Optimizations**: Any new `.bat`, Python, or system administration tweaks must be legal, non-intrusive, and revertible.
- **Android Support (`main2.py`)**: You can add new non-root features to the Android version via `main2.py`. Make sure any terminal UI enhancements use the `rich` library.

## Ground Rules (CRITICAL)

Because this tool is used by gamers, we have zero tolerance for anything that puts accounts at risk.

1. **NO Memory Injection**: Do not add hooks using PyMem or direct memory editing that would trigger Anti-Cheats (Vanguard, Hyperion, EAC, BattlEye).
2. **NO Permanent Network Changes**: Do not add persistent network route changes. Temporary DNS flushes or process routing is fine.
3. **NO Roblox Network Flags**: We only support Rendering and Physics `FFlags` in `ClientAppSettings.json`. Adding flags that modify `MTU` or network protocols usually results in bans or kicks. Do not add them.
4. **Clean Exit**: Any system change you trigger must be reverted in `_on_close()` inside `main.py` so the user's PC is left clean afterward.
5. **No Android Root required**: All `main2.py` code should be strictly no-root or gracefully fallback if root is not present. Do not depend on Magisk modules or `su`.

## How to Submit Changes

1. Create a new branch: `git checkout -b feature-name`
2. Commit your changes: `git commit -m "Add new feature"`
3. Push to your branch: `git push origin feature-name`
4. Open a **Pull Request** on the original repo!

Thanks for helping us build the coolest open-source booster out there.
