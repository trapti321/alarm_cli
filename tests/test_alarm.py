import unittest
from datetime import datetime, timedelta
from alarm_cli.parser import parse_command, parse_relative_duration, parse_time_of_day
from alarm_cli.manager import AlarmManager
import tempfile
from pathlib import Path


class TestAlarmParser(unittest.TestCase):

    def setUp(self):
        # Fixed reference time: 2026-09-13 14:00:00 (2:00 PM)
        self.now = datetime(2026, 9, 13, 14, 0, 0)

    def test_specific_time_5pm(self):
        res = parse_command("set alarm for 5pm", self.now)
        self.assertEqual(res["action"], "set")
        self.assertEqual(res["target_time"], datetime(2026, 9, 13, 17, 0, 0))
        self.assertEqual(res["label"], "Alarm")

    def test_specific_time_5_44pm(self):
        res = parse_command("set alarm for 5:44pm", self.now)
        self.assertEqual(res["action"], "set")
        self.assertEqual(res["target_time"], datetime(2026, 9, 13, 17, 44, 0))

    def test_specific_time_20_30(self):
        res = parse_command("set alarm for 20:30", self.now)
        self.assertEqual(res["action"], "set")
        self.assertEqual(res["target_time"], datetime(2026, 9, 13, 20, 30, 0))

    def test_past_time_rolls_to_tomorrow(self):
        # 10am is in the past relative to 14:00 (2pm)
        res = parse_command("set alarm for 10am", self.now)
        self.assertEqual(res["action"], "set")
        self.assertEqual(res["target_time"], datetime(2026, 9, 14, 10, 0, 0))

    def test_named_time_dinner(self):
        res = parse_command("set alarm for dinner at 8pm", self.now)
        self.assertEqual(res["action"], "set")
        self.assertEqual(res["label"], "dinner")
        self.assertEqual(res["target_time"], datetime(2026, 9, 13, 20, 0, 0))

    def test_named_time_meeting(self):
        res = parse_command("set alarm for team meeting at 15:30", self.now)
        self.assertEqual(res["action"], "set")
        self.assertEqual(res["label"], "team meeting")
        self.assertEqual(res["target_time"], datetime(2026, 9, 13, 15, 30, 0))

    def test_relative_duration_20s(self):
        res = parse_command("set alarm for 20s", self.now)
        self.assertEqual(res["action"], "set")
        self.assertEqual(res["duration_sec"], 20)
        self.assertEqual(res["target_time"], datetime(2026, 9, 13, 14, 0, 20))

    def test_relative_duration_30m(self):
        res = parse_command("set alarm for 30m", self.now)
        self.assertEqual(res["action"], "set")
        self.assertEqual(res["duration_sec"], 1800)
        self.assertEqual(res["target_time"], datetime(2026, 9, 13, 14, 30, 0))

    def test_relative_duration_2h(self):
        res = parse_command("set alarm for 2h", self.now)
        self.assertEqual(res["action"], "set")
        self.assertEqual(res["duration_sec"], 7200)
        self.assertEqual(res["target_time"], datetime(2026, 9, 13, 16, 0, 0))

    def test_relative_duration_1h_30m(self):
        res = parse_command("set alarm for 1h 30m", self.now)
        self.assertEqual(res["action"], "set")
        self.assertEqual(res["duration_sec"], 5400)
        self.assertEqual(res["target_time"], datetime(2026, 9, 13, 15, 30, 0))

    def test_management_commands(self):
        self.assertEqual(parse_command("list")["action"], "list")
        self.assertEqual(parse_command("ls")["action"], "list")
        self.assertEqual(parse_command("list alarms")["action"], "list")

        cancel_id = parse_command("cancel 1")
        self.assertEqual(cancel_id["action"], "cancel")
        self.assertEqual(cancel_id["cancel_query"], "1")

        cancel_name = parse_command("cancel dinner")
        self.assertEqual(cancel_name["action"], "cancel")
        self.assertEqual(cancel_name["cancel_query"], "dinner")

        self.assertEqual(parse_command("clear")["action"], "clear")
        self.assertEqual(parse_command("help")["action"], "help")
        self.assertEqual(parse_command("exit")["action"], "exit")

    def test_countdown_commands(self):
        self.assertEqual(parse_command("countdown")["action"], "countdown")
        self.assertEqual(parse_command("show countdown")["action"], "countdown")
        self.assertEqual(parse_command("timer")["action"], "countdown")
        self.assertEqual(parse_command("live")["action"], "countdown")
        self.assertEqual(parse_command("watch countdown")["action"], "countdown")

    def test_timer_set_with_countdown(self):
        res = parse_command("timer 20s", self.now)
        self.assertEqual(res["action"], "set")
        self.assertEqual(res["duration_sec"], 20)
        self.assertTrue(res["show_countdown"])

        res2 = parse_command("set alarm for 10s --countdown", self.now)
        self.assertEqual(res2["action"], "set")
        self.assertTrue(res2["show_countdown"])


class TestAlarmManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = Path(self.temp_dir.name) / "test_alarms.json"
        self.manager = AlarmManager(storage_path=self.storage_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_and_list_alarms(self):
        t1 = datetime(2026, 9, 13, 15, 0, 0)
        t2 = datetime(2026, 9, 13, 16, 0, 0)
        
        a1 = self.manager.add_alarm(t1, "Meeting")
        a2 = self.manager.add_alarm(t2, "Dinner")
        
        active = self.manager.list_active_alarms()
        self.assertEqual(len(active), 2)
        self.assertEqual(active[0]["id"], 1)
        self.assertEqual(active[0]["label"], "Meeting")
        self.assertEqual(active[1]["id"], 2)
        self.assertEqual(active[1]["label"], "Dinner")

    def test_cancel_alarm_by_id(self):
        t = datetime(2026, 9, 13, 15, 0, 0)
        self.manager.add_alarm(t, "Meeting")
        
        cancelled = self.manager.cancel_alarm("1")
        self.assertIsNotNone(cancelled)
        self.assertEqual(len(self.manager.list_active_alarms()), 0)

    def test_cancel_alarm_by_label(self):
        t = datetime(2026, 9, 13, 15, 0, 0)
        self.manager.add_alarm(t, "Important Meeting")
        
        cancelled = self.manager.cancel_alarm("meeting")
        self.assertIsNotNone(cancelled)
        self.assertEqual(cancelled["label"], "Important Meeting")
        self.assertEqual(len(self.manager.list_active_alarms()), 0)

    def test_check_pending_triggers(self):
        past_target = datetime(2026, 9, 13, 13, 59, 0)
        future_target = datetime(2026, 9, 13, 15, 0, 0)
        now = datetime(2026, 9, 13, 14, 0, 0)

        self.manager.add_alarm(past_target, "Old Alarm")
        self.manager.add_alarm(future_target, "Future Alarm")

        triggered = self.manager.check_pending_triggers(now)
        self.assertEqual(len(triggered), 1)
        self.assertEqual(triggered[0]["label"], "Old Alarm")
        self.assertEqual(len(self.manager.list_active_alarms()), 1)

    def test_format_digital_countdown(self):
        now = datetime(2026, 9, 13, 14, 0, 0)
        target = datetime(2026, 9, 13, 14, 2, 15)
        digital = AlarmManager.format_digital_countdown(target.isoformat(), now=now)
        self.assertEqual(digital, "00:02:15")

        past = datetime(2026, 9, 13, 13, 59, 0)
        self.assertEqual(AlarmManager.format_digital_countdown(past.isoformat(), now=now), "00:00:00")


if __name__ == "__main__":
    unittest.main()

