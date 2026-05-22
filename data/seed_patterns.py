"""Shared 4-week patterns for demo seed and streak tests."""

from __future__ import annotations

from datetime import datetime, timedelta

from domain.models import Habit, HabitEvent

# 28 days — index 0 is the oldest day in the window
DAILY_PATTERNS: dict[str, list[bool]] = {
    "Drink 2L of Water": [
        True, True, True, True, True, True, True,
        True, True, True, True, True, True, True,
        True, True, False, True, True, True, True,
        True, True, True, True, True, True, True,
    ],
    "Morning Run": [
        True, False, True, True, False, True, True,
        True, True, False, True, True, True, False,
        False, True, True, True, False, True, True,
        True, False, True, True, True, False, True,
    ],
    "Read 20 Pages": [
        True, True, False, True, True, True, False,
        True, True, True, False, True, True, True,
        True, False, True, True, True, True, False,
        True, True, True, True, False, True, True,
    ],
}

# 4 weeks — index 0 is the oldest week
WEEKLY_PATTERNS: dict[str, list[bool]] = {
    "Weekly Review": [True, True, True, True],
    "Grocery Shopping": [True, True, False, True],
}

HABIT_DESCRIPTIONS: dict[str, str] = {
    "Drink 2L of Water": "Stay hydrated by drinking at least 2 litres of water every day.",
    "Morning Run": "Go for a run of at least 20 minutes in the morning.",
    "Read 20 Pages": "Read at least 20 pages of a non-fiction or fiction book.",
    "Weekly Review": "Review goals, tasks and calendar for the upcoming week.",
    "Grocery Shopping": "Do the weekly grocery shopping.",
}

# Fixed date so pytest streak expectations stay stable
SEED_REFERENCE_TODAY = datetime(2026, 5, 22, 0, 0, 0)

SEED_EXPECTED_STREAKS: dict[str, dict[str, int]] = {
    "Drink 2L of Water": {"current": 11, "longest": 16},
    "Morning Run": {"current": 1, "longest": 4},
    "Read 20 Pages": {"current": 2, "longest": 4},
    "Weekly Review": {"current": 4, "longest": 4},
    "Grocery Shopping": {"current": 1, "longest": 2},
}


def four_week_start(reference_today: datetime) -> datetime:
    """Midnight on the first day of the 28-day window."""
    return reference_today.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
        days=27
    )


def build_seed_events(
    habit_id: int,
    periodicity: str,
    pattern: list[bool],
    reference_today: datetime,
) -> list[HabitEvent]:
    """Build events from a bool pattern (same rules as data.seed)."""
    start = four_week_start(reference_today)
    events: list[HabitEvent] = []

    if periodicity == "daily":
        for offset, completed in enumerate(pattern):
            if completed:
                day = start + timedelta(days=offset)
                events.append(
                    HabitEvent(
                        habit_id=habit_id,
                        completed_at=day.replace(hour=8, minute=0),
                    )
                )
        return events

    for week_index, completed in enumerate(pattern):
        if completed:
            # Saturday of each week in the window
            day = start + timedelta(weeks=week_index, days=5)
            events.append(
                HabitEvent(
                    habit_id=habit_id,
                    completed_at=day.replace(hour=10, minute=0),
                )
            )
    return events


def build_seed_habit(
    habit_id: int,
    name: str,
    periodicity: str,
    reference_today: datetime,
) -> Habit:
    """Habit record aligned with the seed window."""
    start = four_week_start(reference_today)
    return Habit(
        id=habit_id,
        name=name,
        periodicity=periodicity,
        description=HABIT_DESCRIPTIONS[name],
        created_at=start - timedelta(days=1),
    )
