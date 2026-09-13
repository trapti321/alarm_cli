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

    elif action == "countdown":
        active = manager.list_active_alarms()
        if not active:
            print(f"{YELLOW}No active alarms pending. Set one with 'set alarm for 10s' or 'dinner at 8pm'.{RESET}\n")
        else:
            run_live_countdown(manager, auto_exit_when_done=False)

    elif action == "set":
        target_dt = parsed["target_time"]
        label = parsed["label"]
        alarm = manager.add_alarm(target_dt, label)
        countdown = AlarmManager.format_countdown(alarm["target_time"])
        target_str = target_dt.strftime("%I:%M:%S %p (%Y-%m-%d)")
        print(f"\n{GREEN}{BOLD}✔ Alarm #{alarm['id']} set for '{label}'!{RESET}")
        print(f"  ⏰ Time: {CYAN}{target_str}{RESET}")
        print(f"  ⏳ Remaining: {YELLOW}{countdown}{RESET}\n")

        if parsed.get("show_countdown"):
            run_live_countdown(manager, auto_exit_when_done=True, specific_alarm_id=alarm["id"])

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
  • {GREEN}timer 30s{RESET} / {GREEN}countdown 1m{RESET}        (Set alarm with live ticking countdown)
  • {GREEN}set alarm for 15s --countdown{RESET}   (Set alarm and display live countdown)

{BOLD}Management & Display Commands:{RESET}
  • {GREEN}countdown{RESET} | {GREEN}show countdown{RESET}      (Show live updating countdown clock)
  • {GREEN}list{RESET} | {GREEN}ls{RESET}                          (List all active alarms with remaining time)
  • {GREEN}cancel <id>{RESET}                      (Cancel by ID, e.g. 'cancel 1')
  • {GREEN}cancel <name>{RESET}                    (Cancel by name, e.g. 'cancel dinner')
  • {GREEN}clear{RESET}                           (Cancel all active alarms)
  • {GREEN}help{RESET}                            (Show this help message)
  • {GREEN}exit{RESET} | {GREEN}quit{RESET}                     (Exit interactive shell)
"""
    print(help_text)


def run_live_countdown(manager: AlarmManager, auto_exit_when_done: bool = False, specific_alarm_id: Optional[int] = None):
    """
    Displays live real-time countdown for active alarms.
    Press Ctrl+C to return.
    """
    print(f"{CYAN}{BOLD}⏳ LIVE COUNTDOWN STARTED{RESET} {YELLOW}(Press Ctrl+C to return){RESET}\n")

    try:
        while True:
            active = manager.list_active_alarms()
            if specific_alarm_id:
                active = [a for a in active if a.get("id") == specific_alarm_id]

            if not active:
                if auto_exit_when_done:
                    break
                sys.stdout.write(f"\r{YELLOW}No active alarms pending. (Press Ctrl+C to return)           {RESET}")
                sys.stdout.flush()
                time.sleep(1)
                continue

            # Check if any alarm should trigger
            triggered = manager.check_pending_triggers()
            for t_alarm in triggered:
                sys.stdout.write("\r" + " " * 85 + "\r")
                target_dt = datetime.fromisoformat(t_alarm["target_time"])
                time_str = target_dt.strftime("%I:%M:%S %p")
                render_alarm_banner(t_alarm["label"], time_str)
                send_system_notification(
                    title=f"⏰ Alarm: {t_alarm['label']}",
                    message=f"Time is up! ({time_str})"
                )
                play_sound(beeps=3)

            # Re-fetch active after potential triggers
            active = [a for a in active if a.get("status") == "pending"]
            if not active and auto_exit_when_done:
                break

            if len(active) == 1:
                alarm = active[0]
                t_iso = alarm["target_time"]
                target_dt = datetime.fromisoformat(t_iso)
                target_str = target_dt.strftime("%I:%M:%S %p")
                digital = AlarmManager.format_digital_countdown(t_iso)
                countdown_readable = AlarmManager.format_countdown(t_iso)

                status_line = f"\r{CYAN}⏰ #{alarm['id']} '{alarm['label']}'{RESET} ➔ {BOLD}{YELLOW}⏳ {digital}{RESET} remaining ({countdown_readable}) | Target: {target_str}   "
                sys.stdout.write(status_line)
                sys.stdout.flush()
            elif len(active) > 1:
                # Multi-alarm compact live status line
                parts = []
                for a in active[:3]:
                    dig = AlarmManager.format_digital_countdown(a["target_time"])
                    parts.append(f"#{a['id']} '{a['label']}': {YELLOW}{dig}{RESET}")
                summary = " | ".join(parts)
                if len(active) > 3:
                    summary += f" (+{len(active)-3} more)"
                sys.stdout.write(f"\r{CYAN}⏳ Active ({len(active)}):{RESET} {summary}   ")
                sys.stdout.flush()

            time.sleep(0.5)

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\r" + " " * 85 + "\r")
        sys.stdout.flush()
        print(f"{YELLOW}✔ Live countdown stopped.{RESET}\n")


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
    print(f"Type {YELLOW}'countdown'{RESET} for live clock, {YELLOW}'help'{RESET} for options, or {YELLOW}'exit'{RESET} to quit.\n")

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
    Runs foreground daemon monitoring and triggering alarms with live countdown.
    """
    manager = AlarmManager()
    print(f"{GREEN}{BOLD}🔔 Alarm CLI Watcher is running in live countdown monitor mode.{RESET}")
    print(f"Monitoring alarms from {manager.storage_path}... Press Ctrl+C to stop.\n")

    active = manager.list_active_alarms()
    if active:
        print_alarms_table(active, "CURRENT PENDING ALARMS")

    run_live_countdown(manager, auto_exit_when_done=False)


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

    if first_arg in ["countdown", "timer", "live", "countdowns", "timers", "show-countdown"]:
        active = manager.list_active_alarms()
        if not active:
            print(f"{YELLOW}No active alarms to count down. Set one first!{RESET}")
            print(f"Example: python run_alarm.py 'set alarm for 10s'\n")
            return
        run_live_countdown(manager, auto_exit_when_done=False)
        return

    # Combine arguments as a single command string
    full_cmd = " ".join(args)
    parsed = parse_command(full_cmd)

    if parsed["action"] == "set":
        handle_parsed_action(parsed, manager)
        if not parsed.get("show_countdown"):
            print(f"{YELLOW}💡 Tip: Run 'python run_alarm.py countdown' to view live timer, or 'python run_alarm.py' for interactive shell.{RESET}")
    else:
        handle_parsed_action(parsed, manager)


if __name__ == "__main__":
    main()

