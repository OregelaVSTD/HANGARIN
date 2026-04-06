from django.contrib import admin
from django.urls import path, include # <--- Make sure 'path' and 'include' are here
from django.shortcuts import redirect

from todo.views import HangarinLoginView

urlpatterns = [
    path('', lambda request: redirect('login')),
    path('admin/', admin.site.urls),
    path('login/', HangarinLoginView.as_view(), name='login'),
    path('accounts/', include('allauth.urls')),
    path('', include('todo.urls')),
    path('', include('pwa.urls')),
]
