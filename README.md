# CityBoy Universal Booster

> Free, open-source Windows performance optimizer for gamers. No bloat, no BS, no fake tricks.

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey?style=flat-square)
![Version](https://img.shields.io/badge/Version-v1.2-00FFCC?style=flat-square)

CityBoy is a single-file Python application that applies real, measurable Windows-level optimizations to improve game performance. It works universally across any game and includes dedicated presets for Roblox, Minecraft, and Fortnite. Everything it touches gets **automatically reverted** when you close the app — nothing is left behind on your system.

---

## Features at a Glance

| Feature | What It Actually Does | Real Effect? |
|---|---|---|
| **RAM Flush** | Calls `EmptyWorkingSet()` via Windows kernel API across every running process | ✅ Yes — watch the RAM bar drop live |
| **Ultimate Power Plan** | Unlocks Microsoft's hidden high-performance power scheme via `powercfg` — disables CPU throttling entirely | ✅ Yes — built into Windows, just hidden |
| **Sleeper Mode** | Lowers CPU scheduling priority of background apps (Discord, Chrome, Spotify) to `BelowNormal` | ✅ Yes — standard OS scheduling |
| **Process Priority Boost** | Sets your game to `High` CPU priority via PowerShell — more time slices from the scheduler | ✅ Yes — identical to what Task Manager does |
| **DNS Optimization** | Switches your network adapter to Cloudflare DNS (`1.1.1.1 / 1.0.0.1`) — faster server lookups | ✅ Yes — measurable with `ping` |
| **Registry Tweaks** | Disables GameDVR background recording, raises MMCSS gaming thread priority, removes network throttling | ✅ Yes — Microsoft-documented keys |
| **Roblox FFlags** | Writes rendering + physics flags to `ClientAppSettings.json`. Zero network flags (those cause kicks) | ✅ Yes — official Roblox client config |
| **VFX Kill Mode** | Disables Roblox particle systems, removes grass rendering, forces MSAA to 0 | ✅ Yes — GPU-load reduction on weak hardware |
| **Cache Cleanup** | Deletes accumulated logs and crash dumps for Minecraft and Fortnite | ✅ Yes — reduces game loading stutter |

---

## Getting Started

### Quick Start (Recommended)

1. Download or clone this repository
2. Double-click **`Run_CityBoy.bat`**
3. Accept the UAC admin prompt (required for priority/registry features)
4. Navigate to your game tab and apply the optimizations you want

The batch file automatically installs Python dependencies on first run.

### Manual Setup

```bash
pip install customtkinter psutil
python main.py
```

> **Note:** Administrator privileges are required for process priority, power plan, and registry features.

---

## Safety

This tool is designed to be fully reversible and transparent.

- **No drivers installed.** All operations use built-in Windows APIs (`powercfg`, `winreg`, `psutil`, `ctypes`).
- **No permanent system changes.** Every setting that gets modified is saved and restored on exit.
- **Auto-cleanup on close.** Hitting the X button triggers a cleanup routine:
  - Roblox `ClientAppSettings.json` is deleted
  - Your original Windows power plan GUID is re-activated
- **No Roblox network flags.** Network FFlags like MTU / RakNet modifiers cause Hyperion auto-kicks. We never write those.
- **No memory injection.** No DLL hooks, no process memory reads or writes, no anti-cheat interference.
- **Fully open source.** The entire app is one readable Python file — you can audit every line before running it.

---

## Supported Games

| Game | Available Optimizations |
|---|---|
| **Any Game** | RAM flush, power plan, sleeper mode, process priority, DNS, registry tweaks |
| **Roblox** | FPS presets (120 / 190 / MAX / No-VFX), auto-revert on close |
| **Minecraft (Java)** | `javaw.exe` priority boost, log folder cleanup, browser RAM reclaim |
| **Fortnite** | Process priority, log + crash dump cleanup |

Want another game added? Open an issue or PR — contributions are welcome.

---

## Roblox FFlags Reference

All Roblox presets write to:
```
%LOCALAPPDATA%\Roblox\Versions\<version>\ClientSettings\ClientAppSettings.json
```

| Preset | Key Flags Applied |
|---|---|
| **120 FPS** | `DFIntTaskSchedulerTargetFps: 120`, VSync off, physics optimization |
| **190 FPS** | `DFIntTaskSchedulerTargetFps: 190`, VSync off, physics optimization |
| **MAX Performance** | Unlocked FPS, VSync off, PostFX off, DPI scale off, shadows off, light update tuning |
| **No VFX** | All MAX flags + particle systems disabled, grass removed, MSAA forced to 0 |

> All presets are automatically removed from disk when you close the app.

---

## Requirements

- **OS:** Windows 10 or Windows 11
- **Python:** 3.8 or higher
- **Privileges:** Administrator (UAC prompt on launch)

**Dependencies** (auto-installed by `Run_CityBoy.bat`):
```
customtkinter
psutil
```

---

## FAQ

**Q: Will this get me banned in Roblox?**
A: No. We only write rendering FFlags to `ClientAppSettings.json`, which is the official supported Roblox configuration method. No memory injection, no DLL hooks, no network modification. Hyperion does not flag this.

**Q: Will this get me banned in Fortnite or Valorant?**
A: No. The app only changes Windows process scheduling priority (the same thing Task Manager lets you do) and deletes log files. It never touches game memory or files.

**Q: My screen went black after applying tweaks!**
A: This should not happen in v1.2. All FSE (Fullscreen Exclusive) registry tweaks were removed in v1.0 due to black-screen reports on specific GPU drivers. If you still experience this, open an issue and include your GPU model and Windows version.

**Q: Does the RAM flush actually do anything?**
A: Yes. `EmptyWorkingSet()` is a real Windows kernel API (`psapi.dll`). It forces processes to release physical RAM they've allocated but aren't actively using back to the OS free pool. Watch the live RAM bar in the sidebar — you will see it drop.

**Q: What happens when I close the app?**
A: The `WM_DELETE_WINDOW` event triggers a cleanup routine before the window is destroyed. Roblox flags are deleted from disk and your original power plan GUID is restored via `powercfg /setactive`. Your system is left exactly as it was before.

**Q: Why does it need admin rights?**
A: Three features require elevation: changing process CPU priority, writing to HKEY_LOCAL_MACHINE registry keys (MMCSS / network throttling), and running `powercfg`. Without admin, those three features silently fail. Everything else runs fine without it.

---

## Changelog

### v1.2 — 2026-04-24
- **Added:** "No VFX" Roblox FFlag preset — disables particle systems (`FFlagDebugGraphicsDisableParticleSystems`), removes all grass (`FIntFRMMinGrassDistance / Max`), and forces MSAA to 0 (`FIntDebugForceMSAASamples`). Targeted at low-end hardware and competitive play.
- **Improved:** Module docstring rewritten with per-feature explanations to make the codebase easier to navigate for contributors.
- **Changed:** Version bumped to v1.2 in title bar, sidebar label, and module header.

### v1.1 — 2026-04-23
- **Added:** Sleeper Mode — lowers background app CPU priority to free up scheduling headroom for games.
- **Added:** Custom process priority input — target any `.exe` by name from the Universal tab.
- **Fixed:** Crash on startup when `psapi.dll` was unavailable on some Windows 10 builds.
- **Fixed:** Power plan GUID not saved correctly when `powercfg /getactivescheme` output format varied by locale.
- **Changed:** Removed all Fullscreen Exclusive (FSE) registry tweaks that caused black screens on AMD + Intel iGPU setups.

### v1.0 — 2026-04-19
- Initial public release.
- Universal page: RAM flush, Ultimate Power Plan, DNS switch, GameDVR registry tweaks.
- Roblox page: 120 / 190 / MAX FPS presets with auto-revert on exit.
- Minecraft page: `javaw.exe` priority boost, log cleanup, browser kill.
- Fortnite page: process priority, log + crash dump cleanup.
- Live CPU / RAM hardware monitor in sidebar (1-second refresh).
- Full cleanup on exit (power plan restore, FFlag removal).

---

## Contributing

This project is MIT licensed — fork it, modify it, ship it. PRs are welcome.

**To add a new game tab:**
1. Add a new `CTkScrollableFrame` in `__init__` and include it in `frames_list`
2. Add a nav button entry to `nav_items`
3. Implement a `_build_<game>_page()` method following the existing pattern
4. Keep it safe — no memory injection, no anti-cheat bypass, no permanent system changes

---

## License

[MIT License](LICENSE) — free to use, modify, and distribute for any purpose.
