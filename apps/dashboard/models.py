from django.conf import settings
from django.db import models
from django.utils import timezone


class CompleteStudentTelemetry(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="telemetry_streams",
    )
    date = models.DateField(default=timezone.localdate)
    gpa = models.FloatField(default=3.0)
    stress_level = models.IntegerField(default=5)
    study_hours = models.FloatField(default=4.0)
    sleep_hours = models.FloatField(default=7.0)
    mood = models.CharField(
        max_length=20,
        default="neutral",
        choices=[
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("neutral", "Neutral"),
            ("anxious", "Anxious"),
            ("exhausted", "Exhausted"),
        ],
    )
    missed_assignments = models.IntegerField(default=0)
    pending_assignments = models.IntegerField(default=0)
    completed_assignments = models.IntegerField(default=0)

    class Meta:
        ordering = ["-date"]
        unique_together = (("user", "date"),)

    def __str__(self):
        return f"Telemetry {self.user.username} - {self.date}"


class PlannedStudySession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dashboard_study_sessions",
    )
    subject = models.CharField(max_length=100)
    date = models.DateField()
    time = models.TimeField()
    duration_hours = models.FloatField(default=1.0)
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ["date", "time"]

    def __str__(self):
        return f"{self.subject} - {self.date} {self.time}"


class CGPAPredictionHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cgpa_prediction_history",
    )
    previous_gpa = models.FloatField(default=3.0)
    credit_hours = models.FloatField(default=15.0)
    assignment_completion = models.FloatField(default=0.0)
    quiz_results = models.FloatField(default=0.0)
    study_hours = models.FloatField(default=4.0)
    focus_level = models.IntegerField(default=5)
    predicted_gpa = models.FloatField(default=3.0)
    subject_forecast = models.JSONField(default=list, blank=True)
    semester_forecast = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"CGPA Prediction - {self.user.username} - {self.predicted_gpa:.2f}"


class SemesterSimulationHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="semester_simulation_history",
    )
    study_hours = models.FloatField(default=4.0)
    attendance = models.FloatField(default=75.0)
    assignment_completion = models.FloatField(default=0.0)
    quiz_performance = models.FloatField(default=0.0)
    expected_gpa = models.FloatField(default=3.0)
    expected_performance = models.CharField(max_length=40, default="Stable")
    forecast_snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Semester Simulation - {self.user.username} - {self.expected_gpa:.2f}"
