"""
Alarm state manager.
Persists alarms to a local JSON file and manages alarm lifecycles.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

DEFAULT_STORAGE_PATH = Path.home() / ".alarm_cli" / "alarms.json"


class AlarmManager:
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or DEFAULT_STORAGE_PATH
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.alarms: List[Dict[str, Any]] = []
        self.load()

    def load(self):
        """Loads alarms from disk."""
        if not self.storage_path.exists():
            self.alarms = []
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                self.alarms = json.load(f)
        except Exception:
            self.alarms = []

    def save(self):
        """Saves alarms to disk."""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.alarms, f, indent=2)
        except Exception as e:
            print(f"Error saving alarms: {e}")

    def get_next_id(self) -> int:
        if not self.alarms:
            return 1
        return max(a.get("id", 0) for a in self.alarms) + 1

    def add_alarm(self, target_time: datetime, label: str = "Alarm") -> Dict[str, Any]:
        """Adds a new alarm and persists it."""
        self.load()
        alarm = {
            "id": self.get_next_id(),
            "label": label,
            "target_time": target_time.isoformat(),
            "created_at": datetime.now().isoformat(),
            "status": "pending"  # pending, triggered, cancelled
        }
        self.alarms.append(alarm)
        self.save()
        return alarm

    def list_active_alarms(self) -> List[Dict[str, Any]]:
        """Returns all pending alarms sorted by target time."""
        self.load()
        pending = [a for a in self.alarms if a.get("status") == "pending"]
        pending.sort(key=lambda x: x["target_time"])
        return pending

    def list_all_alarms(self) -> List[Dict[str, Any]]:
        self.load()
        return sorted(self.alarms, key=lambda x: x["target_time"])

    def cancel_alarm(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Cancels an alarm by ID or matching label name.
        """
        self.load()
        query = query.strip()

        # Try ID match first
        if query.isdigit():
            alarm_id = int(query)
            for a in self.alarms:
                if a.get("id") == alarm_id and a.get("status") == "pending":
                    a["status"] = "cancelled"
                    self.save()
                    return a

        # Match label (case-insensitive substring)
        for a in self.alarms:
            if query.lower() in a.get("label", "").lower() and a.get("status") == "pending":
                a["status"] = "cancelled"
                self.save()
                return a

        return None

    def clear_all(self) -> int:
        """Cancels all pending alarms."""
        self.load()
        count = 0
        for a in self.alarms:
            if a.get("status") == "pending":
                a["status"] = "cancelled"
                count += 1
        self.save()
        return count

    def mark_triggered(self, alarm_id: int):
        self.load()
        for a in self.alarms:
            if a.get("id") == alarm_id:
                a["status"] = "triggered"
        self.save()

    def check_pending_triggers(self, now: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Returns all pending alarms whose target time <= now, and marks them triggered.
        """
        if now is None:
            now = datetime.now()

        self.load()
        triggered = []
        for a in self.alarms:
            if a.get("status") == "pending":
                t = datetime.fromisoformat(a["target_time"])
                if t <= now:
                    a["status"] = "triggered"
                    triggered.append(a)

        if triggered:
            self.save()

        return triggered

    @staticmethod
    def format_countdown(target_iso: str, now: Optional[datetime] = None) -> str:
        """Formats remaining time as '1h 25m 10s' or 'triggered'."""
        if now is None:
            now = datetime.now()
        target = datetime.fromisoformat(target_iso)
        diff = (target - now).total_seconds()
        if diff <= 0:
            return "Now / Due"
        
        diff = int(diff)
        hours, rem = divmod(diff, 3600)
        minutes, seconds = divmod(rem, 60)

        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        return " ".join(parts)
