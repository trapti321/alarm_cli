"""
Cross-platform sound and notification handler for Alarm CLI.
Plays audio alerts and desktop notifications on macOS, Linux, and Windows.
"""

import os
import sys
import subprocess
import threading
import time


# ANSI styling helpers
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"


def play_sound(beeps: int = 3):
    """
    Plays an alert sound using native platform tools or fallback terminal bell.
    """
    def _play():
        platform = sys.platform
        played = False

        if platform == "darwin":  # macOS
            sounds = [
                "/System/Library/Sounds/Glass.aiff",
                "/System/Library/Sounds/Hero.aiff",
                "/System/Library/Sounds/Ping.aiff"
            ]
            for s in sounds:
                if os.path.exists(s):
                    try:
                        for _ in range(beeps):
                            subprocess.run(["afplay", s], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            time.sleep(0.1)
                        played = True
                        break
                    except Exception:
                        pass

        elif platform.startswith("linux"):
            # Try paplay, aplay, or canberra-gtk-play
            for tool, sound_path in [
                ("paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"),
                ("aplay", "/usr/share/sounds/alsa/Front_Center.wav"),
                ("canberra-gtk-play", "--id=complete")
            ]:
                try:
                    if tool == "canberra-gtk-play":
                        subprocess.run([tool, sound_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        if os.path.exists(sound_path):
                            subprocess.run([tool, sound_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    played = True
                    break
                except Exception:
                    continue

        elif platform == "win32":
            try:
                import winsound
                for _ in range(beeps):
                    winsound.Beep(1000, 400)
                    time.sleep(0.1)
                played = True
            except Exception:
                pass

        if not played:
            # Fallback to system bell
            for _ in range(beeps):
                sys.stdout.write("\a")
                sys.stdout.flush()
                time.sleep(0.3)

    t = threading.Thread(target=_play, daemon=True)
    t.start()


def send_system_notification(title: str, message: str):
    """
    Sends native system notification popup if supported.
    """
    platform = sys.platform
    try:
        if platform == "darwin":
            script = f'display notification "{message}" with title "{title}" sound name "Glass"'
            subprocess.run(["osascript", "-e", script], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif platform.startswith("linux"):
            subprocess.run(["notify-send", title, message], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif platform == "win32":
            ps_script = f"""
            [reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null
            $notify = new-object system.windows.forms.notifyicon
            $notify.icon = [system.drawing.systemicons]::Information
            $notify.visible = $true
            $notify.showballoontip(10, '{title}', '{message}', [system.windows.forms.tooltipicon]::Info)
            """
            subprocess.run(["powershell", "-Command", ps_script], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def render_alarm_banner(label: str, target_time_str: str):
    """
    Renders a standout ASCII / ANSI notification banner in the terminal.
    """
    border = "=" * 58
    banner = f"""
{RED}{BOLD}{border}
 🔔 ⏰  ALARM TRIGGERED: {label.upper()}
 Time: {target_time_str}
{border}{RESET}
"""
    print(banner)
