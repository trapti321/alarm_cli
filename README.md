# 🔔 Alarm CLI

A lightweight, zero-dependency, natural-language Python CLI alarm clock. Set alarms naturally, manage upcoming timers, and receive audio alerts + terminal banners when time is up.

---

## ✨ Features

- 🗣️ **Natural Language Parsing**: Understands human-friendly time and duration inputs.
  - **Specific Time**: `set alarm for 5pm`, `set alarm for 5:44pm`, `set alarm for 20:30`
  - **Named Alarms**: `set alarm for dinner at 8pm`, `set alarm for meeting at 14:00`
  - **Relative Duration**: `set alarm for 20s`, `set alarm for 30m`, `set alarm for 2h`, `set alarm for 1h 30m`
  - **Shorthand Format**: `tea in 5m`, `workout in 45m`, `dinner at 8pm`
  - **Timer & Live Countdown**: `timer 30s`, `countdown 5m`, `set alarm for 10s --countdown`
- ⏳ **Live Real-time Countdown**:
  - Live ticking countdown clocks in terminal (`HH:MM:SS` format).
  - Multi-alarm visual monitor.
- 📋 **Alarm Management**: List pending alarms, check remaining countdowns, cancel by ID or name, and clear all.
- 🔔 **Audio & Visual Alerts**:
  - Standout ANSI visual notification banners in terminal.
  - Native sound playback across macOS (`afplay`), Linux (`paplay`/`aplay`), and Windows (`winsound`/bell).
  - Native desktop system notifications (`osascript` on macOS, `notify-send` on Linux, PowerShell on Windows).
- 🔄 **Execution Modes**:
  - **Interactive REPL Shell**: Live interactive shell with background scheduler thread that rings alarms while you work.
  - **Live Countdown Mode**: Real-time ticker clock that counts down to zero.
  - **Single CLI Command Mode**: Quick one-liner execution from bash/zsh scripts or terminal.
- ⚡ **Zero External Dependencies**: Pure Python 3 standard library.

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.7+ installed.

### 2. Running Directly

Run the interactive shell:
```bash
python3 run_alarm.py
```

Show live countdown of active alarms:
```bash
python3 run_alarm.py countdown
```

Or set an alarm directly with live countdown:
```bash
python3 run_alarm.py "timer 20s"
# or
python3 run_alarm.py "set alarm for 30s --countdown"
```

Or set an alarm directly in one command:
```bash
python3 run_alarm.py "set alarm for 20s"
python3 run_alarm.py "set alarm for dinner at 8pm"
python3 run_alarm.py list
```

### 3. Optional: Install as a System Command
```bash
pip install -e .
```
Then run simply:
```bash
alarm
alarm countdown
```

---

## 📖 Command Reference & Examples

### 1. Setting Alarms & Timers

| Command | Description |
| :--- | :--- |
| `set alarm for 5pm` | Sets alarm for 5:00 PM (today or tomorrow) |
| `set alarm for 5:44pm` | Sets alarm for exact 12-hour minute |
| `set alarm for 20:30` | Sets alarm using 24-hour military format |
| `set alarm for dinner at 8pm` | Named alarm label (`dinner`) at 8:00 PM |
| `set alarm for meeting at 14:00` | Named alarm label (`meeting`) at 14:00 |
| `set alarm for 20s` | Relative alarm in 20 seconds |
| `set alarm for 30m` | Relative alarm in 30 minutes |
| `set alarm for 2h` | Relative alarm in 2 hours |
| `set alarm for 1h 30m` | Combined relative duration (1 hour 30 mins) |
| `tea in 5m` | Shorthand named timer for "tea" in 5 mins |
| `timer 30s` / `countdown 1m` | Set timer and view live ticking countdown |
| `set alarm for 15s --countdown` | Set alarm and immediately start live countdown |

---

### 2. Managing Alarms & Live Countdown

| Command | Description |
| :--- | :--- |
| `countdown` or `show countdown` | Display real-time live ticking countdown clock for all active alarms |
| `list` or `ls` | Show all active alarms, target times, and remaining countdowns |
| `cancel 1` | Cancel pending alarm with ID `#1` |
| `cancel dinner` | Cancel pending alarm matching name `"dinner"` |
| `clear` | Cancel all active alarms |
| `help` | Show command help |
| `exit` or `quit` | Exit the interactive shell |


---

## 🖥️ Usage Modes

### Interactive Mode (Default)
Start the live interactive REPL:
```bash
python3 run_alarm.py
```
```text
╔═══════════════════════════════════════════╗
║         🔔  ALARM CLI CLOCK  🔔           ║
╚═══════════════════════════════════════════╝
Type a command (e.g. 'set alarm for 10s' or 'dinner at 8pm').
Type 'help' for options or 'exit' to quit.

alarm> set alarm for 20s

✔ Alarm #1 set for 'Alarm'!
  ⏰ Time: 08:15:30 PM (2026-09-13)
  ⏳ Remaining: 20s

alarm> list

=== ACTIVE ALARMS ===
  ID  | Label                | Target Time            | Remaining    | Status
  ---------------------------------------------------------------------------
  #1  | Alarm                | 2026-09-13 08:15:30 PM | 14s          | PENDING

alarm> 
==========================================================
 🔔 ⏰  ALARM TRIGGERED: ALARM
 Time: 08:15:30 PM
==========================================================
```

### Background Watcher / Daemon Mode
Run a dedicated monitor process in a separate terminal or tmux pane:
```bash
python3 run_alarm.py watch
```

---

## 🧪 Running Tests

Run the test suite:
```bash
python3 -m unittest discover -s tests -v
```

---

## 📁 Project Structure

```text
alarm_cli/
├── README.md               # Documentation and guides
├── requirements.txt        # Dependencies
├── setup.py                # Package setup script
├── run_alarm.py            # Executable launcher
├── alarm_cli/
│   ├── __init__.py         # Package entry
│   ├── parser.py           # Natural language parser
│   ├── manager.py          # State persistence and timer manager
│   ├── notifier.py         # Audio, banners, and system notifications
│   ├── cli.py              # CLI and interactive REPL loop
│   └── main.py             # Module entry point
└── tests/
    ├── __init__.py
    └── test_alarm.py       # Unit test suite
```

---

## 📦 Git Repository Setup

To push to GitHub:
```bash
git remote add origin https://github.com/trapti321/alarm_cli.git
git branch -M main
git push -u origin main
```
