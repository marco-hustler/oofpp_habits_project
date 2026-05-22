"""Tests for HabitManager business logic."""

import pytest
from datetime import datetime

from domain.db import init_db
from domain.repository import HabitRepository, EventRepository
from habit_management.manager import HabitManager


@pytest.fixture
def manager():
    conn = init_db(":memory:")
    return HabitManager(HabitRepository(conn), EventRepository(conn))


class TestCreateHabit:
    def test_creates_and_returns_habit(self, manager):
        h = manager.create_habit("Run", "daily", "Morning run")
        assert h.id is not None
        assert h.name == "Run"
        assert h.periodicity == "daily"

    def test_strips_whitespace_from_name(self, manager):
        h = manager.create_habit("  Run  ", "daily")
        assert h.name == "Run"

    def test_invalid_periodicity_raises(self, manager):
        with pytest.raises(ValueError):
            manager.create_habit("Run", "monthly")

    def test_blank_name_raises(self, manager):
        with pytest.raises(ValueError):
            manager.create_habit("   ", "daily")

    def test_custom_created_at(self, manager):
        ts = datetime(2026, 1, 1)
        h = manager.create_habit("Run", "daily", created_at=ts)
        assert h.created_at == ts


class TestUpdateHabit:
    def test_updates_fields(self, manager):
        h = manager.create_habit("Run", "daily", "old desc")
        updated = manager.update_habit(h.id, "Jog", "weekly", "new desc")
        assert updated.id == h.id
        assert updated.name == "Jog"
        assert updated.periodicity == "weekly"
        assert updated.description == "new desc"

    def test_preserves_created_at(self, manager):
        ts = datetime(2026, 1, 15)
        h = manager.create_habit("Run", "daily", created_at=ts)
        updated = manager.update_habit(h.id, "Run", "weekly")
        assert updated.created_at == ts

    def test_persisted_in_database(self, manager):
        h = manager.create_habit("Run", "daily")
        manager.update_habit(h.id, "Sprint", "weekly")
        loaded = manager.get_habit(h.id)
        assert loaded.name == "Sprint"
        assert loaded.periodicity == "weekly"

    def test_events_still_linked(self, manager):
        h = manager.create_habit("Run", "daily")
        manager.complete_habit(h.id, datetime(2026, 2, 1))
        manager.update_habit(h.id, "Jog", "daily")
        assert len(manager.get_events(h.id)) == 1

    def test_strips_whitespace_from_name(self, manager):
        h = manager.create_habit("Run", "daily")
        updated = manager.update_habit(h.id, "  Jog  ", "daily")
        assert updated.name == "Jog"

    def test_invalid_periodicity_raises(self, manager):
        h = manager.create_habit("Run", "daily")
        with pytest.raises(ValueError):
            manager.update_habit(h.id, "Run", "monthly")

    def test_blank_name_raises(self, manager):
        h = manager.create_habit("Run", "daily")
        with pytest.raises(ValueError):
            manager.update_habit(h.id, "   ", "daily")

    def test_update_nonexistent_raises(self, manager):
        with pytest.raises(ValueError, match="not found"):
            manager.update_habit(999, "Run", "daily")


class TestDeleteHabit:
    def test_deletes_existing_habit(self, manager):
        h = manager.create_habit("Run", "daily")
        manager.delete_habit(h.id)
        assert manager.get_habit(h.id) is None

    def test_deletes_associated_events(self, manager):
        h = manager.create_habit("Run", "daily")
        manager.complete_habit(h.id)
        manager.delete_habit(h.id)
        assert manager.get_events(h.id) == []

    def test_delete_nonexistent_raises(self, manager):
        with pytest.raises(ValueError, match="not found"):
            manager.delete_habit(999)


class TestCompleteHabit:
    def test_creates_event(self, manager):
        h = manager.create_habit("Run", "daily")
        ev = manager.complete_habit(h.id)
        assert ev.id is not None
        assert ev.habit_id == h.id

    def test_complete_with_custom_timestamp(self, manager):
        h = manager.create_habit("Run", "daily")
        ts = datetime(2026, 3, 1, 8, 0)
        ev = manager.complete_habit(h.id, completed_at=ts)
        assert ev.completed_at == ts

    def test_complete_nonexistent_habit_raises(self, manager):
        with pytest.raises(ValueError, match="not found"):
            manager.complete_habit(999)

    def test_multiple_completions_allowed(self, manager):
        h = manager.create_habit("Run", "daily")
        manager.complete_habit(h.id, datetime(2026, 1, 1))
        manager.complete_habit(h.id, datetime(2026, 1, 2))
        assert len(manager.get_events(h.id)) == 2


class TestListHabits:
    def test_empty_returns_empty_list(self, manager):
        assert manager.list_habits() == []

    def test_returns_all_habits(self, manager):
        manager.create_habit("A", "daily")
        manager.create_habit("B", "weekly")
        assert len(manager.list_habits()) == 2
