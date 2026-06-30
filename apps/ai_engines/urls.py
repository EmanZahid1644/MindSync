from django.urls import path
from . import views

urlpatterns = [
    path('notes/', views.upload_notes_page_view, name='notes_generator_home'),
    path('notes/upload/', views.process_file_upload_view, name='trigger_file_upload'),
    path('quiz/save/', views.save_quiz_result_view, name='save_quiz_result'),
    path('coach/', views.ai_coach_home_view, name='ai_coach_home'),
    path('coach/chat/', views.ai_coach_chat_view, name='ai_coach_chat'),
    path('coach/recommendations/', views.ai_coach_instant_recommendations_view, name='ai_coach_recommendations'),
    
    # New Action Route Endpoint mapping dynamic numerical database tracking variables
    path('notes/generate/<int:material_id>/', views.generate_ai_study_pack_view, name='trigger_ai_generation'),
]