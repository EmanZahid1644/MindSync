import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import render
from google import genai

from .models import TopicResourceCache

logger = logging.getLogger(__name__)


def get_gemini_client():
    if getattr(settings, "GEMINI_API_KEY", None):
        return genai.Client(api_key=settings.GEMINI_API_KEY)
    return None


def _strip_code_fences(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _fallback_resources(query: str, message: str) -> dict:
    slug = query.lower().replace(" ", "-")
    return {
        "topic": query,
        "difficulty_rating": "Intermediate",
        "error": True,
        "error_msg": message,
        "articles": [
            {"title": f"Advanced Paradigms in {query} - Core Review", "url": "https://arxiv.org", "source": "arXiv Paper / Fallback"}
        ],
        "blogs": [
            {"title": f"Migrating our microservices to {query}", "url": "https://dev.to", "source": "Dev.to / Fallback"}
        ],
        "github_repos": [
            {"repo": f"awesome-{slug}", "url": "https://github.com", "desc": "Curated workspace repository tracking frameworks."}
        ],
        "videos": [
            {"title": f"Deep Dive Study into {query} Architecture", "url": "https://youtube.com", "channel": "MindSync AI Core"}
        ],
    }


def _normalize_topic(query: str) -> str:
    return " ".join((query or "").lower().split())


def _build_flashcards_from_resources(query: str, resources: dict) -> list:
    flashcards = []

    difficulty = resources.get("difficulty_rating") or "Intermediate"
    flashcards.append({
        "q": f"What difficulty level is recommended for {query}?",
        "a": str(difficulty),
    })

    first_article = (resources.get("articles") or [{}])[0]
    first_repo = (resources.get("github_repos") or [{}])[0]
    first_video = (resources.get("videos") or [{}])[0]

    if first_article.get("title"):
        flashcards.append({
            "q": f"Which research/article resource should you review first for {query}?",
            "a": first_article.get("title", ""),
        })
    if first_repo.get("repo"):
        flashcards.append({
            "q": f"Which GitHub repository is suggested for {query}?",
            "a": first_repo.get("repo", ""),
        })
    if first_video.get("title"):
        flashcards.append({
            "q": f"Which video lecture can you start with for {query}?",
            "a": first_video.get("title", ""),
        })

    return flashcards[:6]


@login_required
def planner_home_view(request):
    query = request.GET.get("query", "").strip()
    resources = None

    recent_cache_qs = TopicResourceCache.objects.order_by("-updated_at")[:10]
    topic_history = [
        {
            "topic": item.original_topic,
            "hits": item.hit_count,
            "updated_at": item.updated_at,
            "difficulty": (item.resources_payload or {}).get("difficulty_rating", "Intermediate"),
        }
        for item in recent_cache_qs
    ]

    if query:
        normalized_topic = _normalize_topic(query)

        cache_entry = TopicResourceCache.objects.filter(normalized_topic=normalized_topic).first()
        if cache_entry:
            TopicResourceCache.objects.filter(id=cache_entry.id).update(hit_count=F("hit_count") + 1)
            cache_entry.refresh_from_db()

            resources = dict(cache_entry.resources_payload or {})
            resources.setdefault("topic", query)
            resources.setdefault("difficulty_rating", "Intermediate")
            resources.setdefault("articles", [])
            resources.setdefault("blogs", [])
            resources.setdefault("github_repos", [])
            resources.setdefault("videos", [])
            resources["flashcards"] = cache_entry.flashcards or _build_flashcards_from_resources(query, resources)
            resources["error"] = False
            resources["from_cache"] = True
            resources["cache_hits"] = cache_entry.hit_count

            return render(
                request,
                "planner/planner_hub.html",
                {"query": query, "resources": resources, "topic_history": topic_history},
            )

        client = get_gemini_client()
        if client:
            prompt = f"""
Act as an AI Academic Resource Ranking Engine. Assess the search topic query: '{query}'.
Evaluate resources based on relevance, popularity, and difficulty level.
Return EXACTLY a valid JSON object with this structure and no markdown wrappers:

{{
  "topic": "{query}",
  "difficulty_rating": "Beginner",
  "articles": [
    {{"title": "Academic paper title or official guide", "url": "https://arxiv.org", "source": "arXiv / Research"}}
  ],
  "blogs": [
    {{"title": "Production case study or blog text", "url": "https://dev.to", "source": "Dev.to / Tech Blog"}}
  ],
  "github_repos": [
    {{"repo": "username/repository", "url": "https://github.com", "desc": "Repository description tracing use cases."}}
  ],
  "videos": [
    {{"title": "High quality tech lecture title", "url": "https://youtube.com", "channel": "Tech Channel"}}
    ],
    "flashcards": [
        {{"q": "Question for quick revision", "a": "Short answer"}}
  ]
}}
"""
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                clean_text = _strip_code_fences(getattr(response, "text", ""))
                resources = json.loads(clean_text)
                resources.setdefault("flashcards", _build_flashcards_from_resources(query, resources))
                resources["error"] = False
                resources["from_cache"] = False

                TopicResourceCache.objects.update_or_create(
                    normalized_topic=normalized_topic,
                    defaults={
                        "original_topic": query,
                        "resources_payload": {
                            "topic": resources.get("topic", query),
                            "difficulty_rating": resources.get("difficulty_rating", "Intermediate"),
                            "articles": resources.get("articles", []),
                            "blogs": resources.get("blogs", []),
                            "github_repos": resources.get("github_repos", []),
                            "videos": resources.get("videos", []),
                        },
                        "flashcards": resources.get("flashcards", []),
                        "source": "gemini",
                        "hit_count": 1,
                    },
                )
            except Exception as exc:
                logger.exception("Gemini resource discovery failed: %s", exc)
                resources = _fallback_resources(query, "MindSync Discovery AI connection buffering.")
                resources["flashcards"] = _build_flashcards_from_resources(query, resources)
                resources["from_cache"] = False
        else:
            resources = _fallback_resources(query, "System running locally. Set GEMINI_API_KEY in settings.")
            resources["flashcards"] = _build_flashcards_from_resources(query, resources)
            resources["from_cache"] = False

    return render(
        request,
        "planner/planner_hub.html",
        {"query": query, "resources": resources, "topic_history": topic_history},
    )
