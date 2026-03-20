from django.urls import path
from . import views # The '.' tells Django to look in the current folder
from django.contrib.auth import views as auth_views # This is the missing piece!

urlpatterns = [
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/complete/<int:pk>/', views.complete_task, name='complete_task'),
    path('tasks/delete/<int:pk>/', views.delete_task, name='delete_task'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]