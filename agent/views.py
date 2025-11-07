    
from django.shortcuts import render
import json
import traceback
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .utils import fetch_engineering_news, summarize_with_hf

try:
    from .models import Article
except Exception:
    Article = None

@csrf_exempt
def health(request):
    return JsonResponse({"status": "ok", "time": timezone.now().isoformat()})

@csrf_exempt
def telex_webhook(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "invalid json"}, status=400)

    try:
        # --- Detect the source of input ---
        text = ""
        if "a2a" in payload:
            text = payload["a2a"].get("input", "")
        else:
            text = (
                payload.get("text")
                or payload.get("message")
                or payload.get("body")
                or ""
            ).strip()

        message_id = (
            payload.get("messageId")
            or payload.get("id")
            or payload.get("message_id")
            or None
        )

        # --- If no user message ---
        if not text:
            help_text = (
                "👋 Hi — I'm the *Engineering News Agent*.\n\n"
                "Try commands like:\n"
                "- `engineering news`\n"
                "- `civil engineering news`\n"
                "- `mechanical engineering discoveries`\n"
                "- `AI in software engineering`\n\n"
                "I’ll fetch recent engineering articles and summarize them for you."
            )
            return JsonResponse(
                {
                    "reply_to": message_id,
                    "actions": [
                        {"type": "send_message", "body": {"text": help_text}}
                    ],
                },
                status=200,
            )

        lower = text.lower()

        # --- Determine query ---
        if "civil" in lower:
            query = "civil engineering OR structural engineering OR bridge OR concrete"
        elif "mechanical" in lower:
            query = "mechanical engineering OR robotics OR manufacturing OR thermodynamics"
        elif "aerospace" in lower:
            query = "aerospace OR flight OR satellite OR space technology"
        elif "materials" in lower or "materials science" in lower:
            query = "materials science OR nanomaterials OR composites OR metallurgy"
        elif "software" in lower or "ai" in lower:
            query = "software engineering OR AI OR machine learning OR programming"
        else:
            query = "engineering OR technology OR innovation OR discovery OR breakthrough"

        # --- Fetch and summarize ---
        articles = fetch_engineering_news(query=query, limit=3)
        if not articles:
            reply_text = "Sorry — I couldn’t fetch news right now. Try again later."
            return JsonResponse(
                {
                    "reply_to": message_id,
                    "actions": [
                        {"type": "send_message", "body": {"text": reply_text}}
                    ],
                },
                status=200,
            )

        bullets = []
        for art in articles:
            title = art.get("title") or "No title"
            desc = art.get("description") or ""
            url = art.get("url") or ""
            text_for_summary = desc if desc else title
            summary = summarize_with_hf(text_for_summary)
            bullets.append(f"• {title}\n{summary}\n{url}")

            if Article:
                try:
                    Article.objects.create(
                        title=title,
                        url=url,
                        summary=summary,
                        published_at=art.get("publishedAt"),
                    )
                except Exception:
                    pass

        reply_text = "📰 Here are the latest engineering items I found:\n\n" + "\n\n".join(bullets)

        return JsonResponse(
            {
                "reply_to": message_id,
                "actions": [
                    {"type": "send_message", "body": {"text": reply_text}}
                ],
            },
            status=200,
        )

    except Exception as e:
        print("Webhook error:", str(e))
        traceback.print_exc()
        return JsonResponse(
            {
                "reply_to": None,
                "actions": [
                    {
                        "type": "send_message",
                        "body": {
                            "text": f"⚠️ An error occurred while processing your request: {e}"
                        },
                    }
                ],
            },
            status=500,
        )
