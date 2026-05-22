"""Tests for domain models: Habit and HabitEvent."""

import pytest
from datetime import datetime

from domain.models import Habit, HabitEvent


class TestHabit:
    def test_valid_daily_habit(self):
        h = Habit(name="Run", periodicity="daily", description="", created_at=datetime.now())
        assert h.name == "Run"
        assert h.periodicity == "daily"
        assert h.id is None

    def test_valid_weekly_habit(self):
        h = Habit(name="Review", periodicity="weekly", description="", created_at=datetime.now())
        assert h.periodicity == "weekly"

    def test_invalid_periodicity_raises(self):
        with pytest.raises(ValueError, match="Invalid periodicity"):
            Habit(name="Run", periodicity="monthly", description="", created_at=datetime.now())

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name must not be empty"):
            Habit(name="  ", periodicity="daily", description="", created_at=datetime.now())

    def test_id_defaults_to_none(self):
        h = Habit(name="X", periodicity="daily", description="", created_at=datetime.now())
        assert h.id is None


class TestHabitEvent:
    def test_valid_event(self):
        ts = datetime(2026, 1, 15, 9, 0)
        ev = HabitEvent(habit_id=1, completed_at=ts)
        assert ev.habit_id == 1
        assert ev.completed_at == ts
        assert ev.id is None
