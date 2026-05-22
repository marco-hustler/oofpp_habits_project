"""Tests for the Analytics Module (functional programming)."""

import pytest
from datetime import datetime, timedelta

from domain.models import Habit, HabitEvent
from data.seed_patterns import DAILY_PATTERNS, SEED_EXPECTED_STREAKS, WEEKLY_PATTERNS
from tests.fixtures import (
    SEED_REFERENCE_TODAY,
    build_seed_events,
    build_seed_habit,
)
from analytics.analytics import (
    compute_streak,
    compute_longest_streak,
    filter_by_periodicity,
    get_all_habits,
    get_longest_streak_all,
    get_struggled_habits,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_habit(name="Run", periodicity="daily", hid=1):
    return Habit(id=hid, name=name, periodicity=periodicity,
                 description="", created_at=datetime(2026, 1, 1))


def _make_events(habit: Habit, offsets: list[int], base: datetime = datetime(2026, 3, 1)) -> list[HabitEvent]:
    """Create events at base + each day offset."""
    return [
        HabitEvent(habit_id=habit.id, completed_at=base + timedelta(days=d))
        for d in offsets
    ]


# ---------------------------------------------------------------------------
# 4-week seed patterns (shared with data.seed)
# ---------------------------------------------------------------------------

class TestSeedFourWeekPatterns:
    """Streak analytics on the five predefined 4-week seed habits."""

    @pytest.mark.parametrize("name", list(DAILY_PATTERNS.keys()))
    def test_daily_seed_current_and_longest_streak(self, name: str) -> None:
        habit = build_seed_habit(1, name, "daily", SEED_REFERENCE_TODAY)
        events = build_seed_events(1, "daily", DAILY_PATTERNS[name], SEED_REFERENCE_TODAY)
        expected = SEED_EXPECTED_STREAKS[name]
        assert compute_streak(habit, events) == expected["current"]
        assert compute_longest_streak(habit, events) == expected["longest"]

    @pytest.mark.parametrize("name", list(WEEKLY_PATTERNS.keys()))
    def test_weekly_seed_current_and_longest_streak(self, name: str) -> None:
        habit = build_seed_habit(1, name, "weekly", SEED_REFERENCE_TODAY)
        events = build_seed_events(1, "weekly", WEEKLY_PATTERNS[name], SEED_REFERENCE_TODAY)
        expected = SEED_EXPECTED_STREAKS[name]
        assert compute_streak(habit, events) == expected["current"]
        assert compute_longest_streak(habit, events) == expected["longest"]

    def test_water_has_longest_streak_among_seed_habits(self) -> None:
        habits = []
        events_by_id: dict[int, list[HabitEvent]] = {}
        hid = 1
        for name in DAILY_PATTERNS:
            habits.append(build_seed_habit(hid, name, "daily", SEED_REFERENCE_TODAY))
            events_by_id[hid] = build_seed_events(
                hid, "daily", DAILY_PATTERNS[name], SEED_REFERENCE_TODAY
            )
            hid += 1
        for name in WEEKLY_PATTERNS:
            habits.append(build_seed_habit(hid, name, "weekly", SEED_REFERENCE_TODAY))
            events_by_id[hid] = build_seed_events(
                hid, "weekly", WEEKLY_PATTERNS[name], SEED_REFERENCE_TODAY
            )
            hid += 1

        result_habit, streak = get_longest_streak_all(habits, events_by_id.get)
        assert result_habit is not None
        assert result_habit.name == "Drink 2L of Water"
        assert streak == SEED_EXPECTED_STREAKS["Drink 2L of Water"]["longest"]


# ---------------------------------------------------------------------------
# get_all_habits
# ---------------------------------------------------------------------------

class TestGetAllHabits:
    def test_returns_same_list(self):
        habits = [_make_habit("A"), _make_habit("B")]
        assert get_all_habits(habits) == habits

    def test_empty(self):
        assert get_all_habits([]) == []


# ---------------------------------------------------------------------------
# filter_by_periodicity
# ---------------------------------------------------------------------------

class TestFilterByPeriodicity:
    def test_filters_daily(self):
        habits = [
            _make_habit("A", "daily"),
            _make_habit("B", "weekly"),
            _make_habit("C", "daily"),
        ]
        result = filter_by_periodicity(habits, "daily")
        assert len(result) == 2
        assert all(h.periodicity == "daily" for h in result)

    def test_filters_weekly(self):
        habits = [_make_habit("A", "daily"), _make_habit("B", "weekly")]
        assert len(filter_by_periodicity(habits, "weekly")) == 1

    def test_no_match_returns_empty(self):
        habits = [_make_habit("A", "daily")]
        assert filter_by_periodicity(habits, "weekly") == []


# ---------------------------------------------------------------------------
# compute_streak (current streak)
# ---------------------------------------------------------------------------

class TestComputeStreak:
    def test_no_events_returns_zero(self):
        h = _make_habit()
        assert compute_streak(h, []) == 0

    def test_consecutive_days(self):
        h = _make_habit()
        events = _make_events(h, [0, 1, 2, 3, 4])
        assert compute_streak(h, events) == 5

    def test_gap_resets_current_streak(self):
        h = _make_habit()
        # days 0,1 then gap, then days 4,5,6
        events = _make_events(h, [0, 1, 4, 5, 6])
        # current streak is the last consecutive run = 3
        assert compute_streak(h, events) == 3

    def test_single_event(self):
        h = _make_habit()
        events = _make_events(h, [0])
        assert compute_streak(h, events) == 1


# ---------------------------------------------------------------------------
# compute_longest_streak
# ---------------------------------------------------------------------------

class TestComputeLongestStreak:
    def test_no_events_returns_zero(self):
        h = _make_habit()
        assert compute_longest_streak(h, []) == 0

    def test_longest_is_earlier_run(self):
        h = _make_habit()
        # 4 days, gap, then 2 days
        events = _make_events(h, [0, 1, 2, 3, 6, 7])
        assert compute_longest_streak(h, events) == 4

    def test_all_consecutive(self):
        h = _make_habit()
        events = _make_events(h, list(range(10)))
        assert compute_longest_streak(h, events) == 10

    def test_weekly_habit_two_consecutive_weeks(self):
        h = _make_habit(periodicity="weekly")
        base = datetime(2026, 3, 2)   # Monday of some week
        events = [
            HabitEvent(habit_id=h.id, completed_at=base),
            HabitEvent(habit_id=h.id, completed_at=base + timedelta(weeks=1)),
            HabitEvent(habit_id=h.id, completed_at=base + timedelta(weeks=2)),
        ]
        assert compute_longest_streak(h, events) == 3

    def test_weekly_with_gap(self):
        h = _make_habit(periodicity="weekly")
        base = datetime(2026, 3, 2)
        events = [
            HabitEvent(habit_id=h.id, completed_at=base),
            # week 2 missing
            HabitEvent(habit_id=h.id, completed_at=base + timedelta(weeks=2)),
            HabitEvent(habit_id=h.id, completed_at=base + timedelta(weeks=3)),
        ]
        assert compute_longest_streak(h, events) == 2

    def test_duplicate_events_same_day_count_once(self):
        h = _make_habit()
        # two events on day 0, then day 1 – should still be streak of 2
        events = _make_events(h, [0, 0, 1])
        assert compute_longest_streak(h, events) == 2


# ---------------------------------------------------------------------------
# get_longest_streak_all
# ---------------------------------------------------------------------------

class TestGetLongestStreakAll:
    def test_returns_none_for_empty(self):
        assert get_longest_streak_all([], lambda _: []) is None

    def test_returns_habit_with_longest_streak(self):
        h1 = _make_habit("A", hid=1)
        h2 = _make_habit("B", hid=2)
        events = {
            1: _make_events(h1, [0, 1, 2]),       # streak 3
            2: _make_events(h2, [0, 1, 2, 3, 4]), # streak 5
        }
        result_habit, streak = get_longest_streak_all([h1, h2], lambda hid: events[hid])
        assert result_habit.id == 2
        assert streak == 5


# ---------------------------------------------------------------------------
# get_struggled_habits
# ---------------------------------------------------------------------------

class TestGetStruggledHabits:
    def test_no_misses_returns_empty(self):
        h = _make_habit()
        today = datetime.now()
        events = [
            HabitEvent(habit_id=h.id, completed_at=today - timedelta(days=i))
            for i in range(31)
        ]
        result = get_struggled_habits([h], lambda _: events, today - timedelta(days=30))
        assert result == []

    def test_struggled_habit_appears_in_result(self):
        h = _make_habit()
        result = get_struggled_habits(
            [h],
            lambda _: [],
            datetime.now() - timedelta(days=7),
        )
        assert len(result) == 1
        assert result[0][0].name == "Run"
        assert result[0][1] > 0

    def test_sorted_by_missed_descending(self):
        h1 = _make_habit("A", hid=1)
        h2 = _make_habit("B", hid=2)
        today = datetime.now()
        since = today - timedelta(days=6)
        events_h1 = [
            HabitEvent(habit_id=1, completed_at=since + timedelta(days=i))
            for i in range(3)
        ]
        result = get_struggled_habits(
            [h1, h2],
            lambda hid: events_h1 if hid == 1 else [],
            since,
        )
        assert result[0][0].id == 2   # h2 struggled more
