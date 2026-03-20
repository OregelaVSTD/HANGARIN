from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Category, Priority, Task, SubTask, Note

# --- 1. SOCIAL ACCOUNTS INTEGRATION ---
try:
    from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
    from allauth.socialaccount.admin import SocialAccountAdmin, SocialAppAdmin, SocialTokenAdmin

    # Unregister default ones
    admin.site.unregister(SocialAccount)
    admin.site.unregister(SocialApp)
    admin.site.unregister(SocialToken)

    # Re-register with Unfold styling
    @admin.register(SocialAccount)
    class UnfoldSocialAccountAdmin(SocialAccountAdmin, ModelAdmin):
        pass

    @admin.register(SocialApp)
    class UnfoldSocialAppAdmin(SocialAppAdmin, ModelAdmin):
        pass

    @admin.register(SocialToken)
    class UnfoldSocialTokenAdmin(SocialTokenAdmin, ModelAdmin):
        pass
except (ImportError, admin.sites.NotRegistered):
    # This prevents errors if allauth isn't installed or registered yet
    pass


# --- 2. YOUR TASK MANAGEMENT MODELS ---

@admin.register(Task)
class TaskAdmin(ModelAdmin):
    # Requirement: Display title, status, deadline, priority, category
    list_display = ('title', 'status', 'deadline', 'priority', 'category')
    # Requirement: Add filters for status, priority, category
    list_filter = ('status', 'priority', 'category')
    # Requirement: Enable search on title and description
    search_fields = ('title', 'description')
    
    # Unfold Extras
    compressed_fields = True  
    warn_unsaved_form = True
    list_filter_sheet = True 

@admin.register(SubTask)
class SubTaskAdmin(ModelAdmin):
    # Requirement: Display title, status, and custom field parent_task_name
    list_display = ("title", "status", "parent_task_name")
    list_filter = ("status",)
    search_fields = ("title",)

    def parent_task_name(self, obj):
        return obj.parent_task.title
    parent_task_name.short_description = 'Parent Task'

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(Priority)
class PriorityAdmin(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(Note)
class NoteAdmin(ModelAdmin):
    # Requirement: Display task, content, and created_at
    list_display = ("task", "content", "created_at")
    list_filter = ("created_at",)
    search_fields = ("content",)