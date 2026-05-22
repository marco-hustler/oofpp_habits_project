"""Domain models for the Habit Tracker application."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Habit:
    """A tracked habit — daily or weekly."""

    name: str
    periodicity: str
    description: str
    created_at: datetime
    id: Optional[int] = field(default=None)

    def __post_init__(self) -> None:
        if self.periodicity not in ("daily", "weekly"):
            raise ValueError(
                f"Invalid periodicity '{self.periodicity}'. Must be 'daily' or 'weekly'."
            )
        if not self.name or not self.name.strip():
            raise ValueError("Habit name must not be empty.")


@dataclass
class HabitEvent:
    """One check-off for a habit."""

    habit_id: int
    completed_at: datetime
    id: Optional[int] = field(default=None)
