from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.unified_dashboard_view, name='platform_home'),
    path('teacher/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('log-metrics/', views.log_telemetry_view, name='log_telemetry'),
    path('add-task/', views.create_task_view, name='create_task'),
    path('complete-task/<int:task_id>/', views.complete_task_view, name='complete_task'),
    path('predict-cgpa/', views.predict_cgpa_view, name='predict_cgpa'),
    path('simulate-semester/', views.simulate_semester_view, name='simulate_semester'),
]