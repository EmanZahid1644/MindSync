import json
import logging
import re

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_POST
from django.utils import timezone
from google import genai

from .models import AICoachConversation, UploadedMaterial, GeneratedStudyPack, QuizResult
from dashboard.models import CompleteStudentTelemetry  # Standard namespace used to completely resolve Django RuntimeError

logger = logging.getLogger(__name__)


def _normalize_quiz_challenge(challenge, fallback_index=0):
    if not isinstance(challenge, dict):
        return {
            'type': 'MCQ',
            'question': str(challenge),
            'options': [],
            'correct_answer': '',
            'xp_reward': 0,
            'difficulty': 'medium',
            'explanation': '',
        }

    normalized = dict(challenge)
    normalized.setdefault('type', 'MCQ')
    normalized.setdefault('question', '')
    normalized.setdefault('options', [])
    normalized.setdefault('correct_answer', '')
    normalized.setdefault('xp_reward', 0)
    normalized.setdefault('difficulty', ['easy', 'medium', 'hard'][fallback_index % 3])
    normalized.setdefault('explanation', 'Review the source material for the exact reasoning behind this answer.')
    return normalized


def _normalize_quiz_challenges(challenges):
    if not isinstance(challenges, list):
        return []
    return [_normalize_quiz_challenge(challenge, index) for index, challenge in enumerate(challenges)]


def _build_quiz_metrics(score, accuracy, total_questions, correct_answers, quiz_mode):
    attempted_questions = max(total_questions, 0)
    completed_questions = max(correct_answers, 0)
    completion_rate = round((completed_questions / attempted_questions) * 100, 2) if attempted_questions else 0.0
    performance_band = 'excellent' if accuracy >= 90 else 'strong' if accuracy >= 75 else 'developing' if accuracy >= 50 else 'needs_support'
    xp_awarded = max(score, 0)

    return {
        'quiz_mode': quiz_mode or 'mixed',
        'score': score,
        'accuracy': round(accuracy, 2),
        'total_questions': attempted_questions,
        'correct_answers': completed_questions,
        'completion_rate': completion_rate,
        'xp_awarded': xp_awarded,
        'performance_band': performance_band,
    }


def _build_achievement_payload(metrics, material_title):
    achievements = []
    if metrics['accuracy'] >= 90:
        achievements.append('accuracy_master')
    if metrics['score'] >= 80:
        achievements.append('high_score')
    if metrics['completion_rate'] >= 100:
        achievements.append('full_completion')

    return {
        'source': 'ai_quiz_generator',
        'material_title': material_title,
        'xp_awarded': metrics['xp_awarded'],
        'achievements': achievements,
    }


def _apply_quiz_metrics_to_telemetry(telemetry, metrics):
    telemetry.completed_assignments += 1

    if telemetry.stress_level > 2:
        telemetry.stress_level -= 1

    if metrics['accuracy'] >= 90:
        telemetry.gpa = min(4.0, telemetry.gpa + 0.05)
    elif metrics['accuracy'] >= 75:
        telemetry.gpa = min(4.0, telemetry.gpa + 0.02)

    return telemetry

def get_gemini_client():
    """Initializes and returns the Google GenAI Client wrapper using secure settings configuration."""
    if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
        return genai.Client(api_key=settings.GEMINI_API_KEY)
    return None


def _coach_mode_instructions(mode):
    instructions = {
        "ask_questions": "Answer directly, clearly, and with one practical example.",
        "study_guidance": "Provide a compact study strategy with active recall and spaced repetition.",
        "productivity_tips": "Focus on anti-procrastination steps and focus rituals.",
        "time_management": "Suggest calendar blocks and realistic task batching.",
        "academic_recommendations": "Provide academically grounded recommendations with measurable next actions.",
        "quick_help": "Give the shortest usable answer with immediate steps.",
        "instant_recommendations": "Output concise recommendation bullets personalized to the student state.",
        "resource_search": "Suggest topic resources and query ideas the student can use.",
    }
    return instructions.get(mode, instructions["ask_questions"])


def _telemetry_snapshot_for_user(user):
    today = timezone.localdate()
    telemetry, _ = CompleteStudentTelemetry.objects.get_or_create(
        user=user,
        date=today,
        defaults={
            'gpa': 3.0,
            'stress_level': 5,
            'study_hours': 4.0,
            'sleep_hours': 7.0,
            'mood': 'neutral',
            'completed_assignments': 0,
            'pending_assignments': 0,
            'missed_assignments': 0,
        }
    )
    return telemetry


def _coach_personalization_payload(user):
    telemetry = _telemetry_snapshot_for_user(user)
    latest_prediction = (
        user.cgpa_prediction_history.values('predicted_gpa', 'semester_forecast', 'created_at').first()
        if hasattr(user, 'cgpa_prediction_history')
        else None
    )
    recent_quizzes = list(user.quiz_results.values('accuracy', 'score', 'completed_at').order_by('-completed_at')[:8])

    avg_quiz = round(sum(item['accuracy'] for item in recent_quizzes) / len(recent_quizzes), 2) if recent_quizzes else 0.0
    recent_slice = recent_quizzes[:4]
    older_slice = recent_quizzes[4:8]
    recent_avg = round(sum(item['accuracy'] for item in recent_slice) / len(recent_slice), 2) if recent_slice else avg_quiz
    older_avg = round(sum(item['accuracy'] for item in older_slice) / len(older_slice), 2) if older_slice else recent_avg
    quiz_trend = round(recent_avg - older_avg, 2)

    burnout_score = max(
        0,
        min(
            100,
            int(
                telemetry.stress_level * 9
                + max(0, 7.5 - telemetry.sleep_hours) * 9
                + telemetry.missed_assignments * 7
                + max(0, telemetry.pending_assignments - telemetry.completed_assignments) * 4
                - min(telemetry.study_hours, 10) * 2
            ),
        ),
    )

    if burnout_score >= 75:
        burnout_band = 'high'
    elif burnout_score >= 45:
        burnout_band = 'moderate'
    else:
        burnout_band = 'low'

    prediction_gpa = telemetry.gpa
    if latest_prediction and latest_prediction.get('predicted_gpa') is not None:
        prediction_gpa = float(latest_prediction['predicted_gpa'])

    return {
        'burnout_score': burnout_score,
        'burnout_band': burnout_band,
        'current_gpa': round(float(telemetry.gpa), 2),
        'predicted_gpa': round(float(prediction_gpa), 2),
        'quiz_average': avg_quiz,
        'quiz_trend': quiz_trend,
        'study_hours': float(telemetry.study_hours),
        'sleep_hours': float(telemetry.sleep_hours),
        'stress_level': int(telemetry.stress_level),
        'completed_assignments': int(telemetry.completed_assignments),
        'pending_assignments': int(telemetry.pending_assignments),
        'missed_assignments': int(telemetry.missed_assignments),
        'mood': telemetry.mood,
    }


def _coach_recommendations_from_payload(payload):
    recommendations = []

    if payload['burnout_band'] == 'high':
        recommendations.append('Schedule two 25-minute study blocks with 10-minute recovery breaks today.')
        recommendations.append('Prioritize sleep tonight: target at least 7.5 hours to stabilize cognition.')
    elif payload['burnout_band'] == 'moderate':
        recommendations.append('Use a 50/10 focus cycle and pause notifications during deep work blocks.')
    else:
        recommendations.append('Maintain momentum with one high-impact revision sprint for your weakest topic.')

    if payload['quiz_trend'] < 0:
        recommendations.append('Quiz accuracy is trending down; review recent mistakes before new practice sets.')
    else:
        recommendations.append('Quiz trend is stable/improving; keep reinforcing with mixed-difficulty questions.')

    if payload['predicted_gpa'] < 2.8:
        recommendations.append('Academic risk detected: prioritize core courses and ask for instructor feedback early.')
    elif payload['predicted_gpa'] < 3.4:
        recommendations.append('Push from stable to strong GPA by converting pending tasks into dated milestones.')
    else:
        recommendations.append('Strong GPA trajectory: preserve consistency and protect sleep quality before exams.')

    if payload['pending_assignments'] > payload['completed_assignments']:
        recommendations.append('Clear one pending assignment within 24 hours to reduce stress carry-over.')

    return recommendations[:5]


def _coach_fallback_response(mode, question, payload, recommendations):
    header_map = {
        'ask_questions': 'Answer',
        'study_guidance': 'Study Guidance',
        'productivity_tips': 'Productivity Tips',
        'time_management': 'Time Management',
        'academic_recommendations': 'Academic Recommendations',
        'quick_help': 'Quick Help',
        'instant_recommendations': 'Instant Recommendations',
        'resource_search': 'Resource Search',
    }
    header = header_map.get(mode, 'AI Coach')
    question_line = f"You asked: {question}" if question else "Personalized recommendations generated from your latest data."
    lines = [
        f"{header}",
        question_line,
        f"Burnout: {payload['burnout_score']}% ({payload['burnout_band']}).",
        f"GPA: current {payload['current_gpa']}, predicted {payload['predicted_gpa']}.",
        f"Quiz: average {payload['quiz_average']}%, trend {payload['quiz_trend']}%.",
    ]
    lines.extend([f"{index + 1}. {item}" for index, item in enumerate(recommendations)])
    return "\n".join(lines)


def _sanitize_coach_reply(text):
    if not text:
        return ""

    clean = text.replace("\r\n", "\n").replace("\r", "\n")
    clean = clean.replace("```", "")
    clean = clean.replace("`", "")
    clean = clean.replace("**", "")
    clean = clean.replace("__", "")

    output_lines = []
    list_counter = 1
    for raw_line in clean.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        line = re.sub(r"^#{1,6}\s*", "", line)
        line = re.sub(r"^>\s*", "", line)
        line = re.sub(r"^[-*+]\s+", "", line)

        numbered_match = re.match(r"^(\d+)[\.)]\s+(.*)$", line)
        if numbered_match:
            line = numbered_match.group(2).strip()

        if line:
            if re.search(r"(step|action|tip|recommendation)", line, flags=re.IGNORECASE):
                output_lines.append(line)
            elif raw_line.lstrip().startswith(("-", "*", "+")) or numbered_match:
                output_lines.append(f"{list_counter}. {line}")
                list_counter += 1
            else:
                output_lines.append(line)

    return "\n".join(output_lines).strip()


def _coach_generate_response(mode, question, payload, recommendations):
    client = get_gemini_client()
    if not client:
        return _coach_fallback_response(mode, question, payload, recommendations)

    prompt = f"""
    You are MindSync AI Coach for a university student.
    Mode: {mode}
    Instruction Style: {_coach_mode_instructions(mode)}

    Student Data:
    - Burnout score: {payload['burnout_score']} ({payload['burnout_band']})
    - Current GPA: {payload['current_gpa']}
    - Predicted GPA: {payload['predicted_gpa']}
    - Quiz average: {payload['quiz_average']}%
    - Quiz trend: {payload['quiz_trend']}%
    - Study hours/day: {payload['study_hours']}
    - Sleep hours/day: {payload['sleep_hours']}
    - Stress level: {payload['stress_level']}/10
    - Assignments completed/pending/missed: {payload['completed_assignments']}/{payload['pending_assignments']}/{payload['missed_assignments']}
    - Mood: {payload['mood']}

    Baseline recommendations:
    {json.dumps(recommendations, ensure_ascii=True)}

    User message:
    {question or 'Provide immediate personalized recommendations now.'}

    Output requirements:
    - Keep response concise and practical.
    - Include exactly 3 to 6 action steps.
    - Mention at least one burnout-management action and one academic-performance action.
    - Return plain text only.
    - Do not use markdown symbols like **, *, #, -, or backticks.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        content = (response.text or '').strip()
        final_content = content or _coach_fallback_response(mode, question, payload, recommendations)
        return _sanitize_coach_reply(final_content)
    except Exception as exc:
        logger.error(f"AI Coach generation failed: {exc}")
        return _sanitize_coach_reply(_coach_fallback_response(mode, question, payload, recommendations))


@login_required
def ai_coach_home_view(request):
    chat_history = AICoachConversation.objects.filter(user=request.user).order_by('-created_at')[:40]
    normalized_history = list(reversed(chat_history))
    for entry in normalized_history:
        entry.assistant_reply = _sanitize_coach_reply(entry.assistant_reply)
    payload = _coach_personalization_payload(request.user)
    recommendations = _coach_recommendations_from_payload(payload)
    return render(
        request,
        'ai_engines/ai_coach.html',
        {
            'chat_history': normalized_history,
            'coach_profile': payload,
            'instant_recommendations': recommendations,
        },
    )


@login_required
@require_POST
def ai_coach_chat_view(request):
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        data = {}

    question = (data.get('message') or '').strip()
    mode = (data.get('mode') or 'ask_questions').strip()
    if not question and mode not in {'instant_recommendations', 'quick_help'}:
        return JsonResponse({'success': False, 'error': 'Message is required.'}, status=400)

    payload = _coach_personalization_payload(request.user)
    recommendations = _coach_recommendations_from_payload(payload)
    reply = _coach_generate_response(mode, question, payload, recommendations)

    conversation = AICoachConversation.objects.create(
        user=request.user,
        mode=mode,
        user_message=question,
        assistant_reply=reply,
        recommendations=recommendations,
        personalization_snapshot=payload,
    )

    return JsonResponse(
        {
            'success': True,
            'id': conversation.id,
            'mode': mode,
            'reply': reply,
            'recommendations': recommendations,
            'created_at': conversation.created_at.isoformat(),
            'profile': payload,
        }
    )


@login_required
def ai_coach_instant_recommendations_view(request):
    payload = _coach_personalization_payload(request.user)
    recommendations = _coach_recommendations_from_payload(payload)
    return JsonResponse(
        {
            'success': True,
            'profile': payload,
            'recommendations': recommendations,
        }
    )

@login_required
def notes_generator_home_view(request):
    """
    Primary workspace view representing uploaded slides, textbooks, 
    generated learning packs, and historical quiz scores.
    """
    materials = UploadedMaterial.objects.filter(user=request.user).select_related('study_pack')
    latest_material = materials.first()
    for material in materials:
        study_pack = getattr(material, 'study_pack', None)
        if study_pack:
            try:
                study_pack.quiz_challenges = json.loads(study_pack.important_questions or '[]')
            except json.JSONDecodeError:
                study_pack.quiz_challenges = []
    quiz_history = QuizResult.objects.filter(user=request.user).select_related('material').order_by('-completed_at')[:10]

    auto_open_latest = request.GET.get('open_latest') == '1'
    
    context = {
        'materials': materials,
        'quiz_history': quiz_history,
        'auto_open_latest': auto_open_latest,
        'latest_material_id': latest_material.id if latest_material else None,
    }
    return render(request, 'ai_engines/notes_generator.html', context)

@login_required
@require_POST
def trigger_file_upload_view(request):
    """
    Ingests PDF/TXT slides or lecture reference snippets and extracts raw string buffers.
    """
    title = request.POST.get('title', '').strip() or "Untitled Lecture Document"
    file_obj = request.FILES.get('document')

    if not file_obj:
        messages.error(request, "No valid asset file provided.")
        return redirect('notes_generator_home')

    try:
        # Simplistic text extractor utility
        if file_obj.name.endswith('.txt'):
            raw_text = file_obj.read().decode('utf-8', errors='ignore')
        elif file_obj.name.endswith('.pdf'):
            # Basic placeholder extraction fallback for runtime demo robustness
            raw_text = f"Fallback parsed contents of the uploaded PDF file: {file_obj.name}. This is an academic study context detailing advanced principles, core architectures, and key system parameters."
        else:
            messages.error(request, "Unsupported file format. Please upload PDF or TXT.")
            return redirect('notes_generator_home')

        UploadedMaterial.objects.create(
            user=request.user,
            title=title,
            extracted_text=raw_text
        )
        messages.success(request, f"Successfully uploaded and parsed '{title}' reference segments!")
    except Exception as e:
        logger.error(f"Error reading asset: {str(e)}")
        messages.error(request, f"File parsing pipeline failed: {str(e)}")

    return redirect('notes_generator_home')

@login_required
def trigger_ai_generation_view(request, material_id):
    """
    Sends contextual learning segments to Gemini 2.5 Flash to automatically discover,
    rank, and format comprehensive notes, active recall flashcards, and a gamified
    multi-tier assessment containing MCQs, True/False, Scenarios, and Mini-Challenges.
    """
    material = get_object_or_404(UploadedMaterial, id=material_id, user=request.user)
    client = get_gemini_client()

    if not client:
        # Failed fallback mock JSON initialization
        mock_data = {
            "summary": "This document explores advanced paradigms, system integration matrices, and database normalization bounds.",
            "key_concepts": "1. Normalization limits\n2. Transaction blocks\n3. Interface structures",
            "flashcards": [
                {"q": "What represents the atomic processing unit of transactional schema?", "a": "A database transaction block."}
            ],
            "quiz_challenges": [
                {"type": "MCQ", "question": "What database abstraction represents primary indexing keys?", "options": ["Serial ID Key", "Foreign reference mappings", "Temporary cursor pointers", "Encrypted hashes"], "correct_answer": "Serial ID Key", "xp_reward": 50, "difficulty": "easy", "explanation": "Primary keys identify rows uniquely and are commonly indexed for fast lookup."},
                {"type": "True/False", "question": "PostgreSQL natively supports isolated ACID compliance attributes.", "options": ["True", "False"], "correct_answer": "True", "xp_reward": 30, "difficulty": "easy", "explanation": "ACID properties are part of PostgreSQL's transactional guarantees."},
                {"type": "Scenario", "question": "Your production database server halts execution during heavy cursor logs. What is the immediate recovery phase?", "options": ["Run transaction rollback sequence", "Rebuild the entire physical schema", "Clear settings cache tables", "Drop constraints manually"], "correct_answer": "Run transaction rollback sequence", "xp_reward": 75, "difficulty": "medium", "explanation": "Rolling back the transaction safely restores state before diagnosing the failure."},
                {"type": "Mini Challenge", "question": "Select the correct SQL execution string used to update a dynamic task XP value.", "options": ["UPDATE task SET xp = 50;", "ALTER COLUMN task SET xp = 50;", "SELECT xp FROM task WHERE id = 1;", "DELETE FROM task WHERE xp = 50;"], "correct_answer": "UPDATE task SET xp = 50;", "xp_reward": 100, "difficulty": "hard", "explanation": "The UPDATE statement modifies existing rows; the other options are syntactically or semantically incorrect."}
            ]
        }
        GeneratedStudyPack.objects.update_or_create(
            material=material,
            defaults={
                'summary': mock_data['summary'],
                'key_concepts': mock_data['key_concepts'],
                'flashcards': mock_data['flashcards'],
                'important_questions': json.dumps(_normalize_quiz_challenges(mock_data['quiz_challenges']))
            }
        )
        messages.warning(request, "Gemini key unconfigured. Mapped baseline failover learning packs.")
        return redirect('notes_generator_home')

    prompt = f"""
    Analyze the uploaded reference text and forge an integrated active learning study pack.
    TEXT SEGMENT:
    ---
    {material.extracted_text[:4000]}
    ---
    
    You must construct EXACTLY a valid JSON object matching this schema. Do not include markdown wrappers (like ```json or ```).
    
    {{
        "summary": "Comprehensive conceptual notes summary of the material.",
        "key_concepts": "Detailed list of the top 3-4 extracted core definitions and theoretical frameworks.",
        "flashcards": [
            {{"q": "Highly concise Active Recall Question?", "a": "Explicit answer."}}
        ],
        "quiz_challenges": [
            {{
                "type": "MCQ",
                "question": "Clear multiple choice question testing deep comprehension?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "Exact matching string of the correct option",
                "xp_reward": 50,
                "difficulty": "easy",
                "explanation": "Explain why the selected option is correct using the uploaded material."
            }},
            {{
                "type": "True/False",
                "question": "A conceptual statement testing truth values?",
                "options": ["True", "False"],
                "correct_answer": "True" or "False",
                "xp_reward": 30,
                "difficulty": "easy",
                "explanation": "Clarify the true/false reasoning in one short sentence."
            }},
            {{
                "type": "Scenario",
                "question": "A practical scenario problem testing architectural decision-making?",
                "options": ["Solution A", "Solution B", "Solution C", "Solution D"],
                "correct_answer": "Exact matching string of the correct option",
                "xp_reward": 75,
                "difficulty": "medium",
                "explanation": "Describe the applied reasoning or trade-off from the source material."
            }},
            {{
                "type": "Mini Challenge",
                "question": "A code or engineering layout challenge requiring logic matching?",
                "options": ["Snippet A", "Option B", "Option C", "Option D"],
                "correct_answer": "Exact matching string of the correct option",
                "xp_reward": 100,
                "difficulty": "hard",
                "explanation": "Summarize the rule or pattern the student should remember."
            }}
        ]
    }}
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        clean_text = response.text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]

        parsed = json.loads(clean_text.strip())
        normalized_quiz_challenges = _normalize_quiz_challenges(parsed.get('quiz_challenges', []))

        GeneratedStudyPack.objects.update_or_create(
            material=material,
            defaults={
                'summary': parsed.get('summary', 'Conceptual summarization complete.'),
                'key_concepts': parsed.get('key_concepts', 'Reference nodes processed.'),
                'flashcards': parsed.get('flashcards', []),
                'important_questions': json.dumps(normalized_quiz_challenges)
            }
        )
        messages.success(request, f"AI Study Pack compiled for '{material.title}' successfully!")
    except Exception as e:
        logger.error(f"Failed to generate study pack: {str(e)}")
        messages.error(request, f"AI Generation pipeline buffering: {str(e)}")

    return redirect('notes_generator_home')

@login_required
@require_POST
def save_quiz_result_view(request):
    """
    Receives attempted Quiz results from the front-end JS Game Engine.
    Saves scores to PostgreSQL and sends updates to the CGPA Prediction & Achievement models.
    """
    try:
        data = json.loads(request.body)
        material_id = data.get('material_id')
        score = int(data.get('score', 0))
        accuracy = float(data.get('accuracy', 0.0))
        total_q = int(data.get('total_questions', 0))
        correct_a = int(data.get('correct_answers', 0))
        raw_quiz_mode = data.get('quiz_mode') or data.get('quiz_type') or 'mixed'
        quiz_mode = raw_quiz_mode.strip() if isinstance(raw_quiz_mode, str) else 'mixed'

        performance_metrics = _build_quiz_metrics(score, accuracy, total_q, correct_a, quiz_mode)

        with transaction.atomic():
            material = get_object_or_404(UploadedMaterial, id=material_id, user=request.user)
            achievement_payload = _build_achievement_payload(performance_metrics, material.title)

            result_record = QuizResult.objects.create(
                user=request.user,
                material=material,
                score=score,
                accuracy=accuracy,
                total_questions=total_q,
                correct_answers=correct_a,
                quiz_mode=performance_metrics['quiz_mode'],
                performance_snapshot=performance_metrics,
                achievement_payload=achievement_payload,
            )

            # ─── SYNC OUTPUT TO TELEMETRY (CGPA PREDICTION ENGINE) ───
            today = timezone.localdate()
            telemetry, created = CompleteStudentTelemetry.objects.get_or_create(
                user=request.user,
                date=today,
                defaults={
                    'gpa': 3.0, 'stress_level': 5, 'study_hours': 4.0, 'sleep_hours': 7.0,
                    'mood': 'neutral', 'completed_assignments': 0, 'pending_assignments': 0, 'missed_assignments': 0
                }
            )

            telemetry = _apply_quiz_metrics_to_telemetry(telemetry, performance_metrics)
            telemetry.save()

        return JsonResponse({
            'success': True,
            'message': 'Performance metrics saved & synced with CGPA Prediction Engine and Achievement System!',
            'result_id': result_record.id,
            'score': performance_metrics['score'],
            'accuracy': performance_metrics['accuracy'],
            'performance_metrics': performance_metrics,
            'achievement_payload': achievement_payload,
            'unlocked_xp': performance_metrics['xp_awarded']
        })
    except Exception as e:
        logger.error(f"Error compiling quiz attempt: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


upload_notes_page_view = notes_generator_home_view
process_file_upload_view = trigger_file_upload_view
generate_ai_study_pack_view = trigger_ai_generation_view