from django.urls import path
from . import views # The '.' tells Django to look in the current folder
from django.contrib.auth import views as auth_views # This is the missing piece!

urlpatterns = [
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/complete/<int:pk>/', views.complete_task, name='complete_task'),
    path('tasks/delete/<int:pk>/', views.delete_task, name='delete_task'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('subtasks/', views.subtask_list, name='subtask_list'),
    path('subtasks/create/', views.subtask_create, name='subtask_create'),
    path('subtasks/edit/<int:pk>/', views.subtask_edit, name='subtask_edit'),

    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/edit/<int:pk>/', views.category_edit, name='category_edit'),

    path('priorities/', views.priority_list, name='priority_list'),
    path('priorities/create/', views.priority_create, name='priority_create'),
    path('priorities/edit/<int:pk>/', views.priority_edit, name='priority_edit'),

    path('notes/', views.note_list, name='note_list'),
    path('notes/create/', views.note_create, name='note_create'),
    path('notes/edit/<int:pk>/', views.note_edit, name='note_edit'),
    
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]