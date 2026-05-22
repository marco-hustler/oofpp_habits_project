"""Habit management — create, edit, delete habits and record check-offs."""

from datetime import datetime
from typing import Optional

from domain.models import Habit, HabitEvent
from domain.repository import HabitRepository, EventRepository


class HabitManager:
    """Business logic for habits; persistence goes through the repos."""

    def __init__(
        self,
        habit_repo: HabitRepository,
        event_repo: EventRepository,
    ) -> None:
        self._habits = habit_repo
        self._events = event_repo

    def create_habit(
        self,
        name: str,
        periodicity: str,
        description: str = "",
        created_at: Optional[datetime] = None,
    ) -> Habit:
        """Create and save a new habit (daily or weekly)."""
        habit = Habit(
            name=name.strip(),
            periodicity=periodicity,
            description=description,
            created_at=created_at or datetime.now(),
        )
        return self._habits.save(habit)

    def update_habit(
        self,
        habit_id: int,
        name: str,
        periodicity: str,
        description: str = "",
    ) -> Habit:
        """Change name, periodicity, or description; keeps id and created_at."""
        existing = self._habits.find_by_id(habit_id)
        if not existing:
            raise ValueError(f"Habit with id={habit_id} not found.")
        habit = Habit(
            id=existing.id,
            name=name.strip(),
            periodicity=periodicity,
            description=description,
            created_at=existing.created_at,
        )
        return self._habits.save(habit)

    def delete_habit(self, habit_id: int) -> None:
        """Remove a habit and its events."""
        if not self._habits.find_by_id(habit_id):
            raise ValueError(f"Habit with id={habit_id} not found.")
        self._habits.delete(habit_id)

    def get_habit(self, habit_id: int) -> Optional[Habit]:
        """Look up one habit by id, or None."""
        return self._habits.find_by_id(habit_id)

    def list_habits(self) -> list[Habit]:
        """All habits, oldest first."""
        return self._habits.find_all()

    def complete_habit(
        self,
        habit_id: int,
        completed_at: Optional[datetime] = None,
    ) -> HabitEvent:
        """Record a check-off for a habit."""
        if not self._habits.find_by_id(habit_id):
            raise ValueError(f"Habit with id={habit_id} not found.")
        event = HabitEvent(
            habit_id=habit_id,
            completed_at=completed_at or datetime.now(),
        )
        return self._events.save(event)

    def get_events(self, habit_id: int) -> list[HabitEvent]:
        """All check-offs for a habit, oldest first."""
        return self._events.find_by_habit(habit_id)
