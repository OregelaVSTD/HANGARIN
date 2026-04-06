import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from faker import Faker

from todo.models import Category, Note, Priority, SubTask, Task


DEFAULT_PRIORITIES = ("high", "medium", "low", "critical", "optional")
DEFAULT_CATEGORIES = ("Work", "School", "Personal", "Finance", "Projects")
DEFAULT_DEMO_USERNAME = "sunny"
DEFAULT_DEMO_PASSWORD = "sunny12345"


class Command(BaseCommand):
    help = (
        "Seed Hangarin with required Priority and Category records plus Faker-based "
        "Task, Note, and SubTask data."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--tasks",
            type=int,
            default=20,
            help="Number of fake tasks to create. Defaults to 20.",
        )
        parser.add_argument(
            "--username",
            type=str,
            default=DEFAULT_DEMO_USERNAME,
            help=(
                "Assign all generated tasks to a specific username. "
                "If the user does not exist, the command will create it."
            ),
        )

    def _ensure_reference_data(self):
        categories = [
            Category.objects.get_or_create(name=name)[0] for name in DEFAULT_CATEGORIES
        ]
        priorities = [
            Priority.objects.get_or_create(name=name)[0] for name in DEFAULT_PRIORITIES
        ]
        return categories, priorities

    def _resolve_users(self, username):
        user_model = get_user_model()

        if username:
            user = user_model.objects.filter(username=username).first()
            if user is None:
                user = user_model.objects.create_user(
                    username=username,
                    password=DEFAULT_DEMO_PASSWORD,
                )
                self.stdout.write(
                    self.style.WARNING(
                        f"Created user '{username}' with password '{DEFAULT_DEMO_PASSWORD}'."
                    )
                )
            return [user]

        users = list(user_model.objects.all())
        if users:
            return users

        demo_user = user_model.objects.create_user(
            username=DEFAULT_DEMO_USERNAME,
            password=DEFAULT_DEMO_PASSWORD,
        )
        self.stdout.write(
            self.style.WARNING(
                "No users were found. "
                f"Created '{DEFAULT_DEMO_USERNAME}' with password '{DEFAULT_DEMO_PASSWORD}'."
            )
        )
        return [demo_user]

    @transaction.atomic
    def handle(self, *args, **options):
        task_count = options["tasks"]
        username = options["username"].strip()

        if task_count < 1:
            raise CommandError("--tasks must be at least 1.")

        fake = Faker()
        categories, priorities = self._ensure_reference_data()
        users = self._resolve_users(username)
        status_choices = [choice for choice, _ in Task._meta.get_field("status").choices]

        created_tasks = 0
        created_subtasks = 0
        created_notes = 0

        for _ in range(task_count):
            task = Task.objects.create(
                title=fake.sentence(nb_words=5),
                description=fake.paragraph(nb_sentences=3),
                status=fake.random_element(elements=status_choices),
                deadline=timezone.make_aware(
                    fake.date_time_this_month(),
                    timezone.get_current_timezone(),
                ),
                category=random.choice(categories),
                priority=random.choice(priorities),
                user=random.choice(users),
            )
            created_tasks += 1

            for _ in range(random.randint(2, 5)):
                SubTask.objects.create(
                    parent_task=task,
                    title=fake.sentence(nb_words=3),
                    status=fake.random_element(elements=status_choices),
                )
                created_subtasks += 1

            for _ in range(random.randint(1, 3)):
                Note.objects.create(
                    task=task,
                    content=fake.paragraph(nb_sentences=2),
                )
                created_notes += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created_tasks} tasks, {created_subtasks} subtasks, "
                f"and {created_notes} notes."
            )
        )
