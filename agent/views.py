from django.shortcuts import render

# Create your views here.
import json
import traceback
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .utils import fetch_engineering_news, summarize_with_hf

# optional: import Article if you want to save
try:
    from .models import Article
except Exception:
    Article = None

@csrf_exempt
def health(request):
    return JsonResponse({"status": "ok", "time": timezone.now().isoformat()})

@csrf_exempt
def telex_webhook(request):
    """
    Expected incoming Telex payload (examples—they might send different keys).
    We'll support common keys: 'text' or 'message' or 'body' -> the user text.
    Telex may include messageId, channelId, from, etc.
    We'll respond with a Telex-friendly JSON:
    {
      "reply_to": "<messageId>",
      "actions": [
        { "type": "send_message", "body": { "text": "..." } }
      ]
    }
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    try:
        payload = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "invalid json"}, status=400)

    # Try several common keys for the incoming text:
    text = (payload.get("text") or payload.get("message") or payload.get("body") or "").strip()
    message_id = payload.get("messageId") or payload.get("id") or payload.get("message_id")

    if not text:
        # no message from user — return help text
        help_text = ("Hi — I'm the Engineering News Agent. Try commands like:\n"
                     "- 'engineering news'\n"
                     "- 'civil engineering news'\n"
                     "- 'mechanical engineering discoveries'\n"
                     "I fetch recent engineering articles and summarize them.")
        resp = {
            "reply_to": message_id,
            "actions": [{"type": "send_message", "body": {"text": help_text}}]
        }
        return JsonResponse(resp, status=200)

    lower = text.lower()

    # Determine query
    # Basic keyword mapping
    if "civil" in lower:
        query = "civil engineering OR structural engineering OR bridge OR concrete"
    elif "mechanical" in lower:
        query = "mechanical engineering OR robotics OR manufacturing OR thermodynamics"
    elif "aerospace" in lower:
        query = "aerospace OR aerospace engineering OR flight OR space"
    elif "materials" in lower or "materials science" in lower:
        query = "materials science OR nanomaterials OR composites OR metallurgy"
    elif "software" in lower or "ai" in lower:
        query = "software engineering OR ai OR machine learning OR systems engineering"
    else:
        # default: broad engineering news
        query = "engineering OR technology OR discovery OR breakthrough"

    # Fetch articles
    articles = fetch_engineering_news(query=query, limit=3)
    if not articles:
        reply_text = "Sorry — I couldn't fetch news right now. Try again later."
        resp = {"reply_to": message_id, "actions": [{"type": "send_message", "body": {"text": reply_text}}]}
        return JsonResponse(resp, status=200)

    # Summarize each article
    bullets = []
    for art in articles:
        title = art.get("title") or "No title"
        desc = art.get("description") or ""
        url = art.get("url") or ""
        text_for_summary = desc if desc else title
        # ensure we don't send an empty string to HF
        if not text_for_summary:
            text_for_summary = title
        summary = summarize_with_hf(text_for_summary)
        bullets.append(f"• {title}\\n{summary}\\n{url}")

        # Optionally save to DB if Article model is available
        if Article:
            try:
                Article.objects.create(title=title, url=url, summary=summary, published_at=art.get("publishedAt"))
            except Exception:
                # ignore save errors
                pass

    reply_text = "Here are latest engineering items I found:\\n\\n" + "\\n\\n".join(bullets)

    response = {
        "reply_to": message_id,
        "actions": [
            {
                "type": "send_message",
                "body": {"text": reply_text}
            }
        ]
    }
    return JsonResponse(response, status=200)
