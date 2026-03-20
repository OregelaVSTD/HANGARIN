from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Category, Note, Priority, SubTask, Task


DEFAULT_PRIORITIES = ("high", "medium", "low", "critical", "optional")
DEFAULT_CATEGORIES = ("Work", "School", "Personal", "Finance", "Projects")

STARTER_TASKS = (
    {
        "title": "Finalize project brief",
        "description": "Review the core deliverables and align the next milestone with the team timeline.",
        "status": "In Progress",
        "category": "Projects",
        "priority": "high",
        "deadline_offset_days": 1,
        "subtasks": (
            ("Outline the deliverables", "Completed"),
            ("Confirm the next milestone date", "In Progress"),
        ),
        "notes": (
            "Keep the milestone scope realistic for the next sprint.",
        ),
    },
    {
        "title": "Submit school requirements",
        "description": "Prepare the files needed for the current submission window and double-check missing items.",
        "status": "Pending",
        "category": "School",
        "priority": "critical",
        "deadline_offset_days": -1,
        "subtasks": (
            ("Review the checklist", "Completed"),
            ("Upload the final documents", "Pending"),
        ),
        "notes": (
            "This item is intentionally overdue so the dashboard can surface deadline pressure.",
        ),
    },
    {
        "title": "Pay monthly utility bill",
        "description": "Settle the current billing cycle and record the payment confirmation.",
        "status": "Pending",
        "category": "Finance",
        "priority": "medium",
        "deadline_offset_days": 2,
        "subtasks": (
            ("Open the payment portal", "Completed"),
            ("Save the receipt reference", "Pending"),
        ),
        "notes": (
            "Use the saved receipt as backup for monthly expense tracking.",
        ),
    },
    {
        "title": "Plan weekly personal errands",
        "description": "List the important errands for the week and group them by location to save time.",
        "status": "Pending",
        "category": "Personal",
        "priority": "low",
        "deadline_offset_days": 5,
        "subtasks": (
            ("Prepare the shopping list", "Pending"),
            ("Schedule the errand route", "Pending"),
        ),
        "notes": (
            "Batching nearby errands keeps the weekend less crowded.",
        ),
    },
    {
        "title": "Archive last sprint feedback",
        "description": "Capture the key improvements from the last sprint review and mark the follow-up as done.",
        "status": "Completed",
        "category": "Work",
        "priority": "optional",
        "deadline_offset_days": -3,
        "subtasks": (
            ("Summarize the recurring feedback", "Completed"),
            ("Store the notes in the team archive", "Completed"),
        ),
        "notes": (
            "Completed starter items help the dashboard show progress immediately.",
        ),
    },
)


@transaction.atomic
def ensure_starter_tasks(user):
    if Task.objects.filter(user=user).exists():
        return False

    categories = {
        name: Category.objects.get_or_create(name=name)[0] for name in DEFAULT_CATEGORIES
    }
    priorities = {
        name: Priority.objects.get_or_create(name=name)[0]
        for name in DEFAULT_PRIORITIES
    }

    now = timezone.now()

    for config in STARTER_TASKS:
        task = Task.objects.create(
            user=user,
            title=config["title"],
            description=config["description"],
            status=config["status"],
            category=categories[config["category"]],
            priority=priorities[config["priority"]],
            deadline=now + timedelta(days=config["deadline_offset_days"]),
        )

        SubTask.objects.bulk_create(
            [
                SubTask(parent_task=task, title=title, status=status)
                for title, status in config["subtasks"]
            ]
        )
        Note.objects.bulk_create(
            [Note(task=task, content=content) for content in config["notes"]]
        )

    return True
