from django.urls import path
from .views import planner_home_view

urlpatterns = [
    path('hub/', planner_home_view, name='planner_hub_home'),
]