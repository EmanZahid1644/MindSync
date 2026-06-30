from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('/auth/login/', permanent=False)), 
    
    path('auth/', include('authentication.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('ai/', include('ai_engines.urls')),
    path('planner/', include('planner.urls')), # <-- DOUBLE CHECK THIS LINE EXACTLY!
]