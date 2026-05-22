"""CLI — menus via questionary; wires manager and analytics together."""

from __future__ import annotations

from datetime import datetime, timedelta

import questionary

from analytics.analytics import (
    compute_longest_streak,
    filter_by_periodicity,
    get_all_habits,
    get_longest_streak_all,
    get_struggled_habits,
)
from domain.db import init_db
from domain.repository import EventRepository, HabitRepository
from habit_management.manager import HabitManager

_SEPARATOR = "-" * 52


def _header(title: str) -> None:
    print(f"\n{_SEPARATOR}")
    print(f"  {title}")
    print(_SEPARATOR)


def _fmt_habit(habit, events=None) -> str:
    streak = f"  streak: {compute_longest_streak(habit, events)}" if events is not None else ""
    return (
        f"  [{habit.id:>3}] {habit.name}  ({habit.periodicity}){streak}\n"
        f"        {habit.description or '—'}"
    )


def _view_all(manager: HabitManager) -> None:
    _header("All tracked habits")
    habits = get_all_habits(manager.list_habits())
    if not habits:
        print("  No habits found. Create one first!")
        return
    for h in habits:
        events = manager.get_events(h.id)
        print(_fmt_habit(h, events))


def _view_by_periodicity(manager: HabitManager) -> None:
    periodicity = questionary.select(
        "Select periodicity:",
        choices=["daily", "weekly"],
    ).ask()
    if periodicity is None:
        return
    _header(f"{periodicity.capitalize()} habits")
    habits = filter_by_periodicity(manager.list_habits(), periodicity)
    if not habits:
        print(f"  No {periodicity} habits found.")
        return
    for h in habits:
        events = manager.get_events(h.id)
        print(_fmt_habit(h, events))


def _create_habit(manager: HabitManager) -> None:
    _header("Create a new habit")
    name = questionary.text("Habit name:").ask()
    if not name or not name.strip():
        print("  Habit name cannot be empty.")
        return
    periodicity = questionary.select(
        "Periodicity:",
        choices=["daily", "weekly"],
    ).ask()
    if periodicity is None:
        return
    description = questionary.text("Description (optional):").ask() or ""

    try:
        habit = manager.create_habit(name, periodicity, description)
        print(f"\n  ✓ Habit '{habit.name}' created (id={habit.id}).")
    except ValueError as exc:
        print(f"  Error: {exc}")


def _edit_habit(manager: HabitManager) -> None:
    habits = manager.list_habits()
    if not habits:
        print("  No habits to edit.")
        return
    _header("Edit a habit")
    choices = [
        questionary.Choice(title=f"[{h.id}] {h.name} ({h.periodicity})", value=h.id)
        for h in habits
    ]
    habit_id = questionary.select("Select habit to edit:", choices=choices).ask()
    if habit_id is None:
        return
    habit = manager.get_habit(habit_id)
    name = questionary.text("Habit name:", default=habit.name).ask()
    if not name or not name.strip():
        print("  Habit name cannot be empty.")
        return
    periodicity = questionary.select(
        "Periodicity:",
        choices=["daily", "weekly"],
        default=habit.periodicity,
    ).ask()
    if periodicity is None:
        return
    description = questionary.text(
        "Description (optional):",
        default=habit.description or "",
    ).ask() or ""

    try:
        updated = manager.update_habit(habit_id, name, periodicity, description)
        print(f"\n  ✓ Habit '{updated.name}' updated (id={updated.id}).")
    except ValueError as exc:
        print(f"  Error: {exc}")


def _complete_habit(manager: HabitManager) -> None:
    habits = manager.list_habits()
    if not habits:
        print("  No habits to complete. Create one first!")
        return
    _header("Complete a habit (check-off)")
    choices = [
        questionary.Choice(title=f"[{h.id}] {h.name} ({h.periodicity})", value=h.id)
        for h in habits
    ]
    habit_id = questionary.select("Select habit to check off:", choices=choices).ask()
    if habit_id is None:
        return
    event = manager.complete_habit(habit_id)
    habit = manager.get_habit(habit_id)
    print(f"\n  ✓ '{habit.name}' checked off at {event.completed_at.strftime('%Y-%m-%d %H:%M')}.")


def _delete_habit(manager: HabitManager) -> None:
    habits = manager.list_habits()
    if not habits:
        print("  No habits to delete.")
        return
    _header("Delete a habit")
    choices = [
        questionary.Choice(title=f"[{h.id}] {h.name} ({h.periodicity})", value=h.id)
        for h in habits
    ]
    habit_id = questionary.select("Select habit to delete:", choices=choices).ask()
    if habit_id is None:
        return
    habit = manager.get_habit(habit_id)
    confirmed = questionary.confirm(
        f"Delete '{habit.name}' and all its events? This cannot be undone."
    ).ask()
    if confirmed:
        manager.delete_habit(habit_id)
        print(f"\n  ✓ Habit '{habit.name}' deleted.")
    else:
        print("  Deletion cancelled.")


def _analytics_menu(manager: HabitManager) -> None:
    action = questionary.select(
        "Analytics – choose an option:",
        choices=[
            questionary.Choice("Longest streak across ALL habits", value="all"),
            questionary.Choice("Longest streak for a SPECIFIC habit", value="one"),
            questionary.Choice("Habits struggled most (last 30 days)", value="struggled"),
            questionary.Choice("← Back", value="back"),
        ],
    ).ask()

    if action == "back" or action is None:
        return

    habits = manager.list_habits()

    if action == "all":
        _header("Longest streak – all habits")
        result = get_longest_streak_all(habits, manager.get_events)
        if result is None:
            print("  No habits found.")
        else:
            habit, streak = result
            print(f"  {habit.name}  →  {streak} {habit.periodicity} period(s) in a row")

    elif action == "one":
        if not habits:
            print("  No habits found.")
            return
        choices = [
            questionary.Choice(title=f"[{h.id}] {h.name} ({h.periodicity})", value=h)
            for h in habits
        ]
        habit = questionary.select("Select habit:", choices=choices).ask()
        if habit is None:
            return
        events = manager.get_events(habit.id)
        streak = compute_longest_streak(habit, events)
        _header(f"Longest streak – {habit.name}")
        print(f"  All-time best: {streak} {habit.periodicity} period(s) in a row")
        print(f"  Total check-offs recorded: {len(events)}")

    elif action == "struggled":
        _header("Most struggled habits (last 30 days)")
        since = datetime.now() - timedelta(days=30)
        results = get_struggled_habits(habits, manager.get_events, since)
        if not results:
            print("  Great job! No missed periods in the last 30 days.")
        else:
            for habit, missed in results:
                print(f"  {habit.name} ({habit.periodicity})  →  {missed} missed period(s)")


_MENU_CHOICES = [
    questionary.Choice("View all habits", value="view_all"),
    questionary.Choice("View habits by periodicity", value="by_period"),
    questionary.Choice("Create a new habit", value="create"),
    questionary.Choice("Edit a habit", value="edit"),
    questionary.Choice("Complete a habit (check-off)", value="complete"),
    questionary.Choice("Delete a habit", value="delete"),
    questionary.Choice("Analytics", value="analytics"),
    questionary.Choice("Exit", value="exit"),
]


def main() -> None:
    """Open DB and run the menu loop."""
    conn = init_db()
    habit_repo = HabitRepository(conn)
    event_repo = EventRepository(conn)
    manager = HabitManager(habit_repo, event_repo)

    print("\n╔══════════════════════════════════════╗")
    print("║         HABIT TRACKER  v1.0          ║")
    print("╚══════════════════════════════════════╝")

    while True:
        action = questionary.select(
            "\nWhat would you like to do?",
            choices=_MENU_CHOICES,
        ).ask()

        if action is None or action == "exit":
            print("\n  Goodbye!\n")
            break
        elif action == "view_all":
            _view_all(manager)
        elif action == "by_period":
            _view_by_periodicity(manager)
        elif action == "create":
            _create_habit(manager)
        elif action == "edit":
            _edit_habit(manager)
        elif action == "complete":
            _complete_habit(manager)
        elif action == "delete":
            _delete_habit(manager)
        elif action == "analytics":
            _analytics_menu(manager)


if __name__ == "__main__":
    main()
