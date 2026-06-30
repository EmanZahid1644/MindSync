from django.contrib import admin

from .models import AICoachConversation, GeneratedStudyPack, QuizResult, UploadedMaterial


@admin.register(UploadedMaterial)
class UploadedMaterialAdmin(admin.ModelAdmin):
	list_display = ("title", "user", "created_at")
	search_fields = ("title", "user__username")
	list_filter = ("created_at",)


@admin.register(GeneratedStudyPack)
class GeneratedStudyPackAdmin(admin.ModelAdmin):
	list_display = ("material", "created_at")
	search_fields = ("material__title", "material__user__username")
	list_filter = ("created_at",)


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
	list_display = ("user", "material", "score", "accuracy", "quiz_mode", "completed_at")
	search_fields = ("user__username", "material__title", "quiz_mode")
	list_filter = ("quiz_mode", "completed_at")


@admin.register(AICoachConversation)
class AICoachConversationAdmin(admin.ModelAdmin):
	list_display = ("user", "mode", "created_at")
	search_fields = ("user__username", "mode", "user_message", "assistant_reply")
	list_filter = ("mode", "created_at")
