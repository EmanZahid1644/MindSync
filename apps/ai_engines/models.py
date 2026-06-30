from django.db import models
from django.conf import settings

class UploadedMaterial(models.Model):
    """
    Relational model storing raw parsed text strings extracted from
    PDF/TXT textbook slides and assignments uploaded by the student.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_materials'
    )
    title = models.CharField(max_length=255)
    extracted_text = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — Extracted by {self.user.username}"


class GeneratedStudyPack(models.Model):
    """
    AI-Processed output schemas derived from UploadedMaterial context text.
    Stores comprehensive summaries, concept lists, active-recall flashcards, 
    and multi-mode scenario quiz questions.
    """
    material = models.OneToOneField(
        UploadedMaterial,
        on_delete=models.CASCADE,
        related_name='study_pack'
    )
    summary = models.TextField(default="")
    key_concepts = models.TextField(default="")
    
    # Store flashcards list of dictionaries: [{"q": "...", "a": "..."}]
    flashcards = models.JSONField(default=list)
    
    # Store quiz challenges list of dictionaries: [{"type": "MCQ" | "True/False" | "Scenario" | "Mini Challenge", "question": "...", "options": [...], "correct_answer": "...", "xp_reward": 50}]
    important_questions = models.TextField(default="[]") 
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Study Pack — Mapped onto: {self.material.title}"


class QuizResult(models.Model):
    """
    Stores dynamic results of student attempts from the Quiz Challenge Arena.
    Bridges quiz outputs directly to achievement tracking and CGPA prediction indices.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_results'
    )
    material = models.ForeignKey(
        UploadedMaterial,
        on_delete=models.CASCADE,
        related_name='quiz_attempts'
    )
    score = models.IntegerField(default=0)
    accuracy = models.FloatField(default=0.0)
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    quiz_mode = models.CharField(max_length=40, default='mixed')
    performance_snapshot = models.JSONField(default=dict, blank=True)
    achievement_payload = models.JSONField(default=dict, blank=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        return f"Quiz Attempt: {self.user.username} - {self.material.title} ({self.accuracy}%)"


class AICoachConversation(models.Model):
    MODE_CHOICES = [
        ("ask_questions", "Ask Questions"),
        ("study_guidance", "Study Guidance"),
        ("productivity_tips", "Productivity Tips"),
        ("time_management", "Time Management"),
        ("academic_recommendations", "Academic Recommendations"),
        ("quick_help", "Quick Help"),
        ("instant_recommendations", "Instant Recommendations"),
        ("resource_search", "Resource Search"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_coach_conversations",
    )
    mode = models.CharField(max_length=40, choices=MODE_CHOICES, default="ask_questions")
    user_message = models.TextField(blank=True, default="")
    assistant_reply = models.TextField(default="")
    recommendations = models.JSONField(default=list, blank=True)
    personalization_snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"AI Coach - {self.user.username} - {self.mode}"