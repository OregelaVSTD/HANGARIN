from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CategoryForm, NoteForm, PriorityForm, SubTaskForm, TaskForm
from .models import Category, Note, Priority, SubTask, Task
from .services import ensure_starter_tasks


STATUS_PENDING = "Pending"
STATUS_IN_PROGRESS = "In Progress"
STATUS_COMPLETED = "Completed"
OPEN_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS)


def _social_provider_enabled(provider_id):
    provider_config = settings.SOCIALACCOUNT_PROVIDERS.get(provider_id, {})
    apps = provider_config.get("APPS")
    if apps:
        return True
    app = provider_config.get("APP")
    return bool(app)


class HangarinLoginView(LoginView):
    template_name = "registration/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["google_login_enabled"] = _social_provider_enabled("google")
        context["github_login_enabled"] = _social_provider_enabled("github")
        return context


def _task_queryset(user):
    ensure_starter_tasks(user)
    return (
        Task.objects.filter(user=user)
        .select_related("priority", "category")
        .prefetch_related("notes", "subtasks")
    )


def _decorate_tasks(task_list):
    now = timezone.now()

    for task in task_list:
        priority_name = (task.priority.name or "").lower()
        task.is_priority_alert = priority_name in {"high", "critical"}
        task.is_overdue = bool(
            task.deadline and task.status != STATUS_COMPLETED and task.deadline < now
        )
        task.preview_notes = list(task.notes.all())[:2]


@login_required
def task_list(request):
    tasks_base = _task_queryset(request.user).order_by("-created_at")
    filtered_tasks = tasks_base

    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()

    if search_query:
        filtered_tasks = filtered_tasks.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
    if status_filter:
        filtered_tasks = filtered_tasks.filter(status=status_filter)

    paginator = Paginator(filtered_tasks, 6)
    page_number = request.GET.get("page")
    tasks = paginator.get_page(page_number)
    _decorate_tasks(tasks.object_list)

    context = {
        "tasks": tasks,
        "status_options": [STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_COMPLETED],
        "summary": {
            "total": tasks_base.count(),
            "pending": tasks_base.filter(status=STATUS_PENDING).count(),
            "in_progress": tasks_base.filter(status=STATUS_IN_PROGRESS).count(),
            "completed": tasks_base.filter(status=STATUS_COMPLETED).count(),
        },
        "active_filters": {
            "q": search_query,
            "status": status_filter,
        },
    }
    return render(request, "tasks/task_list.html", context)


@login_required
def create_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            new_task = form.save(commit=False)
            new_task.user = request.user
            new_task.save()
            messages.success(request, "Task created successfully.")
            return redirect("task_list")
    else:
        form = TaskForm()

    return render(request, "create_task.html", {"form": form})


@login_required
@require_POST
def complete_task(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task.status = STATUS_COMPLETED
    task.save(update_fields=["status", "updated_at"])
    messages.success(request, f'"{task.title}" marked as completed.')
    return redirect("task_list")


@login_required
@require_POST
def delete_task(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task_title = task.title
    task.delete()
    messages.success(request, f'"{task_title}" deleted.')
    return redirect("task_list")


@login_required
def subtask_list(request):
    q = request.GET.get("q")
    subtasks = SubTask.objects.filter(parent_task__user=request.user)
    if q:
        subtasks = subtasks.filter(title__icontains=q)
    subtasks = subtasks.order_by("-created_at")
    
    paginator = Paginator(subtasks, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "tasks/subtask_list.html", {"page_obj": page_obj})


@login_required
def subtask_create(request):
    if request.method == "POST":
        form = SubTaskForm(request.POST)
        if form.is_valid():
            subtask = form.save(commit=False)
            if subtask.parent_task.user == request.user:
                subtask.save()
                messages.success(request, "Sub task created successfully.")
                return redirect("subtask_list")
            else:
                messages.error(request, "Unauthorized action.")
    else:
        form = SubTaskForm()
        # Limit parent_task choices to user's tasks
        form.fields["parent_task"].queryset = Task.objects.filter(user=request.user)
    
    return render(request, "tasks/form.html", {"form": form, "title": "Create Sub Task", "kicker": "Sub Tasks"})


@login_required
def subtask_edit(request, pk):
    subtask = get_object_or_404(SubTask, pk=pk, parent_task__user=request.user)
    if request.method == "POST":
        form = SubTaskForm(request.POST, instance=subtask)
        if form.is_valid():
            form.save()
            messages.success(request, "Sub task updated successfully.")
            return redirect("subtask_list")
    else:
        form = SubTaskForm(instance=subtask)
        form.fields["parent_task"].queryset = Task.objects.filter(user=request.user)
    
    return render(request, "tasks/form.html", {"form": form, "title": "Edit Sub Task", "kicker": "Sub Tasks"})


@login_required
def category_list(request):
    q = request.GET.get("q")
    categories = Category.objects.annotate(task_count=Count('tasks', filter=Q(tasks__user=request.user)))
    if q:
        categories = categories.filter(name__icontains=q)
    categories = categories.order_by('name')
    return render(request, "tasks/category_list.html", {"categories": categories})


@login_required
def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category created successfully.")
            return redirect("category_list")
    else:
        form = CategoryForm()
    
    return render(request, "tasks/form.html", {"form": form, "title": "Create Category", "kicker": "Categories"})


@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully.")
            return redirect("category_list")
    else:
        form = CategoryForm(instance=category)
    
    return render(request, "tasks/form.html", {"form": form, "title": "Edit Category", "kicker": "Categories"})


@login_required
def priority_list(request):
    q = request.GET.get("q")
    priorities = Priority.objects.annotate(task_count=Count('tasks', filter=Q(tasks__user=request.user)))
    if q:
        priorities = priorities.filter(name__icontains=q)
    priorities = priorities.order_by('name')
    return render(request, "tasks/priority_list.html", {"priorities": priorities})


@login_required
def priority_create(request):
    if request.method == "POST":
        form = PriorityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Priority created successfully.")
            return redirect("priority_list")
    else:
        form = PriorityForm()
    
    return render(request, "tasks/form.html", {"form": form, "title": "Create Priority", "kicker": "Priorities"})


@login_required
def priority_edit(request, pk):
    priority = get_object_or_404(Priority, pk=pk)
    if request.method == "POST":
        form = PriorityForm(request.POST, instance=priority)
        if form.is_valid():
            form.save()
            messages.success(request, "Priority updated successfully.")
            return redirect("priority_list")
    else:
        form = PriorityForm(instance=priority)
    
    return render(request, "tasks/form.html", {"form": form, "title": "Edit Priority", "kicker": "Priorities"})


@login_required
def note_list(request):
    q = request.GET.get("q")
    notes = Note.objects.filter(task__user=request.user)
    if q:
        notes = notes.filter(content__icontains=q)
    notes = notes.order_by("-created_at")
    
    paginator = Paginator(notes, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "tasks/note_list.html", {"page_obj": page_obj})


@login_required
def note_create(request):
    if request.method == "POST":
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            if note.task.user == request.user:
                note.save()
                messages.success(request, "Note created successfully.")
                return redirect("note_list")
            else:
                messages.error(request, "Unauthorized action.")
    else:
        form = NoteForm()
        form.fields["task"].queryset = Task.objects.filter(user=request.user)
    
    return render(request, "tasks/form.html", {"form": form, "title": "Create Note", "kicker": "Notes"})


@login_required
def note_edit(request, pk):
    note = get_object_or_404(Note, pk=pk, task__user=request.user)
    if request.method == "POST":
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, "Note updated successfully.")
            return redirect("note_list")
    else:
        form = NoteForm(instance=note)
        form.fields["task"].queryset = Task.objects.filter(user=request.user)
    
    return render(request, "tasks/form.html", {"form": form, "title": "Edit Note", "kicker": "Notes"})


@login_required
def dashboard(request):
    q = request.GET.get("q")
    all_tasks = _task_queryset(request.user)
    if q:
        all_tasks = all_tasks.filter(Q(title__icontains=q) | Q(description__icontains=q))
    
    today = timezone.localdate()
    total = all_tasks.count()
    completed = all_tasks.filter(status=STATUS_COMPLETED).count()
    pending = all_tasks.filter(status=STATUS_PENDING).count()
    in_progress = all_tasks.filter(status=STATUS_IN_PROGRESS).count()
    overdue = all_tasks.filter(
        status__in=OPEN_STATUSES,
        deadline__date__lt=today,
    ).count()
    due_today = all_tasks.filter(
        status__in=OPEN_STATUSES,
        deadline__date=today,
    ).count()
    completion_rate = round((completed / total) * 100) if total else 0

    urgent = list(
        all_tasks.filter(
            Q(priority__name__iexact="high") | Q(priority__name__iexact="critical"),
            status__in=OPEN_STATUSES,
        )
        .order_by("deadline", "-created_at")[:5]
    )
    upcoming = list(
        all_tasks.filter(status__in=OPEN_STATUSES, deadline__isnull=False)
        .order_by("deadline")[:5]
    )
    recent_tasks = list(all_tasks.order_by("-created_at")[:4])
    recent_notes = list(
        Note.objects.filter(task__user=request.user)
        .select_related("task")
        .order_by("-created_at")[:4]
    )
    category_breakdown = list(
        all_tasks.values("category__name")
        .annotate(total=Count("id"))
        .order_by("-total", "category__name")
    )

    max_category_total = max((item["total"] for item in category_breakdown), default=1)
    for item in category_breakdown:
        item["label"] = item["category__name"] or "Uncategorized"
        item["percentage"] = round((item["total"] / max_category_total) * 100)

    _decorate_tasks(urgent)
    _decorate_tasks(upcoming)
    _decorate_tasks(recent_tasks)

    context = {
        "total": total,
        "completed": completed,
        "pending": pending,
        "in_progress": in_progress,
        "overdue": overdue,
        "due_today": due_today,
        "completion_rate": completion_rate,
        "urgent": urgent,
        "upcoming": upcoming,
        "recent_tasks": recent_tasks,
        "recent_notes": recent_notes,
        "category_breakdown": category_breakdown,
    }
    return render(request, "dashboard.html", context)
