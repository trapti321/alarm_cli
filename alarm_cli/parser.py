"""
Natural language parser for alarm commands.
Handles:
- Specific time: 'set alarm for 5pm', 'set alarm for 5:44pm', 'set alarm for 20:30', '7:15 am'
- Named time: 'set alarm for dinner at 8pm', 'set alarm for meeting at 14:30'
- Relative duration: 'set alarm for 20s', 'set alarm for 30m', 'set alarm for 2h', 'set alarm for 1h 30m'
- Management: 'list', 'cancel 1', 'cancel dinner', 'clear'
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any


def parse_relative_duration(text: str) -> Optional[int]:
    """
    Parses strings like '20s', '30m', '2h', '1h 30m', '45 secs', '1 hour 15 mins 30 seconds'.
    Returns total duration in seconds, or None if no match.
    """
    text = text.strip().lower()

    # Pattern to extract hours, minutes, seconds
    total_seconds = 0
    matched = False

    # Regex for components like 1h, 1 hr, 1 hour, 30m, 30 min, 20s, 20 sec
    # Token matches
    pattern = r'(\d+(?:\.\d+)?)\s*(h(?:ours?|rs?)?|m(?:in(?:ute)?s?)?|s(?:ec(?:ond)?s?)?)'
    matches = re.findall(pattern, text)

    if matches:
        matched = True
        for value_str, unit in matches:
            val = float(value_str)
            unit_initial = unit[0].lower()
            if unit_initial == 'h':
                total_seconds += int(val * 3600)
            elif unit_initial == 'm':
                total_seconds += int(val * 60)
            elif unit_initial == 's':
                total_seconds += int(val)

    if matched and total_seconds > 0:
        return total_seconds

    # Also match plain numbers with suffix attached or separated
    return None


def parse_time_of_day(time_str: str, now: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parses time strings like:
    - '5pm', '5:44pm', '5:44:10pm', '5:00 pm', '8 am'
    - '20:30', '8:00', '17:45:00'
    Returns datetime object for the next occurrence of that time (today or tomorrow).
    """
    if now is None:
        now = datetime.now()

    time_str = time_str.strip().lower()

    # Normalize spacing in '5:44 pm' -> '5:44pm'
    time_str = re.sub(r'\s+(am|pm)', r'\1', time_str)

    formats_to_try = [
        ("%I:%M:%S%p", True),
        ("%I:%M%p", True),
        ("%I%p", True),
        ("%H:%M:%S", False),
        ("%H:%M", False),
    ]

    parsed_time = None
    for fmt, is_12hr in formats_to_try:
        try:
            t = datetime.strptime(time_str, fmt).time()
            parsed_time = t
            break
        except ValueError:
            continue

    if not parsed_time:
        # Check single digit or number without am/pm if format is HH
        if re.match(r'^\d{1,2}$', time_str):
            hr = int(time_str)
            if 0 <= hr <= 23:
                try:
                    parsed_time = datetime.strptime(f"{hr}:00", "%H:%M").time()
                except ValueError:
                    pass

    if not parsed_time:
        return None

    # Calculate target datetime
    target = now.replace(
        hour=parsed_time.hour,
        minute=parsed_time.minute,
        second=parsed_time.second,
        microsecond=0
    )

    # If target is in the past, schedule for tomorrow
    if target <= now:
        target += timedelta(days=1)

    return target


def parse_command(raw_input: str, now: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Parses user input into a command dictionary.
    
    Returns:
      {
        "action": "set" | "list" | "cancel" | "clear" | "help" | "exit" | "unknown",
        "target_time": datetime | None,
        "label": str,
        "duration_sec": int | None,
        "cancel_query": str | None,
        "raw": str,
        "error": str | None
      }
    """
    if now is None:
        now = datetime.now()

    cmd = raw_input.strip()
    lower_cmd = cmd.lower()

    if not cmd:
        return {"action": "empty", "raw": cmd}

    # Help & Exit
    if lower_cmd in ["help", "?", "h", "--help", "-h"]:
        return {"action": "help", "raw": cmd}
    if lower_cmd in ["exit", "quit", "q"]:
        return {"action": "exit", "raw": cmd}

    # List alarms
    if lower_cmd in ["list", "ls", "show", "list alarms", "show alarms", "alarms"]:
        return {"action": "list", "raw": cmd}

    # Clear / delete all
    if lower_cmd in ["clear", "clear all", "cancel all", "delete all"]:
        return {"action": "clear", "raw": cmd}

    # Cancel command: 'cancel 1', 'cancel dinner', 'delete 2', 'remove dinner'
    cancel_match = re.match(r'^(?:cancel|delete|remove|rm)\s+(?:alarm\s+)?(.+)$', lower_cmd)
    if cancel_match:
        query = cancel_match.group(1).strip()
        return {
            "action": "cancel",
            "cancel_query": query,
            "raw": cmd
        }

    # Strip prefixes like "set alarm for", "set alarm", "set an alarm for", "alarm for", "alarm"
    clean_text = cmd
    prefixes = [
        r'^set\s+(?:an\s+)?alarm\s+(?:for\s+)?',
        r'^alarm\s+(?:for\s+)?',
        r'^set\s+',
        r'^remind\s+me\s+to\s+',
        r'^remind\s+me\s+for\s+',
    ]
    for p in prefixes:
        m = re.match(p, clean_text, re.IGNORECASE)
        if m:
            clean_text = clean_text[m.end():].strip()
            break

    # Check for named time: "<label> at <time>" (e.g. "dinner at 8pm", "meeting at 14:30")
    named_at_match = re.match(r'^(.*?)\s+at\s+([0-9:apmAPM\s]+)$', clean_text)
    if named_at_match:
        label = named_at_match.group(1).strip()
        time_part = named_at_match.group(2).strip()
        target_dt = parse_time_of_day(time_part, now)
        if target_dt:
            return {
                "action": "set",
                "target_time": target_dt,
                "label": label if label else "Alarm",
                "duration_sec": int((target_dt - now).total_seconds()),
                "raw": cmd
            }

    # Check for named relative: "<label> in <duration>" (e.g. "tea in 5m", "break in 30s")
    named_in_match = re.match(r'^(.*?)\s+in\s+([0-9a-zA-Z\s]+)$', clean_text)
    if named_in_match:
        label = named_in_match.group(1).strip()
        dur_part = named_in_match.group(2).strip()
        dur_sec = parse_relative_duration(dur_part)
        if dur_sec:
            target_dt = now + timedelta(seconds=dur_sec)
            return {
                "action": "set",
                "target_time": target_dt,
                "label": label if label else "Alarm",
                "duration_sec": dur_sec,
                "raw": cmd
            }

    # Check for pure relative duration: "20s", "30m", "2h", "1h 30m", "in 15m"
    rel_candidate = clean_text
    if rel_candidate.lower().startswith("in "):
        rel_candidate = rel_candidate[3:].strip()
    
    dur_sec = parse_relative_duration(rel_candidate)
    if dur_sec is not None:
        target_dt = now + timedelta(seconds=dur_sec)
        return {
            "action": "set",
            "target_time": target_dt,
            "label": "Alarm",
            "duration_sec": dur_sec,
            "raw": cmd
        }

    # Check for pure time of day: "5pm", "5:44pm", "20:30", "at 8:00"
    tod_candidate = clean_text
    if tod_candidate.lower().startswith("at "):
        tod_candidate = tod_candidate[3:].strip()

    target_dt = parse_time_of_day(tod_candidate, now)
    if target_dt:
        return {
            "action": "set",
            "target_time": target_dt,
            "label": "Alarm",
            "duration_sec": int((target_dt - now).total_seconds()),
            "raw": cmd
        }

    return {
        "action": "unknown",
        "raw": cmd,
        "error": f"Could not recognize command: '{cmd}'. Type 'help' for examples."
    }
