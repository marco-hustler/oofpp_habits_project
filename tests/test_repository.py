"""Tests for HabitRepository and EventRepository using an in-memory SQLite DB."""

import pytest
from datetime import datetime

from domain.db import init_db
from domain.models import Habit, HabitEvent
from domain.repository import HabitRepository, EventRepository


@pytest.fixture
def conn():
    """Provide a fresh in-memory database for each test."""
    c = init_db(":memory:")
    yield c
    c.close()


@pytest.fixture
def repos(conn):
    return HabitRepository(conn), EventRepository(conn)


class TestHabitRepository:
    def test_save_new_habit_assigns_id(self, repos):
        habit_repo, _ = repos
        h = Habit(name="Run", periodicity="daily", description="", created_at=datetime.now())
        saved = habit_repo.save(h)
        assert saved.id is not None
        assert saved.id >= 1

    def test_find_by_id_returns_habit(self, repos):
        habit_repo, _ = repos
        h = habit_repo.save(
            Habit(name="Run", periodicity="daily", description="", created_at=datetime.now())
        )
        found = habit_repo.find_by_id(h.id)
        assert found is not None
        assert found.name == "Run"

    def test_find_by_id_missing_returns_none(self, repos):
        habit_repo, _ = repos
        assert habit_repo.find_by_id(999) is None

    def test_find_all_returns_all_habits(self, repos):
        habit_repo, _ = repos
        habit_repo.save(Habit(name="A", periodicity="daily", description="", created_at=datetime.now()))
        habit_repo.save(Habit(name="B", periodicity="weekly", description="", created_at=datetime.now()))
        assert len(habit_repo.find_all()) == 2

    def test_delete_removes_habit(self, repos):
        habit_repo, _ = repos
        h = habit_repo.save(
            Habit(name="Run", periodicity="daily", description="", created_at=datetime.now())
        )
        habit_repo.delete(h.id)
        assert habit_repo.find_by_id(h.id) is None

    def test_update_existing_habit(self, repos):
        habit_repo, _ = repos
        h = habit_repo.save(
            Habit(name="Run", periodicity="daily", description="old", created_at=datetime.now())
        )
        h.description = "new"
        habit_repo.save(h)
        updated = habit_repo.find_by_id(h.id)
        assert updated.description == "new"


class TestEventRepository:
    def test_save_event_assigns_id(self, repos):
        habit_repo, event_repo = repos
        h = habit_repo.save(
            Habit(name="Run", periodicity="daily", description="", created_at=datetime.now())
        )
        ev = event_repo.save(HabitEvent(habit_id=h.id, completed_at=datetime.now()))
        assert ev.id is not None

    def test_find_by_habit_returns_events(self, repos):
        habit_repo, event_repo = repos
        h = habit_repo.save(
            Habit(name="Run", periodicity="daily", description="", created_at=datetime.now())
        )
        event_repo.save(HabitEvent(habit_id=h.id, completed_at=datetime(2026, 1, 1)))
        event_repo.save(HabitEvent(habit_id=h.id, completed_at=datetime(2026, 1, 2)))
        events = event_repo.find_by_habit(h.id)
        assert len(events) == 2

    def test_delete_by_habit_removes_events(self, repos):
        habit_repo, event_repo = repos
        h = habit_repo.save(
            Habit(name="Run", periodicity="daily", description="", created_at=datetime.now())
        )
        event_repo.save(HabitEvent(habit_id=h.id, completed_at=datetime.now()))
        event_repo.delete_by_habit(h.id)
        assert event_repo.find_by_habit(h.id) == []

    def test_cascade_delete_via_habit(self, repos):
        """Habit delete should remove its events too."""
        habit_repo, event_repo = repos
        h = habit_repo.save(
            Habit(name="Run", periodicity="daily", description="", created_at=datetime.now())
        )
        event_repo.save(HabitEvent(habit_id=h.id, completed_at=datetime.now()))
        habit_repo.delete(h.id)
        assert event_repo.find_by_habit(h.id) == []
