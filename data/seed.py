"""Load 5 sample habits with 4 weeks of check-offs.

    python -m data.seed
    python -m data.seed --reset
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.seed_patterns import (
    DAILY_PATTERNS,
    HABIT_DESCRIPTIONS,
    WEEKLY_PATTERNS,
    build_seed_events,
    four_week_start,
)
from domain.db import init_db
from domain.repository import HabitRepository, EventRepository
from habit_management.manager import HabitManager


def _seed(manager: HabitManager, today: datetime) -> None:
    created = four_week_start(today) - timedelta(days=1)

    for name, pattern in DAILY_PATTERNS.items():
        habit = manager.create_habit(
            name=name,
            periodicity="daily",
            description=HABIT_DESCRIPTIONS[name],
            created_at=created,
        )
        for event in build_seed_events(habit.id, "daily", pattern, today):
            manager.complete_habit(habit.id, completed_at=event.completed_at)

    for name, pattern in WEEKLY_PATTERNS.items():
        habit = manager.create_habit(
            name=name,
            periodicity="weekly",
            description=HABIT_DESCRIPTIONS[name],
            created_at=created,
        )
        for event in build_seed_events(habit.id, "weekly", pattern, today):
            manager.complete_habit(habit.id, completed_at=event.completed_at)


def main() -> None:
    reset = "--reset" in sys.argv

    conn = init_db()
    habit_repo = HabitRepository(conn)
    event_repo = EventRepository(conn)
    manager = HabitManager(habit_repo, event_repo)

    if reset:
        conn.execute("DELETE FROM habit_events")
        conn.execute("DELETE FROM habits")
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('habits','habit_events')")
        conn.commit()
        print("Database reset.")

    existing = manager.list_habits()
    if existing and not reset:
        print(f"Database already contains {len(existing)} habit(s). Use --reset to reload.")
        return

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    _seed(manager, today)

    habits = manager.list_habits()
    print(f"Seeded {len(habits)} habits successfully.")
    for h in habits:
        events = manager.get_events(h.id)
        print(f"  [{h.periodicity:6}] {h.name} — {len(events)} event(s)")


if __name__ == "__main__":
    main()
