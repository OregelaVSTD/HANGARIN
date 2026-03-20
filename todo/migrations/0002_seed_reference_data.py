from django.db import migrations


DEFAULT_PRIORITIES = ("high", "medium", "low", "critical", "optional")
DEFAULT_CATEGORIES = ("Work", "School", "Personal", "Finance", "Projects")


def seed_reference_data(apps, schema_editor):
    Category = apps.get_model("todo", "Category")
    Priority = apps.get_model("todo", "Priority")

    for name in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(name=name)

    for name in DEFAULT_PRIORITIES:
        Priority.objects.get_or_create(name=name)


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ("todo", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_reference_data, noop_reverse),
    ]
