"""SQLite repos for habits and check-off events."""

import sqlite3
from datetime import datetime
from typing import Optional

from domain.models import Habit, HabitEvent

_DT_FORMAT = "%Y-%m-%d %H:%M:%S"


def _parse_dt(value: str) -> datetime:
    return datetime.strptime(value, _DT_FORMAT)


def _fmt_dt(dt: datetime) -> str:
    return dt.strftime(_DT_FORMAT)


class HabitRepository:
    """Read/write habits table."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, habit: Habit) -> Habit:
        """Insert when id is None, otherwise update the row."""
        if habit.id is None:
            cur = self._conn.execute(
                "INSERT INTO habits (name, periodicity, description, created_at) "
                "VALUES (?, ?, ?, ?)",
                (habit.name, habit.periodicity, habit.description, _fmt_dt(habit.created_at)),
            )
            self._conn.commit()
            habit.id = cur.lastrowid
        else:
            self._conn.execute(
                "UPDATE habits SET name=?, periodicity=?, description=?, created_at=? "
                "WHERE id=?",
                (habit.name, habit.periodicity, habit.description,
                 _fmt_dt(habit.created_at), habit.id),
            )
            self._conn.commit()
        return habit

    def delete(self, habit_id: int) -> None:
        """Delete habit; events cascade via FK."""
        self._conn.execute("DELETE FROM habits WHERE id=?", (habit_id,))
        self._conn.commit()

    def find_by_id(self, habit_id: int) -> Optional[Habit]:
        return _row_to_habit(row) if (row := self._conn.execute(
            "SELECT * FROM habits WHERE id=?", (habit_id,)
        ).fetchone()) else None

    def find_all(self) -> list[Habit]:
        rows = self._conn.execute(
            "SELECT * FROM habits ORDER BY created_at"
        ).fetchall()
        return [_row_to_habit(r) for r in rows]


class EventRepository:
    """Read/write habit_events table."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, event: HabitEvent) -> HabitEvent:
        cur = self._conn.execute(
            "INSERT INTO habit_events (habit_id, completed_at) VALUES (?, ?)",
            (event.habit_id, _fmt_dt(event.completed_at)),
        )
        self._conn.commit()
        event.id = cur.lastrowid
        return event

    def find_by_habit(self, habit_id: int) -> list[HabitEvent]:
        rows = self._conn.execute(
            "SELECT * FROM habit_events WHERE habit_id=? ORDER BY completed_at",
            (habit_id,),
        ).fetchall()
        return [_row_to_event(r) for r in rows]

    def delete_by_habit(self, habit_id: int) -> None:
        self._conn.execute(
            "DELETE FROM habit_events WHERE habit_id=?", (habit_id,)
        )
        self._conn.commit()


def _row_to_habit(row: sqlite3.Row) -> Habit:
    return Habit(
        id=row["id"],
        name=row["name"],
        periodicity=row["periodicity"],
        description=row["description"],
        created_at=_parse_dt(row["created_at"]),
    )


def _row_to_event(row: sqlite3.Row) -> HabitEvent:
    return HabitEvent(
        id=row["id"],
        habit_id=row["habit_id"],
        completed_at=_parse_dt(row["completed_at"]),
    )
