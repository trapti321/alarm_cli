#!/usr/bin/env python3
"""
Alarm CLI Clock
Execute directly with Python 3:
    python run_alarm.py
    python run_alarm.py "set alarm for 5pm"
    python run_alarm.py "set alarm for dinner at 8pm"
    python run_alarm.py "set alarm for 20s"
    python run_alarm.py list
    python run_alarm.py cancel 1
"""
import sys
import os

# Ensure local package is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from alarm_cli.cli import main

if __name__ == "__main__":
    main()
