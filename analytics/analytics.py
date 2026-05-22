"""Analytics — pure functions, filter/map/reduce where it fits."""

from __future__ import annotations

import functools
from datetime import datetime, date, timedelta
from typing import Callable

from domain.models import Habit, HabitEvent


def get_all_habits(habits: list[Habit]) -> list[Habit]:
    """Return every habit (portfolio API)."""
    return list(habits)


def filter_by_periodicity(habits: list[Habit], periodicity: str) -> list[Habit]:
    """Keep only daily or weekly habits."""
    return list(filter(lambda h: h.periodicity == periodicity, habits))


def _completed_periods(habit: Habit, events: list[HabitEvent]) -> list[tuple[int, int]]:
    """Map events to sorted (year, period) tuples — day-of-year or ISO week."""
    def _to_period(event: HabitEvent) -> tuple[int, int]:
        d: date = event.completed_at.date()
        if habit.periodicity == "daily":
            return (d.year, d.timetuple().tm_yday)
        iso = d.isocalendar()
        return (iso.year, iso.week)

    periods = list(map(_to_period, events))
    return sorted(set(periods))


def _are_consecutive(periodicity: str, p1: tuple[int, int], p2: tuple[int, int]) -> bool:
    """True if p2 is the next day or next week after p1."""
    if periodicity == "daily":
        d1 = date(p1[0], 1, 1) + timedelta(days=p1[1] - 1)
        d2 = date(p2[0], 1, 1) + timedelta(days=p2[1] - 1)
        return (d2 - d1).days == 1
    d1 = _iso_week_to_date(p1[0], p1[1])
    d2 = _iso_week_to_date(p2[0], p2[1])
    return (d2 - d1).days == 7


def _iso_week_to_date(year: int, week: int) -> date:
    """Monday of the given ISO year/week."""
    return datetime.strptime(f"{year} {week} 1", "%G %V %u").date()


def _streak_lengths(periods: list[tuple[int, int]], periodicity: str) -> list[int]:
    """Length of each consecutive run in the period list."""
    if not periods:
        return []

    def _reducer(acc: list[int], pair: tuple[tuple[int, int], tuple[int, int]]) -> list[int]:
        prev, curr = pair
        if _are_consecutive(periodicity, prev, curr):
            acc[-1] += 1
        else:
            acc.append(1)
        return acc

    pairs = list(zip(periods[:-1], periods[1:]))
    return functools.reduce(_reducer, pairs, [1])


def compute_streak(habit: Habit, events: list[HabitEvent]) -> int:
    """Current streak ending at the most recent check-off."""
    periods = _completed_periods(habit, events)
    streaks = _streak_lengths(periods, habit.periodicity)
    return streaks[-1] if streaks else 0


def compute_longest_streak(habit: Habit, events: list[HabitEvent]) -> int:
    """Best streak ever for this habit."""
    periods = _completed_periods(habit, events)
    streaks = _streak_lengths(periods, habit.periodicity)
    return max(streaks, default=0)


def get_longest_streak_all(
    habits: list[Habit],
    get_events: Callable[[int], list[HabitEvent]],
) -> tuple[Habit, int] | None:
    """Habit with the highest all-time streak, or None if empty."""
    if not habits:
        return None

    def _habit_streak(habit: Habit) -> tuple[Habit, int]:
        return (habit, compute_longest_streak(habit, get_events(habit.id)))

    scored = list(map(_habit_streak, habits))
    return max(scored, key=lambda x: x[1])


def get_struggled_habits(
    habits: list[Habit],
    get_events: Callable[[int], list[HabitEvent]],
    since: datetime,
) -> list[tuple[Habit, int]]:
    """Habits with the most missed periods since `since`, worst first."""
    today = datetime.now().date()
    since_date = since.date()

    def _missed(habit: Habit) -> int:
        events = get_events(habit.id)
        completed = set(_completed_periods(habit, events))

        if habit.periodicity == "daily":
            total_periods = {
                (d.year, d.timetuple().tm_yday)
                for d in _date_range(since_date, today)
            }
        else:
            total_periods = {
                (d.isocalendar().year, d.isocalendar().week)
                for d in _date_range(since_date, today)
            }

        return len(total_periods - completed)

    scored = [(habit, _missed(habit)) for habit in habits]
    filtered = list(filter(lambda x: x[1] > 0, scored))
    return sorted(filtered, key=lambda x: x[1], reverse=True)


def _date_range(start: date, end: date) -> list[date]:
    """Every calendar day from start through end."""
    delta = (end - start).days
    return [start + timedelta(days=i) for i in range(delta + 1)]
