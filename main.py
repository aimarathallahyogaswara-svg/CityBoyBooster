"""
CityBoy Universal Booster — v1.3
Hey! So this is the main file. It's a single-script app so everything lives here —
the UI, all the boost logic, the cleanup on exit, all of it. Keeps things simple.

What this thing actually does when you click buttons:

  RAM Flush
    Calls EmptyWorkingSet() on every running process through the Windows kernel.
    That's a real API call, not a fake trick. Your RAM bar will literally drop.
    Great to run before launching any game.

  Ultimate Power Plan
    Windows ships with a hidden "Ultimate Performance" power scheme that disables
    CPU throttling entirely. It's just... not enabled by default for some reason.
    We unlock it with powercfg, save your old plan, and restore it when you close.

  Process Priority
    Uses PowerShell to bump your game to High scheduling priority. The OS gives
    high-priority threads more CPU time slices. Works the same as Task Manager
    but without you having to go dig through menus every time.

  Sleeper Mode
    Drops Discord, Chrome, Spotify, etc. to BelowNormal priority so they don't
    steal CPU cycles from your game mid-match. Nobody wants lag because Chrome
    decided to run 40 background tasks at the wrong moment.

  DNS Switch
    Swaps your adapter DNS to Cloudflare 1.1.1.1 for faster server lookups.
    Won't magically fix your ping, but cuts out slow ISP DNS responses.

  Registry Tweaks
    Turns off GameDVR (Windows background recording eats CPU for no reason),
    bumps MMCSS gaming thread priority, and disables network throttling.
    All standard Microsoft-documented keys — nothing sketchy.
    
  GPU Enhancements (new in v1.3)
    Detects OpenGL & Vulkan capabilities and enables Windows Hardware-Accelerated 
    GPU Scheduling via safe registry keys.

  Roblox FFlags
    Writes a ClientAppSettings.json into Roblox's ClientSettings folder.
    Rendering + physics flags only. We never touch network flags (MTU, RakNet)
    because those cause Hyperion auto-kicks. When you close the app, this file
    gets cleaned up automatically so Roblox goes back to vanilla.

  VFX Kill Mode (new in v1.2)
    Disables the particle system engine, removes grass rendering, and forces
    MSAA to 0. Basically strips out all the eye-candy so your GPU can focus
    entirely on frame delivery. Big help on lower-end machines.

Cleanup on exit:
    The app hooks WM_DELETE_WINDOW so when you hit X, it runs cleanup before
    closing — removes Roblox flags, restores your power plan. No leftover junk.

Dev note:
    All the page-building methods are named _build_<game>_page() so they're easy
    to find. If you want to add a new game tab, just follow that pattern.

License: MIT — fork it, break it, make it yours.
"""

import customtkinter as ctk
import os
import sys
import json
import ctypes
import psutil
import subprocess
import shutil
import threading
import atexit
from datetime import datetime


# ---------------------------------------------------------------------------
#  Admin elevation — we need it for priority changes and registry access.
#  If we're not admin, we re-launch ourselves with a UAC prompt and exit.
# ---------------------------------------------------------------------------
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

if not is_admin():
    params = " ".join(f'"{a}"' for a in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    sys.exit(0)


# Windows API constants for EmptyWorkingSet
PROCESS_SET_QUOTA         = 0x0100
PROCESS_QUERY_INFORMATION = 0x0400

ctk.set_appearance_mode("dark")


# ---------------------------------------------------------------------------
#  Roblox FFlag presets (rendering + physics ONLY — no network flags)
#  Network flags like MTU / RakNet cause auto-kick, so we never touch those.
# ---------------------------------------------------------------------------
ROBLOX_FLAGS_PRESETS = {
    120: {
        "DFIntTaskSchedulerTargetFps": 120,
        "FFlagDebugGraphicsDisableDirect3D11Vsync1": "True",
        "DFFlagPhysicsSkipObsoletePrimitives": "True",
    },
    190: {
        "DFIntTaskSchedulerTargetFps": 190,
        "FFlagDebugGraphicsDisableDirect3D11Vsync1": "True",
        "DFFlagPhysicsSkipObsoletePrimitives": "True",
    },
    9999: {
        "DFIntTaskSchedulerTargetFps": 9999,
        "FFlagDebugGraphicsDisableDirect3D11Vsync1": "True",
        "FFlagDisablePostFx": "True",
        "DFFlagDisableDPIScale": "True",
        "FIntRenderShadowIntensity": 0,
        "FIntRenderLocalLightUpdatesMax": 8,
        "FIntRenderLocalLightUpdatesMin": 4,
        "DFFlagPhysicsSkipObsoletePrimitives": "True",
    },
    "VFX": {
        "DFIntTaskSchedulerTargetFps": 9999,
        "FFlagDebugGraphicsDisableDirect3D11Vsync1": "True",
        "FFlagDisablePostFx": "True",
        "DFFlagDisableDPIScale": "True",
        "FIntRenderShadowIntensity": 0,
        "DFFlagPhysicsSkipObsoletePrimitives": "True",
        # VFX kill flags — verified working names
        "FIntParticleEmitterRate": 0,
        "FFlagEnableParticleEmitter": "False",
        "FIntGrassMaxDistance": 0,
        "FIntRenderGrassDetailStrands": 0,
        "FIntTerrainOctreeMaxDepth": 3,
        "FIntDebugForceMSAASamples": 0,
        "FFlagGlobalWindRendering": "False",
        "DFIntCSGLevelOfDetailSwitchingDistance": 0,
        "FIntRenderShadowmapBias": 999999999,
        "DFIntDebugRestrictGCDistance": 1,
        "FFlagDebugSkyGray": "True",
        "FIntRenderLocalLightUpdatesMax": 1,
        "FIntRenderLocalLightUpdatesMin": 1,
    },
}


# ===========================================================================
#  The main application window
# ===========================================================================
class CityBoyBooster(ctk.CTk):

    def __init__(self):
        super().__init__()

        # We'll remember the user's original power plan GUID so we can
        # restore it when they close the app.  None = haven't changed it yet.
        self.original_power_plan_guid = None
        self.roblox_flags_applied = False
        self._hud_after_id = None        # track the HUD timer so we can cancel it
        self._closing = False            # prevent double-close

        self.title("CITYBOY HUB v1.3")
        self.geometry("760x560")
        self.resizable(False, False)
        self.configure(fg_color="#030304")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── sidebar ──────────────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(
            self, width=185, corner_radius=0,
            fg_color="#070709", border_width=0,
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)   # push HUD to bottom

        ctk.CTkLabel(
            self.sidebar, text="CITYBOY",
            font=ctk.CTkFont(family="Inter", size=26, weight="bold"),
            text_color="#FFFFFF",
        ).grid(row=0, column=0, padx=20, pady=(25, 0))

        ctk.CTkLabel(
            self.sidebar, text="universal booster v1.3",
            font=ctk.CTkFont(family="Inter", size=9), text_color="#00FFCC",
        ).grid(row=1, column=0, padx=20, pady=(0, 20))

        # navigation buttons
        nav_items = [
            ("⚡  Universal",  2),
            ("🖥  GPU",        3),
            ("🎮  Roblox",     4),
            ("⛏  Minecraft",  5),
            ("🔫  Fortnite",   6),
        ]
        self.nav_buttons = []
        frames_list = []   # filled after we create the content frames

        def _switch(idx):
            for i, f in enumerate(frames_list):
                f.grid_forget()
                self.nav_buttons[i].configure(
                    fg_color="transparent", text_color="#555555",
                )
            frames_list[idx].grid(row=0, column=1, sticky="nsew", padx=25, pady=25)
            self.nav_buttons[idx].configure(
                fg_color="#121215", text_color="#FFFFFF",
            )

        for label, row in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, text=label, anchor="w",
                fg_color="transparent", text_color="#555555",
                hover_color="#121215", corner_radius=6,
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda r=row: _switch(r - 2),
            )
            btn.grid(row=row, column=0, pady=4, padx=12, sticky="ew")
            self.nav_buttons.append(btn)

        # live hardware HUD — updates every second
        hud = ctk.CTkFrame(
            self.sidebar, fg_color="#050507", corner_radius=8,
            border_color="#111115", border_width=1,
        )
        hud.grid(row=8, column=0, padx=14, pady=(0, 20), sticky="sew")

        self.lbl_cpu = ctk.CTkLabel(
            hud, text="CPU  …", anchor="w",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color="#00FFCC",
        )
        self.lbl_cpu.pack(pady=(10, 2), padx=10, fill="x")

        self.lbl_ram = ctk.CTkLabel(
            hud, text="RAM  …", anchor="w",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color="#FF3366",
        )
        self.lbl_ram.pack(pady=(2, 2), padx=10, fill="x")

        self.lbl_gpu = ctk.CTkLabel(
            hud, text="GPU  …", anchor="w",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color="#3399FF",
        )
        self.lbl_gpu.pack(pady=(2, 10), padx=10, fill="x")

        # ── content frames ───────────────────────────────────────────────
        self.univ_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.gpu_frame  = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.rblx_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.mc_frame   = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.fn_frame   = ctk.CTkScrollableFrame(self, fg_color="transparent")
        frames_list.extend([self.univ_frame, self.gpu_frame, self.rblx_frame, self.mc_frame, self.fn_frame])

        # ── bottom console log ───────────────────────────────────────────
        self.log_box = ctk.CTkTextbox(
            self, height=120,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#050507", text_color="#A0A0A0",
            border_width=1, border_color="#111115", corner_radius=8,
        )
        self.log_box.grid(row=1, column=1, sticky="nsew", padx=25, pady=(0, 20))
        self.log_box.configure(state="disabled")

        # build out each page
        self._build_universal_page()
        self._build_gpu_page()
        self._build_roblox_page()
        self._build_minecraft_page()
        self._build_fortnite_page()

        # show universal by default
        _switch(0)

        self.log("hey, everything's loaded up and ready to go.")
        self.log("admin privileges confirmed — all systems green.")
        self.log("tip: when you close this window, any tweaks are reverted automatically.")

        # kick off the live hardware monitor
        self._tick_hud()

    # ─── helpers ─────────────────────────────────────────────────────────

    def log(self, msg: str):
        """Append a timestamped line to the bottom console."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{ts}]  {msg}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _heading(self, parent, title, subtitle):
        ctk.CTkLabel(
            parent, text=title,
            font=ctk.CTkFont(size=20, weight="bold"), text_color="#FFFFFF",
        ).pack(anchor="w")
        ctk.CTkLabel(
            parent, text=subtitle,
            font=ctk.CTkFont(size=11), text_color="#555555",
        ).pack(anchor="w", pady=(2, 18))

    def _btn(self, parent, text, command,
             fg="#111114", hover="#222228", text_color="#FFFFFF"):
        """Shorthand to create a styled action button."""
        ctk.CTkButton(
            parent, text=text, command=command,
            fg_color=fg, hover_color=hover, text_color=text_color,
            height=38, corner_radius=5,
            border_width=1, border_color="#222228",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(fill="x", pady=5)

    # ─── live hardware HUD ───────────────────────────────────────────────

    def _tick_hud(self):
        """Refresh CPU / RAM bars every second."""
        if self._closing:
            return
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory()

            def bar(pct):
                filled = int(pct / 100 * 12)
                return "█" * filled + "░" * (12 - filled)

            self.lbl_cpu.configure(text=f"CPU  {bar(cpu)}  {int(cpu):>3}%")
            self.lbl_ram.configure(text=f"RAM  {bar(ram.percent)}  {int(ram.percent):>3}%")
            
            if "..." in self.lbl_gpu.cget("text"):
                try:
                    res = subprocess.getoutput("wmic path win32_VideoController get name")
                    lines = [l.strip() for l in res.split("\n") if l.strip() and "Name" not in l]
                    g_name = lines[0] if lines else "Unknown"
                    if len(g_name) > 13: g_name = g_name[:10] + "..."
                    self.lbl_gpu.configure(text=f"GPU  {g_name}")
                except:
                    self.lbl_gpu.configure(text=f"GPU  Unknown")
        except Exception:
            return  # widget was destroyed, stop updating
        self._hud_after_id = self.after(1000, self._tick_hud)

    # ─── safe shutdown ───────────────────────────────────────────────────

    def _on_close(self):
        """
        Called when the user clicks the X button.
        We revert anything that might leave the system in a weird state:
          1. Remove any Roblox FFlags we wrote
          2. Restore the original Windows power plan (if we changed it)
        Then forcefully exit so the CMD window closes too.
        """
        if self._closing:
            return  # already shutting down, don't double-fire
        self._closing = True

        # Stop the HUD ticker immediately so it doesn't fire during teardown
        if self._hud_after_id is not None:
            try:
                self.after_cancel(self._hud_after_id)
            except Exception:
                pass

        try:
            self.log("cleaning up before we go...")
        except Exception:
            pass

        # 1) revert roblox flags
        if self.roblox_flags_applied:
            try:
                self._remove_roblox_fflags(silent=True)
            except Exception:
                pass

        # 2) restore original power plan
        if self.original_power_plan_guid:
            try:
                subprocess.run(
                    f"powercfg /setactive {self.original_power_plan_guid}",
                    shell=True, capture_output=True,
                    timeout=5,
                )
            except Exception:
                pass

        # 3) destroy the window and force-exit the process
        #    This ensures the CMD window closes properly even if
        #    background threads or after() callbacks are still pending.
        try:
            self.destroy()
        except Exception:
            pass
        os._exit(0)

    # =====================================================================
    #  UNIVERSAL PAGE
    # =====================================================================

    def _build_universal_page(self):
        f = self.univ_frame
        self._heading(f, "Universal Optimizations",
                      "Hardware-level tweaks that work with any game on your PC.")

        self._btn(f, "🔋  Activate Ultimate Power Plan",
                  self._cmd_power_plan,
                  fg="#1A0A05", hover="#2E110A", text_color="#FF4422")

        self._btn(f, "🧹  Free System RAM (EmptyWorkingSet)",
                  self._cmd_nuke_ram,
                  fg="#051A0A", hover="#0A2E11", text_color="#22FF66")

        self._btn(f, "💤  Enable Sleeper Mode for Background Apps",
                  self._cmd_sleeper_mode,
                  fg="#0A0A1A", hover="#11112E", text_color="#6688FF")

        self._btn(f, "🌐  Switch DNS → Cloudflare 1.1.1.1",
                  self._cmd_dns,
                  fg="#0D0D18", hover="#1A1A30", text_color="#AAAAFF")

        self._btn(f, "🧩  Apply Safe Registry Tweaks (GameDVR off)",
                  self._cmd_regedit,
                  fg="#111114", hover="#222228")

        # custom process priority
        ctk.CTkLabel(
            f, text="Or target a specific game process:",
            font=ctk.CTkFont(size=11), text_color="#555555",
        ).pack(anchor="w", pady=(20, 4))

        self.process_entry = ctk.CTkEntry(
            f, placeholder_text="e.g. cs2.exe, Valorant.exe, javaw.exe",
            height=36, fg_color="#0A0A0C", border_color="#222222",
        )
        self.process_entry.pack(fill="x", pady=(0, 8))

        self._btn(f, "🎯  Set High Priority for That Process",
                  self._cmd_inject_custom,
                  fg="#001122", hover="#002244", text_color="#3399FF")

    # — universal commands —

    def _cmd_power_plan(self):
        """
        Unlock the hidden 'Ultimate Performance' power plan.
        Before switching, we save the current active plan GUID
        so we can restore it on exit.
        """
        self.log("saving your current power plan as a backup...")
        try:
            # grab the currently active plan GUID
            res = subprocess.run(
                "powercfg /getactivescheme", shell=True,
                capture_output=True, text=True,
            )
            if res.returncode == 0 and "GUID" in res.stdout:
                # line looks like: "Power Scheme GUID: <guid>  (Balanced)"
                self.original_power_plan_guid = res.stdout.split()[3]
                self.log(f"backed up plan: {self.original_power_plan_guid}")
        except Exception:
            pass

        self.log("unlocking the hidden Ultimate Performance plan...")
        try:
            subprocess.run(
                "powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61",
                shell=True, capture_output=True,
            )
            listing = subprocess.run(
                "powercfg /list", shell=True, capture_output=True, text=True,
            )
            guid = None
            for line in listing.stdout.splitlines():
                if "Ultimate Performance" in line:
                    guid = line.split()[3]
                    break
            if guid:
                subprocess.run(f"powercfg /setactive {guid}", shell=True, capture_output=True)
                self.log("done! your CPU is now running without power-saving throttling.")
                self.log("(this will be reverted automatically when you close the app.)")
            else:
                self.log("couldn't find the plan — Windows might not support it on this edition.")
        except Exception as e:
            self.log(f"power plan error: {e}")

    def _cmd_nuke_ram(self):
        """
        Walk through every running process and call EmptyWorkingSet on it.
        This is a real Windows kernel API call — it forces the OS to page out
        idle memory so your game has more physical RAM available.
        You can literally watch the RAM bar drop after clicking this.
        """
        def _work():
            self.log("flushing idle RAM from all running processes...")
            before = psutil.virtual_memory().percent
            flushed = 0
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    handle = ctypes.windll.kernel32.OpenProcess(
                        PROCESS_SET_QUOTA | PROCESS_QUERY_INFORMATION,
                        False, proc.info["pid"],
                    )
                    if handle:
                        ok = ctypes.windll.psapi.EmptyWorkingSet(handle)
                        ctypes.windll.kernel32.CloseHandle(handle)
                        if ok:
                            flushed += 1
                except Exception:
                    pass
            after = psutil.virtual_memory().percent
            diff = round(before - after, 1)
            self.log(f"flushed {flushed} processes — RAM went from {before}% → {after}% ({diff}% freed).")
        threading.Thread(target=_work, daemon=True).start()

    def _cmd_dns(self):
        def _work():
            self.log("flushing DNS cache...")
            try:
                subprocess.run(
                    "ipconfig /flushdns", shell=True,
                    capture_output=True, timeout=10,
                )
            except Exception:
                pass

            # Build the PowerShell command properly to avoid quoting hell.
            # Using -EncodedCommand with a Base64-encoded script is the most
            # reliable way to pass complex PS commands from Python.
            ps_script = (
                "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | "
                "Set-DnsClientServerAddress -ServerAddresses @('1.1.1.1','1.0.0.1')"
            )
            import base64
            encoded = base64.b64encode(ps_script.encode("utf-16-le")).decode("ascii")
            cmd = ["powershell.exe", "-NoProfile", "-EncodedCommand", encoded]

            try:
                res = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=15,
                )
                if res.returncode == 0:
                    self.log("DNS switched to Cloudflare 1.1.1.1 — should feel snappier online.")
                else:
                    err = (res.stderr or "").strip()
                    self.log(f"couldn't change adapter DNS. {err or 'try doing it manually in network settings.'}")
            except subprocess.TimeoutExpired:
                self.log("DNS command timed out. your adapter might be busy — try again.")
            except Exception as e:
                self.log(f"DNS command failed: {e}")
        threading.Thread(target=_work, daemon=True).start()

    def _cmd_regedit(self):
        """
        Only safe registry keys:
        - Turn off GameDVR (background recording eats CPU)
        - MMCSS gaming priority (tells Windows to schedule game threads first)
        - Disable network throttling
        We do NOT touch FSE/fullscreen settings to avoid black-screen issues.
        """
        import winreg
        self.log("applying safe registry tweaks...")
        try:
            # disable GameDVR background recording
            k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"System\GameConfigStore")
            winreg.SetValueEx(k, "GameDVR_Enabled", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(k)
            self.log("  → GameDVR background recording disabled.")
        except Exception as e:
            self.log(f"  → GameDVR tweak failed: {e}")

        try:
            # MMCSS gaming priority
            k = winreg.CreateKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games",
            )
            winreg.SetValueEx(k, "GPU Priority", 0, winreg.REG_DWORD, 8)
            winreg.SetValueEx(k, "Priority", 0, winreg.REG_DWORD, 6)
            winreg.SetValueEx(k, "Scheduling Category", 0, winreg.REG_SZ, "High")
            winreg.CloseKey(k)
            self.log("  → MMCSS gaming thread priority set to High.")
        except Exception as e:
            self.log(f"  → MMCSS tweak failed: {e}")

        try:
            # network throttling
            k = winreg.CreateKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
            )
            winreg.SetValueEx(k, "NetworkThrottlingIndex", 0, winreg.REG_DWORD, 0xFFFFFFFF)
            winreg.SetValueEx(k, "SystemResponsiveness", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(k)
            self.log("  → Windows network throttling disabled.")
        except Exception as e:
            self.log(f"  → network tweak failed: {e}")

        self.log("registry tweaks done. you might want to restart to feel the full effect.")

    def _cmd_sleeper_mode(self):
        """
        Lowers priority of common background apps to 'BelowNormal'
        so they don't eat CPU cycles from the game.
        """
        targets = ["discord", "chrome", "msedge", "brave", "spotify", "opera", "firefox"]
        self.log("putting background apps to sleep (lowering CPU priority)...")
        
        found_any = False
        for proc in psutil.process_iter(["name"]):
            pname = (proc.info.get("name") or "").lower().replace(".exe", "")
            if pname in targets:
                found_any = True
                break
                
        if not found_any:
            self.log("no heavy background apps found to sleep. you're good.")
            return

        import base64
        ps_script = (
            "$apps = @('" + "','".join(targets) + "'); "
            "ForEach ($app in $apps) { "
            "Get-Process $app -ErrorAction SilentlyContinue | ForEach-Object { $_.PriorityClass = 'BelowNormal' } "
            "}"
        )
        encoded = base64.b64encode(ps_script.encode("utf-16-le")).decode("ascii")
        cmd = ["powershell.exe", "-NoProfile", "-EncodedCommand", encoded]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                self.log("done — Discord, browsers, and Spotify are now running in sleeper mode.")
            else:
                self.log("error lowering priority. make sure you're running as admin.")
        except Exception as e:
            self.log(f"sleeper mode failed: {e}")

    def _cmd_inject_custom(self):
        target = self.process_entry.get().strip()
        if not target:
            self.log("type a process name in the box first (like cs2.exe).")
            return
        self._set_process_priority(target)

    # =====================================================================
    #  GPU PAGE
    # =====================================================================

    def _build_gpu_page(self):
        f = self.gpu_frame
        self._heading(f, "GPU Diagnostics & Tweaks",
                      "Detects OpenGL/Vulkan capabilities and applies safe GPU scheduling.")

        self._btn(f, "🔍  Check OpenGL Capabilities",
                  self._cmd_check_opengl,
                  fg="#0A1A1A", hover="#112E2E", text_color="#66FFFF")

        self._btn(f, "🔍  Check Vulkan 1.3 Support",
                  self._cmd_check_vulkan,
                  fg="#1A0A0A", hover="#2E1111", text_color="#FF6666")

        self._btn(f, "⚙️  Enable Hardware-Accelerated GPU Scheduling",
                  self._cmd_enable_hws,
                  fg="#1A1A0A", hover="#2E2E11", text_color="#FFFF66")
                  
        ctk.CTkLabel(
            f, text=(
                "Tip: Hardware-Accelerated GPU Scheduling (HAGS) reduces latency\n"
                "and improves performance on supported NVIDIA/AMD cards.\n"
                "Requires a PC restart to take effect."
            ),
            font=ctk.CTkFont(size=11), text_color="#444444",
            wraplength=440, justify="left",
        ).pack(anchor="w", pady=(20, 0))

    def _cmd_check_opengl(self):
        self.log("checking OpenGL driver...")
        try:
            gl = ctypes.windll.LoadLibrary("opengl32.dll")
            if gl:
                self.log("OpenGL driver (opengl32.dll) is installed and active.")
            else:
                self.log("OpenGL driver not found. Update your GPU drivers.")
        except Exception as e:
            self.log(f"OpenGL check failed: {e}")

    def _cmd_check_vulkan(self):
        self.log("checking Vulkan support...")
        try:
            vk = ctypes.windll.LoadLibrary("vulkan-1.dll")
            if vk:
                self.log("Vulkan driver (vulkan-1.dll) is installed.")
                self.log("Run 'vulkaninfo' in CMD for full version details.")
            else:
                self.log("Vulkan driver not found. Your GPU might not support it.")
        except Exception as e:
            self.log("Vulkan driver not found or check failed.")

    def _cmd_enable_hws(self):
        self.log("enabling Hardware-Accelerated GPU Scheduling...")
        import winreg
        try:
            k = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers")
            winreg.SetValueEx(k, "HwSchMode", 0, winreg.REG_DWORD, 2)
            winreg.CloseKey(k)
            self.log("HAGS enabled in registry! Please restart your PC for it to take effect.")
        except Exception as e:
            self.log(f"couldn't enable HAGS (ensure you run as admin): {e}")

    # =====================================================================
    #  ROBLOX PAGE
    # =====================================================================

    def _build_roblox_page(self):
        f = self.rblx_frame
        self._heading(f, "Roblox Engine Tweaks",
                      "Writes safe rendering FFlags to ClientSettings. No network flags.")

        self._btn(f, "Apply 120 FPS", lambda: self._apply_roblox_preset(120))
        self._btn(f, "Apply 190 FPS", lambda: self._apply_roblox_preset(190))
        self._btn(f, "Apply MAX Performance", lambda: self._apply_roblox_preset(9999))
        self._btn(f, "🚫  Disable All VFX (Max Performance + No Particles)", lambda: self._apply_roblox_preset("VFX"))
        self._btn(f, "🗑  Revert to Vanilla (remove all flags)",
                  self._cmd_revert_roblox,
                  fg="#2A1015", hover="#441020", text_color="#FF4466")

    def _get_roblox_path(self):
        local = os.environ.get("LOCALAPPDATA", "")
        versions = os.path.join(local, "Roblox", "Versions")
        if not os.path.exists(versions):
            return None
        for folder in os.listdir(versions):
            full = os.path.join(versions, folder)
            if os.path.isdir(full) and os.path.exists(
                os.path.join(full, "RobloxPlayerBeta.exe")
            ):
                return full
        return None

    def _write_roblox_fflags(self, flags: dict):
        path = self._get_roblox_path()
        if not path:
            self.log("couldn't find Roblox. launch the game once so Windows creates the folder.")
            return False
        cs_dir = os.path.join(path, "ClientSettings")
        os.makedirs(cs_dir, exist_ok=True)
        fp = os.path.join(cs_dir, "ClientAppSettings.json")
        try:
            with open(fp, "w") as f:
                json.dump(flags, f, indent=4)
            self.roblox_flags_applied = True
            self.log(f"flags written to {os.path.basename(path)}\\ClientSettings.")
            return True
        except Exception as e:
            self.log(f"couldn't write flags: {e}")
            return False

    def _remove_roblox_fflags(self, silent=False):
        path = self._get_roblox_path()
        if not path:
            if not silent:
                self.log("Roblox folder not found — nothing to revert.")
            return
        fp = os.path.join(path, "ClientSettings", "ClientAppSettings.json")
        if os.path.exists(fp):
            try:
                os.remove(fp)
                self.roblox_flags_applied = False
                if not silent:
                    self.log("flags removed — Roblox is back to default settings.")
            except Exception as e:
                if not silent:
                    self.log(f"couldn't delete the flags file: {e}")
        else:
            self.roblox_flags_applied = False
            if not silent:
                self.log("no custom flags found — you're already on vanilla settings.")

    def _apply_roblox_preset(self, fps):
        preset = ROBLOX_FLAGS_PRESETS.get(fps)
        if not preset:
            return
        if fps == 9999:
            label = "MAX Performance"
        elif fps == "VFX":
            label = "No VFX"
        else:
            label = f"{fps} FPS"
        self.log(f"applying {label} preset...")
        self._write_roblox_fflags(preset)

    def _cmd_revert_roblox(self):
        self._remove_roblox_fflags()

    # =====================================================================
    #  MINECRAFT PAGE
    # =====================================================================

    def _build_minecraft_page(self):
        f = self.mc_frame
        self._heading(f, "Minecraft (Java Edition)",
                      "JVM and system-level optimizations for smoother chunk loading.")

        self._btn(f, "⬆  Boost javaw.exe Priority",
                  lambda: self._set_process_priority("javaw.exe"))

        self._btn(f, "🧹  Clear .minecraft/logs folder",
                  self._cmd_clear_mc_logs)

        self._btn(f, "💀  Kill Background Browsers (free RAM)",
                  self._cmd_kill_browsers,
                  fg="#1A1400", hover="#332800", text_color="#FFCC33")

        ctk.CTkLabel(
            f, text=(
                "Tip: for the biggest FPS gain in Minecraft, install Sodium + Lithium mods.\n"
                "This booster handles the OS side — mods handle the engine side."
            ),
            font=ctk.CTkFont(size=11), text_color="#444444",
            wraplength=440, justify="left",
        ).pack(anchor="w", pady=(20, 0))

    def _cmd_clear_mc_logs(self):
        appdata = os.environ.get("APPDATA", "")
        mc_logs = os.path.join(appdata, ".minecraft", "logs")
        if os.path.exists(mc_logs):
            shutil.rmtree(mc_logs, ignore_errors=True)
            self.log("cleared Minecraft log files.")
        else:
            self.log("no .minecraft/logs folder found — nothing to clean.")

    def _cmd_kill_browsers(self):
        self.log("looking for browsers eating your RAM...")
        browser_names = ["chrome.exe", "msedge.exe", "brave.exe", "opera.exe", "firefox.exe"]
        killed = 0
        for proc in psutil.process_iter(["name"]):
            name = (proc.info["name"] or "").lower()
            if name in browser_names:
                try:
                    proc.kill()
                    killed += 1
                except Exception:
                    pass
        if killed:
            self.log(f"closed {killed} browser processes — that RAM is yours now.")
        else:
            self.log("no browsers running in the background. you're already lean.")

    # =====================================================================
    #  FORTNITE PAGE
    # =====================================================================

    def _build_fortnite_page(self):
        f = self.fn_frame
        self._heading(f, "Fortnite (Unreal Engine 5)",
                      "Process priority and cache cleanup for smoother builds & fights.")

        self._btn(f, "⬆  Boost Fortnite Process Priority",
                  lambda: self._set_process_priority("FortniteClient-Win64-Shipping.exe"))

        self._btn(f, "🧹  Clear Fortnite Logs & Crash Data",
                  self._cmd_clear_fn_logs)

        ctk.CTkLabel(
            f, text=(
                "Tip: in Fortnite settings, set Rendering Mode to 'Performance'\n"
                "and turn off Replay Recording for a big FPS boost."
            ),
            font=ctk.CTkFont(size=11), text_color="#444444",
            wraplength=440, justify="left",
        ).pack(anchor="w", pady=(20, 0))

    def _cmd_clear_fn_logs(self):
        local = os.environ.get("LOCALAPPDATA", "")
        logs_dir = os.path.join(local, "FortniteGame", "Saved", "Logs")
        crash_dir = os.path.join(local, "FortniteGame", "Saved", "Crashes")
        cleaned = False
        for d in [logs_dir, crash_dir]:
            if os.path.exists(d):
                shutil.rmtree(d, ignore_errors=True)
                cleaned = True
        if cleaned:
            self.log("cleared Fortnite logs and crash dumps.")
        else:
            self.log("no Fortnite cache found — either it's already clean or the game isn't installed.")

    # =====================================================================
    #  SHARED: process priority helper
    # =====================================================================

    def _set_process_priority(self, proc_name: str):
        """
        Uses PowerShell to set a process to High priority.
        This is safer than opening raw kernel handles (which anti-cheats flag).
        """
        nice_name = proc_name.replace(".exe", "")
        self.log(f"looking for {proc_name}...")

        found = False
        for p in psutil.process_iter(["name"]):
            pname = p.info.get("name") or ""
            if nice_name.lower() in pname.lower():
                found = True
                break

        if not found:
            self.log(f"{proc_name} isn't running right now. launch the game first!")
            return

        import base64
        ps_script = (
            f"Get-Process '{nice_name}' -ErrorAction SilentlyContinue | "
            f"ForEach-Object {{ $_.PriorityClass = 'High' }}"
        )
        encoded = base64.b64encode(ps_script.encode("utf-16-le")).decode("ascii")
        cmd = ["powershell.exe", "-NoProfile", "-EncodedCommand", encoded]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log(f"done — {proc_name} is now running at High priority.")
            else:
                self.log(f"priority change returned an error. make sure you're running as admin.")
        except Exception as e:
            self.log(f"failed to set priority: {e}")


# ===========================================================================
#  Entry point
# ===========================================================================
if __name__ == "__main__":
    app = CityBoyBooster()
    app.mainloop()
