# Generated manually for AI Coach conversation persistence

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_engines", "0003_alter_generatedstudypack_key_concepts_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AICoachConversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "mode",
                    models.CharField(
                        choices=[
                            ("ask_questions", "Ask Questions"),
                            ("study_guidance", "Study Guidance"),
                            ("productivity_tips", "Productivity Tips"),
                            ("time_management", "Time Management"),
                            ("academic_recommendations", "Academic Recommendations"),
                            ("quick_help", "Quick Help"),
                            ("instant_recommendations", "Instant Recommendations"),
                            ("resource_search", "Resource Search"),
                        ],
                        default="ask_questions",
                        max_length=40,
                    ),
                ),
                ("user_message", models.TextField(blank=True, default="")),
                ("assistant_reply", models.TextField(default="")),
                ("recommendations", models.JSONField(blank=True, default=list)),
                ("personalization_snapshot", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ai_coach_conversations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
