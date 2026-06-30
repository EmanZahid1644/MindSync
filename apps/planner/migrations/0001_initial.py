# Generated manually for planner topic resource cache

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TopicResourceCache",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("normalized_topic", models.CharField(max_length=255, unique=True)),
                ("original_topic", models.CharField(max_length=255)),
                ("resources_payload", models.JSONField(blank=True, default=dict)),
                ("flashcards", models.JSONField(blank=True, default=list)),
                ("source", models.CharField(default="gemini", max_length=20)),
                ("hit_count", models.IntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("last_accessed_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-updated_at"]},
        ),
    ]
