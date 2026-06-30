from django.contrib import admin

from .models import CGPAPredictionHistory, CompleteStudentTelemetry, PlannedStudySession, SemesterSimulationHistory


@admin.register(CompleteStudentTelemetry)
class CompleteStudentTelemetryAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "gpa", "stress_level", "study_hours", "completed_assignments")
    list_select_related = ("user",)


@admin.register(PlannedStudySession)
class PlannedStudySessionAdmin(admin.ModelAdmin):
    list_display = ("user", "subject", "date", "time", "duration_hours", "is_completed")
    list_select_related = ("user",)


@admin.register(CGPAPredictionHistory)
class CGPAPredictionHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "previous_gpa", "predicted_gpa", "credit_hours", "study_hours", "focus_level", "created_at")
    list_select_related = ("user",)


@admin.register(SemesterSimulationHistory)
class SemesterSimulationHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "study_hours", "attendance", "assignment_completion", "quiz_performance", "expected_gpa", "created_at")
    list_select_related = ("user",)
