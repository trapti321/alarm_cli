"""
CLI Interface and Interactive REPL for Alarm CLI.
"""

import sys
import time
import threading
from datetime import datetime
from typing import Optional

from alarm_cli.parser import parse_command
from alarm_cli.manager import AlarmManager
from alarm_cli.notifier import (
    play_sound,
    send_system_notification,
    render_alarm_banner,
    BOLD, GREEN, YELLOW, RED, CYAN, MAGENTA, RESET
)


def format_alarm_row(alarm: dict) -> str:
    target = datetime.fromisoformat(alarm["target_time"])
    time_str = target.strftime("%Y-%m-%d %I:%M:%S %p")
    countdown = AlarmManager.format_countdown(alarm["target_time"])
    status_col = f"{YELLOW}PENDING{RESET}" if alarm["status"] == "pending" else f"{GREEN}TRIGGERED{RESET}" if alarm["status"] == "triggered" else f"{RED}CANCELLED{RESET}"
    return f"  #{alarm['id']:<3} | {alarm['label']:<20} | {time_str:<22} | {countdown:<12} | {status_col}"


def print_alarms_table(alarms, title="ACTIVE ALARMS"):
    print(f"\n{CYAN}{BOLD}=== {title} ==={RESET}")
    if not alarms:
        print(f"  {YELLOW}No active alarms found.{RESET}\n")
        return

    header = f"  {'ID':<3} | {'Label':<20} | {'Target Time':<22} | {'Remaining':<12} | Status"
    print(f"{BOLD}{header}{RESET}")
    print("  " + "-" * 75)
    for a in alarms:
        print(format_alarm_row(a))
    print()


def handle_parsed_action(parsed: dict, manager: AlarmManager, silent_set: bool = False) -> bool:
    """
    Executes the parsed command. Returns False if requested to exit.
    """
    action = parsed.get("action")

    if action == "exit":
        print(f"{GREEN}Goodbye! 👋{RESET}")
        return False

    elif action == "help":
        print_help()

    elif action == "empty":
        pass

    elif action == "list":
        active = manager.list_active_alarms()
        print_alarms_table(active, title="ACTIVE ALARMS")

    elif action == "clear":
        count = manager.clear_all()
        print(f"{GREEN}✔ Cancelled {count} active alarm(s).{RESET}\n")

    elif action == "cancel":
        query = parsed.get("cancel_query", "")
        cancelled = manager.cancel_alarm(query)
        if cancelled:
            print(f"{GREEN}✔ Cancelled alarm #{cancelled['id']} ('{cancelled['label']}'){RESET}\n")
        else:
            print(f"{RED}✖ No active alarm matching '{query}' found.{RESET}\n")

    elif action == "set":
        target_dt = parsed["target_time"]
        label = parsed["label"]
        alarm = manager.add_alarm(target_dt, label)
        countdown = AlarmManager.format_countdown(alarm["target_time"])
        target_str = target_dt.strftime("%I:%M:%S %p (%Y-%m-%d)")
        print(f"\n{GREEN}{BOLD}✔ Alarm #{alarm['id']} set for '{label}'!{RESET}")
        print(f"  ⏰ Time: {CYAN}{target_str}{RESET}")
        print(f"  ⏳ Remaining: {YELLOW}{countdown}{RESET}\n")

    elif action == "unknown":
        print(f"{RED}{parsed.get('error', 'Unknown command.')}{RESET}\n")

    return True


def print_help():
    help_text = f"""
{CYAN}{BOLD}Alarm CLI - Command Guide{RESET}
{BOLD}Natural Alarm Syntax:{RESET}
  • {GREEN}set alarm for 5pm{RESET}               (Specific time today/tomorrow)
  • {GREEN}set alarm for 5:44pm{RESET}            (Exact minute)
  • {GREEN}set alarm for 20:30{RESET}             (24-hour format)
  • {GREEN}set alarm for dinner at 8pm{RESET}     (Named alarm with time)
  • {GREEN}set alarm for meeting at 14:00{RESET}  (Named alarm 24hr)
  • {GREEN}set alarm for 20s{RESET}               (Seconds)
  • {GREEN}set alarm for 30m{RESET}               (Minutes)
  • {GREEN}set alarm for 2h{RESET}                (Hours)
  • {GREEN}set alarm for 1h 30m{RESET}            (Combined duration)
  • {GREEN}tea in 5m{RESET}                       (Shorthand named relative)

{BOLD}Management Commands:{RESET}
  • {GREEN}list{RESET} | {GREEN}ls{RESET}                          (List all active alarms)
  • {GREEN}cancel <id>{RESET}                      (Cancel by ID, e.g. 'cancel 1')
  • {GREEN}cancel <name>{RESET}                    (Cancel by name, e.g. 'cancel dinner')
  • {GREEN}clear{RESET}                           (Cancel all active alarms)
  • {GREEN}help{RESET}                            (Show this help message)
  • {GREEN}exit{RESET} | {GREEN}quit{RESET}                     (Exit interactive shell)
"""
    print(help_text)


def start_background_watcher(manager: AlarmManager, stop_event: threading.Event):
    """
    Background worker that polls and rings alarms when due.
    """
    while not stop_event.is_set():
        triggered = manager.check_pending_triggers()
        for alarm in triggered:
            target_dt = datetime.fromisoformat(alarm["target_time"])
            time_str = target_dt.strftime("%I:%M:%S %p")
            render_alarm_banner(alarm["label"], time_str)
            send_system_notification(
                title=f"⏰ Alarm: {alarm['label']}",
                message=f"Time is up! ({time_str})"
            )
            play_sound(beeps=3)
            # Re-print prompt if in interactive shell
            sys.stdout.write(f"\n{CYAN}alarm> {RESET}")
            sys.stdout.flush()

        time.sleep(0.5)


def run_interactive_repl():
    """
    Interactive shell with live real-time scheduler.
    """
    manager = AlarmManager()
    stop_event = threading.Event()

    # Start live watcher thread
    watcher_thread = threading.Thread(
        target=start_background_watcher,
        args=(manager, stop_event),
        daemon=True
    )
    watcher_thread.start()

    print(f"{CYAN}{BOLD}╔═══════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}{BOLD}║         🔔  ALARM CLI CLOCK  🔔           ║{RESET}")
    print(f"{CYAN}{BOLD}╚═══════════════════════════════════════════╝{RESET}")
    print(f"Type a command (e.g. {GREEN}'set alarm for 10s'{RESET} or {GREEN}'dinner at 8pm'{RESET}).")
    print(f"Type {YELLOW}'help'{RESET} for options or {YELLOW}'exit'{RESET} to quit.\n")

    # Initial show active alarms if any
    active = manager.list_active_alarms()
    if active:
        print_alarms_table(active, "ACTIVE ALARMS")

    try:
        while True:
            try:
                user_input = input(f"{CYAN}alarm> {RESET}")
            except EOFError:
                break

            parsed = parse_command(user_input)
            keep_running = handle_parsed_action(parsed, manager)
            if not keep_running:
                break
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted. Exiting...{RESET}")
    finally:
        stop_event.set()


def run_watch_daemon():
    """
    Runs foreground daemon monitoring and triggering alarms until interrupted.
    """
    manager = AlarmManager()
    stop_event = threading.Event()
    print(f"{GREEN}{BOLD}🔔 Alarm CLI Watcher is running in background/daemon mode.{RESET}")
    print(f"Monitoring alarms from {manager.storage_path}... Press Ctrl+C to stop.\n")

    active = manager.list_active_alarms()
    print_alarms_table(active, "CURRENT PENDING ALARMS")

    try:
        start_background_watcher(manager, stop_event)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Stopping daemon watcher.{RESET}")
        stop_event.set()


def main():
    manager = AlarmManager()
    args = sys.argv[1:]

    if not args:
        # Default to interactive REPL
        run_interactive_repl()
        return

    first_arg = args[0].lower()

    if first_arg in ["watch", "daemon", "monitor", "run"]:
        run_watch_daemon()
        return

    if first_arg in ["interactive", "repl", "shell", "-i"]:
        run_interactive_repl()
        return

    # Combine arguments as a single command string
    full_cmd = " ".join(args)
    parsed = parse_command(full_cmd)

    if parsed["action"] == "set":
        # If relative alarm is short (e.g. <= 60s) or user sets an alarm from CLI,
        # we can prompt if they want to wait or run in background
        handle_parsed_action(parsed, manager)
        print(f"{YELLOW}💡 Tip: Run 'python main.py' to enter the live interactive shell or 'python main.py watch' to keep watching.{RESET}")
    else:
        handle_parsed_action(parsed, manager)


if __name__ == "__main__":
    main()
