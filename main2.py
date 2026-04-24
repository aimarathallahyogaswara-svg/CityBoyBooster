"""
CityBoy Universal Booster v1.3 — Android (Termux) Edition
A lightweight, terminal-based optimizer for Android devices. No root required.
"""

import os
import sys
import subprocess
import shutil
import time
import psutil
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

console = Console()

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def get_android_info():
    info = {
        "device": "Unknown",
        "version": "Unknown",
        "cpu": "Unknown",
        "gpu": "Unknown"
    }
    try:
        info["device"] = subprocess.getoutput("getprop ro.product.model")
        info["version"] = subprocess.getoutput("getprop ro.build.version.release")
        info["cpu"] = subprocess.getoutput("getprop ro.board.platform")
        
        gpu_info = subprocess.getoutput("dumpsys SurfaceFlinger | grep -i 'GLES'")
        if gpu_info and "not found" not in gpu_info.lower() and "permission denied" not in gpu_info.lower():
            info["gpu"] = gpu_info.split('\n')[0].strip()
        else:
            info["gpu"] = "Detecting via dumpsys failed (Root may be required)"
            
    except Exception:
        pass
    return info

def show_header():
    clear_screen()
    console.print(Panel("[bold cyan]CITYBOY HUB v1.3[/bold cyan]\n[dim]Universal Android Booster (No Root)[/dim]", border_style="cyan", expand=False))
    
def menu_system_info():
    show_header()
    with console.status("[bold green]Gathering system info...[/bold green]"):
        info = get_android_info()
        try:
            ram = psutil.virtual_memory()
            ram_str = f"{ram.percent}% ({ram.used // 1048576}MB / {ram.total // 1048576}MB)"
        except:
            ram_str = "Unavailable"
        
    table = Table(show_header=False, box=None)
    table.add_column("Property", style="cyan", width=15)
    table.add_column("Value", style="white")
    
    table.add_row("Device:", info["device"])
    table.add_row("Android:", info["version"])
    table.add_row("Chipset:", info["cpu"])
    table.add_row("GPU (GLES):", info["gpu"])
    table.add_row("RAM Usage:", ram_str)
    
    console.print(Panel(table, title="[bold]Hardware Diagnostics[/bold]", border_style="blue", expand=False))
    Prompt.ask("\n[dim]Press Enter to return to menu...[/dim]")

def menu_ram_flush():
    show_header()
    console.print("[yellow]Flushing background cached apps...[/yellow]")
    
    try:
        res = subprocess.getoutput("am kill-all")
        if "Error" in res or "not found" in res.lower() or "permission denied" in res.lower():
            console.print("[red]Failed to flush RAM via am kill-all. (May require root or specific permissions)[/red]")
        else:
            console.print("[green]Background caches cleared successfully![/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        
    time.sleep(2)

def menu_cache_cleaner():
    show_header()
    console.print("[yellow]Cleaning generic game caches...[/yellow]")
    
    sdcard = os.environ.get("EXTERNAL_STORAGE", "/sdcard")
    cleaned = 0
    
    targets = [
        os.path.join(sdcard, "Download", ".thumbnails"),
        os.path.join(sdcard, "DCIM", ".thumbnails"),
        os.path.join(sdcard, "Android", "data", "com.roblox.client", "cache"),
        os.path.join(sdcard, "Android", "data", "com.mojang.minecraftpe", "cache"),
        os.path.join(sdcard, "Android", "data", "com.epicgames.portal", "cache"),
    ]
    
    for t in targets:
        if os.path.exists(t):
            try:
                shutil.rmtree(t, ignore_errors=True)
                cleaned += 1
                console.print(f"[dim]Cleaned: {t}[/dim]")
            except Exception:
                pass
                
    if cleaned == 0:
        console.print("[cyan]No accessible cache found. (Note: Android 11+ limits access to Android/data without root)[/cyan]")
    else:
        console.print(f"[green]Cleaned {cleaned} cache directories![/green]")
        
    Prompt.ask("\n[dim]Press Enter to return to menu...[/dim]")

def menu_wakelock():
    show_header()
    console.print("[yellow]Toggling Termux Wake Lock...[/yellow]")
    console.print("This prevents the CPU/Wi-Fi from sleeping when the screen is off or in the background.")
    
    try:
        subprocess.run(["termux-wake-lock"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        console.print("[green]Wake Lock ENABLED![/green]")
        console.print("Run 'termux-wake-unlock' later if you want to disable it.")
    except Exception:
        console.print("[red]Failed. Ensure you have installed termux-api (pkg install termux-api).[/red]")
        
    time.sleep(3)

def main_menu():
    while True:
        show_header()
        
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="cyan", justify="right")
        table.add_column("Action", style="white")
        
        table.add_row("[1]", "System & GPU Diagnostics")
        table.add_row("[2]", "RAM Flush (Kill Background Apps)")
        table.add_row("[3]", "Cache Cleaner")
        table.add_row("[4]", "Enable Gaming Wake Lock")
        table.add_row("[5]", "Exit")
        
        console.print(table)
        
        choice = Prompt.ask("\n[bold cyan]Select an option[/bold cyan]", choices=["1", "2", "3", "4", "5"])
        
        if choice == "1":
            menu_system_info()
        elif choice == "2":
            menu_ram_flush()
        elif choice == "3":
            menu_cache_cleaner()
        elif choice == "4":
            menu_wakelock()
        elif choice == "5":
            clear_screen()
            console.print("[cyan]Exiting CityBoy Hub. Stay frosty.[/cyan]")
            break

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        clear_screen()
        console.print("\n[cyan]Force exited. See ya.[/cyan]")
        sys.exit(0)
