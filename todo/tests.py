from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from todo.models import Category, Note, Priority, SubTask, Task


class SeedHangarinCommandTests(TestCase):
    def test_seed_hangarin_creates_required_reference_and_fake_data(self):
        output = StringIO()

        call_command("seed_hangarin", "--tasks", "3", stdout=output)

        self.assertEqual(Category.objects.count(), 5)
        self.assertEqual(Priority.objects.count(), 5)
        self.assertTrue(
            get_user_model().objects.filter(username="sunny").exists()
        )
        self.assertEqual(Task.objects.count(), 3)
        self.assertGreaterEqual(SubTask.objects.count(), 6)
        self.assertGreaterEqual(Note.objects.count(), 3)

        allowed_statuses = {
            "Pending",
            "In Progress",
            "Completed",
        }
        for task in Task.objects.all():
            self.assertIn(task.status, allowed_statuses)
            self.assertTrue(timezone.is_aware(task.deadline))
            self.assertTrue(task.title)
            self.assertTrue(task.description)

        self.assertIn("Seeded 3 tasks", output.getvalue())

    def test_seed_data_alias_uses_same_command_behavior(self):
        user_model = get_user_model()
        user_model.objects.create_user(username="existing_user", password="testpass123")

        call_command("seed_data", "--tasks", "1", "--username", "existing_user")

        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(Task.objects.get().user.username, "existing_user")


class LoginPageTests(TestCase):
    def test_login_page_shows_background_login_and_google_option(self):
        response = self.client.get("/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email or Username")
        self.assertContains(response, "Continue with Google")
        self.assertNotContains(response, "Continue with GitHub")
        self.assertNotContains(response, "GOOGLE_OAUTH_CLIENT_ID")

    @override_settings(
        SOCIALACCOUNT_PROVIDERS={
            "google": {
                "SCOPE": ["profile", "email"],
                "APPS": [
                    {
                        "name": "Google",
                        "client_id": "google-client-id",
                        "secret": "google-client-secret",
                    }
                ],
            },
            "github": {
                "SCOPE": ["read:user", "user:email"],
                "APPS": [
                    {
                        "name": "GitHub",
                        "client_id": "github-client-id",
                        "secret": "github-client-secret",
                    }
                ],
            },
        }
    )
    def test_login_page_renders_only_google_button_when_configured(self):
        response = self.client.get("/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Continue with Google")
        self.assertNotContains(response, "Continue with GitHub")
        self.assertContains(response, "/accounts/google/login/")
        self.assertNotContains(response, "/accounts/github/login/")

    def test_login_accepts_email_address(self):
        user_model = get_user_model()
        user_model.objects.create_user(
            username="emailuser",
            email="emailuser@example.com",
            password="testpass123",
        )

        response = self.client.post(
            "/login/",
            {"username": "emailuser@example.com", "password": "testpass123"},
        )

        self.assertEqual(response.status_code, 302)


class StarterTaskProvisioningTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="starter_user",
            password="testpass123",
        )

    def test_dashboard_provisions_starter_tasks_for_empty_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.filter(user=self.user).count(), 5)
        self.assertContains(response, "Finalize project brief")
        self.assertContains(response, "Submit school requirements")

    def test_task_list_shows_provisioned_starter_tasks(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("task_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.filter(user=self.user).count(), 5)
        self.assertContains(response, "Plan weekly personal errands")
        self.assertContains(response, "Archive last sprint feedback")

    def test_existing_user_tasks_are_not_duplicated(self):
        category = Category.objects.create(name="Existing Category")
        priority = Priority.objects.create(name="Existing Priority")
        Task.objects.create(
            user=self.user,
            title="Existing task",
            description="Already assigned work.",
            status="Pending",
            category=category,
            priority=priority,
            deadline=timezone.now(),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.filter(user=self.user).count(), 1)
        self.assertContains(response, "Existing task")
