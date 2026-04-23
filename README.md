# CityBoy Universal Booster

A free, open-source Windows game performance optimizer. Works with **Roblox, Minecraft, Fortnite, CS2, Valorant** — basically any game.

No placebo tweaks. Every optimization uses real Windows kernel APIs and system calls.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

---

## What Does It Actually Do?

| Feature | How It Works | Placebo? |
|---|---|---|
| **Free System RAM** | Calls `EmptyWorkingSet()` via Windows kernel API on every process. Forces idle RAM back to the OS. | ❌ Real — you can watch your RAM % drop live |
| **Ultimate Power Plan** | Unlocks Microsoft's hidden high-performance power scheme using `powercfg`. Disables CPU throttling. | ❌ Real — built into Windows, just hidden |
| **Process Priority** | Uses PowerShell to set your game's CPU scheduling priority to High. OS gives it more CPU time. | ❌ Real — standard Windows task management |
| **DNS Optimization** | Switches your network adapter to Cloudflare DNS (1.1.1.1). Faster DNS = faster server connections. | ❌ Real — measurable with `ping` |
| **GameDVR Disable** | Turns off Windows background game recording that eats CPU/GPU in the background. | ❌ Real — Microsoft recommends this for gaming |
| **Roblox FFlags** | Writes rendering-only flags to ClientSettings. No network flags (those cause kicks). | ❌ Real — official Roblox client config |
| **Cache Cleanup** | Deletes old logs and crash dumps that pile up and slow down game loading. | ❌ Real — just deleting junk files |

---

## How to Use

### Quick Start (Recommended)

1. Download or clone this repo
2. Double-click **`Run_CityBoy.bat`**
3. Click "Yes" on the admin prompt (needed for priority changes)
4. Pick your game tab and click the buttons you want

That's it. The batch file handles installing Python dependencies automatically.

### Manual Setup

If you prefer to run it yourself:

```bash
pip install customtkinter psutil
python main.py
```

> **Note:** You need to run as Administrator for process priority and registry features to work.

---

## Is It Safe?

**Yes.** Here's why:

- **No drivers installed.** Everything uses built-in Windows APIs.
- **No system files modified permanently.** Registry tweaks are standard Microsoft-documented settings.
- **Auto-cleanup on exit.** When you close the app:
  - Any Roblox FFlags you applied get deleted automatically
  - Your original Windows power plan gets restored
  - Nothing is left behind on your system
- **No network flags for Roblox.** We only touch rendering and physics flags. Network flags (MTU, RakNet) cause auto-kicks from Hyperion, so we never use them.
- **Open source.** Read the code yourself — it's one file, under 400 lines.

---

## Supported Games

| Game | What's Available |
|---|---|
| **Any Game** | Process priority boost, RAM flush, power plan, DNS, registry tweaks |
| **Roblox** | FPS cap presets (120 / 190 / MAX), auto-revert on close |
| **Minecraft** | JVM priority boost, log cleanup, browser RAM reclaim |
| **Fortnite** | Process priority, log + crash dump cleanup |

Want another game added? Open an issue or PR.

---

## Screenshots

The app has a dark brutalist sidebar UI with a live CPU/RAM hardware monitor that updates every second.

---

## Requirements

- **Windows 10 or 11**
- **Python 3.8+**
- **Administrator privileges** (for priority and registry access)

Dependencies (auto-installed by the batch file):
```
customtkinter
psutil
```

---

## FAQ

**Q: Will this get me banned in Roblox?**
A: No. We only write rendering FFlags to `ClientAppSettings.json`, which is the official Roblox configuration method. No memory injection, no DLL hooks, no network modification. Hyperion doesn't flag this.

**Q: Will this get me banned in Fortnite?**
A: No. We only change the Windows process priority (like Task Manager does) and delete log files. We don't touch the game's memory or files at all.

**Q: My PC went to a black screen!**
A: This shouldn't happen with the current version. We removed all aggressive FSE (Fullscreen Exclusive) registry tweaks that caused this on some laptops. If it still happens, please open an issue with your GPU model.

**Q: Does the RAM flush actually do anything?**
A: Yes — `EmptyWorkingSet()` is a real Windows kernel API. It forces processes to release RAM they've allocated but aren't actively using. Watch the live RAM bar in the sidebar — you'll see it drop after clicking the button.

**Q: What happens when I close the app?**
A: Everything gets cleaned up automatically. Roblox flags are deleted, your power plan is restored to what it was before. Your system is left exactly how it was.

---

## Contributing

This is MIT licensed — fork it, modify it, ship it. PRs welcome.

If you want to add support for another game:
1. Add a new tab in `_build_<game>_page()`
2. Add it to the sidebar navigation list
3. Keep it safe — no memory injection, no anti-cheat bypass stuff

---

## License

[MIT License](LICENSE) — do whatever you want with it.
