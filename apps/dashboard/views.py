import json
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from django.utils import timezone
from django.db import connection
from django.urls import reverse
from google import genai

from .models import CGPAPredictionHistory, CompleteStudentTelemetry, PlannedStudySession, SemesterSimulationHistory
from ai_engines.models import QuizResult

logger = logging.getLogger(__name__)
User = get_user_model()


def _today_telemetry(user):
    today = timezone.localdate()
    telemetry, _ = CompleteStudentTelemetry.objects.get_or_create(
        user=user,
        date=today,
        defaults={
            "gpa": 3.0,
            "stress_level": 5,
            "study_hours": 4.0,
            "sleep_hours": 7.0,
            "mood": "neutral",
            "missed_assignments": 0,
            "pending_assignments": 0,
            "completed_assignments": 0,
        },
    )
    return telemetry


def _build_ai_context(telemetry):
    productivity_score = max(
        0,
        min(
            100,
            int(
                (telemetry.gpa / 4.0) * 35
                + min(telemetry.study_hours * 6, 30)
                + min(telemetry.completed_assignments * 4, 20)
                + min(telemetry.sleep_hours * 2, 15)
            ),
        ),
    )
    burnout_percentage = max(
        0,
        min(
            100,
            int(
                telemetry.stress_level * 8
                + max(0, 8 - telemetry.sleep_hours) * 8
                + telemetry.missed_assignments * 7
                - min(telemetry.study_hours, 8) * 2
            ),
        ),
    )
    if burnout_percentage >= 70:
        risk_level = "HIGH RISK"
    elif burnout_percentage >= 40:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW RISK"

    return {
        "productivity_score": productivity_score,
        "burnout_percentage": burnout_percentage,
        "risk_level": risk_level,
        "explanation": (
            f"Current mood is {telemetry.mood}. Stress is {telemetry.stress_level}/10, "
            f"sleep is {telemetry.sleep_hours}h, and study time is {telemetry.study_hours}h."
        ),
        "recommendations": [
            "Balance study blocks with short recovery breaks.",
            "Protect sleep to reduce burnout risk.",
            "Convert pending assignments into a prioritized checklist.",
        ],
    }


def _gamification_context(telemetry):
    xp = int(
        telemetry.completed_assignments * 20
        + telemetry.pending_assignments * 5
        + max(0, 100 - telemetry.stress_level * 5)
    )
    badges = [
        {
            "icon": "🔥",
            "title": "Momentum Starter",
            "desc": "Consistent activity unlocked the first progress milestone.",
        },
        {
            "icon": "📘",
            "title": "Study Architect",
            "desc": "Active planning sessions are being tracked and organized.",
        },
    ]
    if telemetry.completed_assignments >= 5:
        badges.append(
            {
                "icon": "🏆",
                "title": "Completion Champion",
                "desc": "High completion rate across tracked assignments.",
            }
        )
    return {"streak": 1, "xp": min(xp, 200), "badges": badges}


def _heatmap_context(sessions):
    heatmap = []
    for day in range(1, 32):
        status = "safe"
        title = "No active deadline"
        for session in sessions:
            # session is a dictionary because of .values()
            session_date = session.get("date")
            if session_date and session_date.day == day:
                status = "upcoming"
                title = f"{session.get('subject', 'Untitled Task')} scheduled"
                break
        heatmap.append({"day": day, "status": status, "title": title})
    return json.dumps(heatmap)


def _session_queryset_for_user(user):
    # Use values() to avoid selecting fields that may lag behind the database schema.
    return list(
        PlannedStudySession.objects.filter(user=user)
        .order_by("date", "time")
        .values("id", "subject", "date", "time", "duration_hours", "is_completed")
    )


def _table_has_column(table_name: str, column_name: str) -> bool:
    with connection.cursor() as cursor:
        columns = [field.name for field in connection.introspection.get_table_description(cursor, table_name)]
    return column_name in columns


def _clamp(value, minimum=0.0, maximum=4.0):
    return max(minimum, min(maximum, value))


def _quiz_average_for_user(user):
    quiz_results = QuizResult.objects.filter(user=user)
    if not quiz_results.exists():
        return 0.0
    return round(sum(result.accuracy for result in quiz_results) / quiz_results.count(), 2)


def _quiz_profile_for_user(user):
    quiz_results = list(QuizResult.objects.filter(user=user).order_by("-completed_at").values_list("accuracy", flat=True))
    if not quiz_results:
        return {
            "average": 0.0,
            "recent_average": 0.0,
            "trend": 0.0,
            "count": 0,
        }

    recent_slice = quiz_results[:5]
    older_slice = quiz_results[5:10]
    recent_average = round(sum(recent_slice) / len(recent_slice), 2)
    older_average = round(sum(older_slice) / len(older_slice), 2) if older_slice else recent_average
    return {
        "average": round(sum(quiz_results) / len(quiz_results), 2),
        "recent_average": recent_average,
        "trend": round(recent_average - older_average, 2),
        "count": len(quiz_results),
    }


def _attendance_proxy_for_user(user):
    sessions = list(PlannedStudySession.objects.filter(user=user).values("duration_hours", "is_completed"))
    if not sessions:
        return 75.0

    weighted_total = sum(max(session.get("duration_hours") or 1.0, 1.0) for session in sessions)
    completed_weight = sum(
        max(session.get("duration_hours") or 1.0, 1.0)
        for session in sessions
        if session.get("is_completed")
    )
    return round((completed_weight / weighted_total) * 100, 2) if weighted_total else 75.0


def _unique_subjects_for_user(user):
    subjects = []
    for session in PlannedStudySession.objects.filter(user=user).order_by("date", "time").values_list("subject", flat=True):
        if session and session not in subjects:
            subjects.append(session)
    return subjects[:5] or ["Core Subjects", "Project Work", "Assessments"]


def _subject_difficulty_map_for_user(user):
    difficulty_map = {}
    sessions = PlannedStudySession.objects.filter(user=user).values("subject", "duration_hours", "is_completed")
    for session in sessions:
        subject = session.get("subject") or "General Studies"
        duration = float(session.get("duration_hours") or 1.0)
        completed = bool(session.get("is_completed"))
        entry = difficulty_map.setdefault(subject, {"load": 0.0, "completion_count": 0, "total_count": 0})
        entry["load"] += duration
        entry["total_count"] += 1
        if completed:
            entry["completion_count"] += 1
    return difficulty_map


def _build_subject_forecast(base_gpa, study_hours, focus_level, subjects, difficulty_map, quiz_trend, attendance_proxy):
    forecast = []
    for index, subject in enumerate(subjects):
        subject_meta = difficulty_map.get(subject, {"load": 1.0, "completion_count": 0, "total_count": 0})
        workload_penalty = min(subject_meta["load"] / 30.0, 0.28)
        completion_bonus = 0.0
        if subject_meta["total_count"]:
            completion_bonus = (subject_meta["completion_count"] / subject_meta["total_count"]) * 0.12
        subject_adjustment = (
            (focus_level - 5) * 0.05
            + (study_hours - 4) * 0.04
            + (attendance_proxy - 75) / 1000.0
            + quiz_trend / 200.0
            + completion_bonus
            - workload_penalty
            - index * 0.02
        )
        forecast.append({
            "subject": subject,
            "projected_gpa": round(_clamp(base_gpa + subject_adjustment), 2),
            "confidence": max(
                55,
                min(
                    96,
                    int(
                        58
                        + focus_level * 3
                        + study_hours * 2
                        + completion_bonus * 100
                        + max(0, quiz_trend)
                        - workload_penalty * 50
                        - index * 4
                    ),
                ),
            ),
        })
    return forecast


def _build_semester_phase_forecast(predicted_gpa, attendance, quiz_performance, study_hours):
    momentum = (attendance / 100.0) * 0.4 + (quiz_performance / 100.0) * 0.35 + (study_hours / 10.0) * 0.15
    return [
        {
            "phase": "Month 1",
            "forecast_gpa": round(_clamp(predicted_gpa - 0.15 + momentum * 0.4), 2),
        },
        {
            "phase": "Mid-Semester",
            "forecast_gpa": round(_clamp(predicted_gpa + momentum * 0.2), 2),
        },
        {
            "phase": "Finals",
            "forecast_gpa": round(_clamp(predicted_gpa + momentum * 0.3 + 0.08), 2),
        },
    ]


def _build_prediction_result(user, previous_gpa, credit_hours, assignment_completion, quiz_results, study_hours, focus_level):
    quiz_profile = _quiz_profile_for_user(user)
    attendance_proxy = _attendance_proxy_for_user(user)
    difficulty_map = _subject_difficulty_map_for_user(user)
    quiz_trend = quiz_profile["trend"]
    score = (
        previous_gpa * 0.35
        + (assignment_completion / 100.0) * 1.0
        + (quiz_results / 100.0) * 1.25
        + (quiz_profile["recent_average"] / 100.0) * 0.35
        + (attendance_proxy / 100.0) * 0.65
        + (study_hours / 10.0) * 0.9
        + (focus_level / 10.0) * 0.85
        - (credit_hours / 24.0) * 0.5
        + max(-0.12, min(0.12, quiz_trend / 200.0))
    )
    predicted_gpa = round(_clamp(score, 0.0, 4.0), 2)
    subjects = _unique_subjects_for_user(user)
    subject_forecast = _build_subject_forecast(predicted_gpa, study_hours, focus_level, subjects, difficulty_map, quiz_trend, attendance_proxy)
    semester_forecast = {
        "predicted_gpa": predicted_gpa,
        "confidence_band": "strong" if predicted_gpa >= 3.5 else "stable" if predicted_gpa >= 2.8 else "needs_attention",
        "phases": _build_semester_phase_forecast(predicted_gpa, attendance_proxy, max(quiz_results, quiz_profile["recent_average"]), study_hours),
        "attendance_proxy": attendance_proxy,
        "quiz_trend": quiz_trend,
    }
    return predicted_gpa, subject_forecast, semester_forecast


def _build_simulation_result(study_hours, attendance, assignment_completion, quiz_performance):
    expected_gpa = round(
        _clamp(
            1.2
            + (study_hours / 10.0) * 1.1
            + (attendance / 100.0) * 1.1
            + (assignment_completion / 100.0) * 1.0
            + (quiz_performance / 100.0) * 1.2,
            0.0,
            4.0,
        ),
        2,
    )
    if expected_gpa >= 3.6:
        expected_performance = "Excellent"
    elif expected_gpa >= 3.0:
        expected_performance = "Strong"
    elif expected_gpa >= 2.2:
        expected_performance = "Stable"
    else:
        expected_performance = "At Risk"

    return expected_gpa, expected_performance, {
        "expected_gpa": expected_gpa,
        "expected_performance": expected_performance,
        "inputs": {
            "study_hours": study_hours,
            "attendance": attendance,
            "assignment_completion": assignment_completion,
            "quiz_performance": quiz_performance,
        },
        "recommendations": [
            "Increase focus on weaker subjects.",
            "Keep attendance above 80% for stability.",
            "Convert quiz misses into weekly review sessions.",
        ],
    }


def _burnout_percentage_for_telemetry(telemetry):
    return max(
        0,
        min(
            100,
            int(
                telemetry.stress_level * 8
                + max(0, 8 - telemetry.sleep_hours) * 8
                + telemetry.missed_assignments * 7
                - min(telemetry.study_hours, 8) * 2
            ),
        ),
    )


def _assignment_completion_percentage(telemetry):
    total = telemetry.completed_assignments + telemetry.pending_assignments + telemetry.missed_assignments
    if total <= 0:
        return 0.0
    return round((telemetry.completed_assignments / total) * 100, 2)


def _teacher_student_row(student):
    telemetry = CompleteStudentTelemetry.objects.filter(user=student).order_by("-date").first()
    latest_prediction = CGPAPredictionHistory.objects.filter(user=student).order_by("-created_at").first()
    quizzes = list(QuizResult.objects.filter(user=student).values_list("accuracy", flat=True))
    quiz_avg = round(sum(quizzes) / len(quizzes), 2) if quizzes else 0.0

    if telemetry:
        burnout_percentage = _burnout_percentage_for_telemetry(telemetry)
        current_gpa = round(float(telemetry.gpa), 2)
        completion_percentage = _assignment_completion_percentage(telemetry)
    else:
        burnout_percentage = 0
        current_gpa = 0.0
        completion_percentage = 0.0

    predicted_gpa = round(float(latest_prediction.predicted_gpa), 2) if latest_prediction else current_gpa
    gpa_drop = round(current_gpa - predicted_gpa, 2)

    risk_reasons = []
    if burnout_percentage >= 70:
        risk_reasons.append("High Burnout Risk")
    if gpa_drop >= 0.4:
        risk_reasons.append("Falling GPA Trend")
    if completion_percentage < 55:
        risk_reasons.append("Low Assignment Completion")

    return {
        "student": student,
        "current_gpa": current_gpa,
        "predicted_gpa": predicted_gpa,
        "gpa_drop": gpa_drop,
        "burnout_percentage": burnout_percentage,
        "assignment_completion": completion_percentage,
        "quiz_average": quiz_avg,
        "at_risk": bool(risk_reasons),
        "risk_reasons": risk_reasons,
    }


@login_required
def teacher_dashboard_view(request):
    if not request.user.is_teacher:
        return redirect("platform_home")

    students = User.objects.filter(is_student=True).order_by("username")
    student_rows = [_teacher_student_row(student) for student in students]

    at_risk_alerts = []
    for row in student_rows:
        for reason in row["risk_reasons"]:
            at_risk_alerts.append(
                {
                    "student": row["student"],
                    "reason": reason,
                    "burnout_percentage": row["burnout_percentage"],
                    "current_gpa": row["current_gpa"],
                    "predicted_gpa": row["predicted_gpa"],
                    "assignment_completion": row["assignment_completion"],
                }
            )

    total_students = len(student_rows)
    avg_burnout = round(sum(row["burnout_percentage"] for row in student_rows) / total_students, 2) if total_students else 0.0
    avg_quiz = round(sum(row["quiz_average"] for row in student_rows) / total_students, 2) if total_students else 0.0
    avg_forecast = round(sum(row["predicted_gpa"] for row in student_rows) / total_students, 2) if total_students else 0.0

    context = {
        "student_rows": student_rows,
        "at_risk_alerts": at_risk_alerts[:30],
        "summary": {
            "total_students": total_students,
            "at_risk_count": sum(1 for row in student_rows if row["at_risk"]),
            "avg_burnout": avg_burnout,
            "avg_quiz": avg_quiz,
            "avg_forecast": avg_forecast,
        },
    }
    return render(request, "dashboard/teacher_hub.html", context)


@login_required
def unified_dashboard_view(request):
    if request.user.is_teacher:
        return teacher_dashboard_view(request)

    telemetry = _today_telemetry(request.user)
    sessions = _session_queryset_for_user(request.user)
    quiz_history = list(
        QuizResult.objects.filter(user=request.user)
        .select_related("material")
        .order_by("-completed_at")[:6]
    )
    quiz_summary = {
        "attempts": len(quiz_history),
        "best_score": max((item.score for item in quiz_history), default=0),
        "avg_accuracy": round(sum(item.accuracy for item in quiz_history) / len(quiz_history), 2) if quiz_history else 0,
    }
    default_focus_level = max(1, 10 - telemetry.stress_level)
    default_assignment_completion = min(100, telemetry.completed_assignments * 10)
    prediction_history = list(CGPAPredictionHistory.objects.filter(user=request.user).order_by("-created_at")[:5])
    simulation_history = list(SemesterSimulationHistory.objects.filter(user=request.user).order_by("-created_at")[:5])
    context = {
        "log": telemetry,
        "ai": _build_ai_context(telemetry),
        "sessions": sessions,
        "gamification": _gamification_context(telemetry),
        "heatmap_data": _heatmap_context(sessions),
        "quiz_history": quiz_history,
        "quiz_summary": quiz_summary,
        "prediction_history": prediction_history,
        "simulation_history": simulation_history,
        "latest_prediction": prediction_history[0] if prediction_history else None,
        "latest_simulation": simulation_history[0] if simulation_history else None,
        "default_focus_level": default_focus_level,
        "default_assignment_completion": default_assignment_completion,
    }
    return render(request, "dashboard/student_hub.html", context)


@login_required
def predict_cgpa_view(request):
    if request.method != "POST":
        return redirect("platform_home")

    telemetry = _today_telemetry(request.user)
    previous_gpa = float(request.POST.get("previous_gpa", telemetry.gpa) or telemetry.gpa)
    credit_hours = float(request.POST.get("credit_hours", 15) or 15)
    assignment_completion = float(request.POST.get("assignment_completion", telemetry.completed_assignments * 10) or 0)
    quiz_results = float(request.POST.get("quiz_results", _quiz_average_for_user(request.user)) or 0)
    study_hours = float(request.POST.get("study_hours", telemetry.study_hours) or telemetry.study_hours)
    focus_level = int(request.POST.get("focus_level", max(1, 10 - telemetry.stress_level)) or max(1, 10 - telemetry.stress_level))

    predicted_gpa, subject_forecast, semester_forecast = _build_prediction_result(
        request.user,
        previous_gpa,
        credit_hours,
        assignment_completion,
        quiz_results,
        study_hours,
        focus_level,
    )

    CGPAPredictionHistory.objects.create(
        user=request.user,
        previous_gpa=previous_gpa,
        credit_hours=credit_hours,
        assignment_completion=assignment_completion,
        quiz_results=quiz_results,
        study_hours=study_hours,
        focus_level=focus_level,
        predicted_gpa=predicted_gpa,
        subject_forecast=subject_forecast,
        semester_forecast=semester_forecast,
    )

    messages.success(request, f"CGPA forecast saved. Predicted GPA: {predicted_gpa}")
    return redirect(f"{reverse('platform_home')}?prediction_saved=1")


@login_required
def simulate_semester_view(request):
    if request.method != "POST":
        return redirect("platform_home")

    study_hours = float(request.POST.get("sim_study_hours", 4.0) or 4.0)
    attendance = float(request.POST.get("attendance", 75.0) or 75.0)
    assignment_completion = float(request.POST.get("sim_assignment_completion", 50.0) or 50.0)
    quiz_performance = float(request.POST.get("sim_quiz_performance", 50.0) or 50.0)

    expected_gpa, expected_performance, forecast_snapshot = _build_simulation_result(
        study_hours,
        attendance,
        assignment_completion,
        quiz_performance,
    )

    SemesterSimulationHistory.objects.create(
        user=request.user,
        study_hours=study_hours,
        attendance=attendance,
        assignment_completion=assignment_completion,
        quiz_performance=quiz_performance,
        expected_gpa=expected_gpa,
        expected_performance=expected_performance,
        forecast_snapshot=forecast_snapshot,
    )

    messages.success(request, f"Semester simulation saved. Expected GPA: {expected_gpa}")
    return redirect(f"{reverse('platform_home')}?simulation_saved=1")


@login_required
def log_telemetry_view(request):
    if request.method != "POST":
        return redirect("platform_home")

    telemetry = _today_telemetry(request.user)
    telemetry.gpa = float(request.POST.get("gpa", telemetry.gpa) or telemetry.gpa)
    telemetry.mood = request.POST.get("mood", telemetry.mood) or telemetry.mood
    telemetry.stress_level = int(request.POST.get("stress_level", telemetry.stress_level) or telemetry.stress_level)
    telemetry.study_hours = float(request.POST.get("study_hours", telemetry.study_hours) or telemetry.study_hours)
    telemetry.sleep_hours = float(request.POST.get("sleep_hours", telemetry.sleep_hours) or telemetry.sleep_hours)
    telemetry.completed_assignments = int(request.POST.get("completed_assignments", telemetry.completed_assignments) or telemetry.completed_assignments)
    telemetry.pending_assignments = int(request.POST.get("pending_assignments", telemetry.pending_assignments) or telemetry.pending_assignments)
    telemetry.missed_assignments = int(request.POST.get("missed_assignments", telemetry.missed_assignments) or telemetry.missed_assignments)
    telemetry.save()

    messages.success(request, "Telemetry updated.")
    return redirect("platform_home")


@login_required
def create_task_view(request):
    if request.method != "POST":
        return redirect("platform_home")

    subject = (request.POST.get("title") or request.POST.get("subject") or "Untitled Task").strip()
    date_value = request.POST.get("due_date") or request.POST.get("date")
    time_value = request.POST.get("time") or "09:00"
    duration_value = request.POST.get("duration") or 1.0

    if not date_value:
        messages.error(request, "A date is required to add a task.")
        return redirect("platform_home")

    # Check dynamically if 'is_completed' column exists to avoid integrity errors
    has_is_completed = _table_has_column("dashboard_plannedstudysession", "is_completed")

    with connection.cursor() as cursor:
        if has_is_completed:
            cursor.execute(
                "INSERT INTO dashboard_plannedstudysession (user_id, subject, date, time, duration_hours, is_completed) VALUES (%s, %s, %s, %s, %s, %s)",
                [request.user.id, subject, date_value, time_value, duration_value, False],
            )
        else:
            cursor.execute(
                "INSERT INTO dashboard_plannedstudysession (user_id, subject, date, time, duration_hours) VALUES (%s, %s, %s, %s, %s)",
                [request.user.id, subject, date_value, time_value, duration_value],
            )

    messages.success(request, "Task added.")
    return redirect("platform_home")


@login_required
def complete_task_view(request, task_id):
    if request.method not in {"POST", "GET"}:
        return redirect("platform_home")

    if _table_has_column("dashboard_plannedstudysession", "is_completed"):
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE dashboard_plannedstudysession SET is_completed = TRUE WHERE id = %s AND user_id = %s",
                [task_id, request.user.id],
            )
        messages.success(request, "Task completed.")
    else:
        messages.warning(request, "Task completion is unavailable until the database column is migrated.")

    return redirect("platform_home")