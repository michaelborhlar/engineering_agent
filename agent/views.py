from django.shortcuts import render
import json
import traceback
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .utils import fetch_engineering_news, summarize_with_hf

try:
    from .models import Article
except Exception:
    Article = None

@csrf_exempt
def health(request):
    """Health check endpoint for A2A validation"""
    return JsonResponse({"status": "ok", "time": timezone.now().isoformat()})

@csrf_exempt
@require_http_methods(["GET", "POST"])
def telex_webhook(request):
    """
    A2A-compatible webhook for Telex.im
    Handles both GET (health check) and POST (A2A messages)
    """
    
    # Handle GET requests - Health check for A2A validation
    if request.method == "GET":
        return JsonResponse({
            "status": "active",
            "agent": "Engineering News Agent",
            "version": "1.0",
            "timestamp": timezone.now().isoformat(),
            "capabilities": ["news_fetching", "summarization"]
        })
    
    # Handle POST requests - A2A message processing
    try:
        # Parse JSON payload
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "type": "error", 
                "message": "Invalid JSON payload"
            }, status=400)

        # --- A2A Protocol Message Handling ---
        message_type = payload.get("type", "message")
        conversation_id = payload.get("conversation_id")
        
        # Extract text from A2A format
        text = payload.get("message", "").strip()
        
        # Fallback for other formats (backward compatibility)
        if not text:
            if "a2a" in payload:
                text = payload["a2a"].get("input", "")
            else:
                text = (
                    payload.get("text")
                    or payload.get("body")
                    or ""
                ).strip()

        # --- If no user message, return help ---
        if not text:
            help_text = (
                "👋 Hi — I'm the *Engineering News Agent*.\n\n"
                "Try commands like:\n"
                "- `engineering news`\n" 
                "- `civil engineering news`\n"
                "- `mechanical engineering discoveries`\n"
                "- `AI in software engineering`\n\n"
                "I'll fetch recent engineering articles and summarize them for you."
            )
            
            # Return in A2A format
            return JsonResponse({
                "status": "success",
                "type": "message",
                "message": help_text,
                "conversation_id": conversation_id,
                "timestamp": timezone.now().isoformat()
            })

        # --- Process Engineering News Request ---
        lower = text.lower()

        # Determine query based on user input
        if "civil" in lower:
            query = "civil engineering OR structural engineering OR bridge OR concrete"
        elif "mechanical" in lower:
            query = "mechanical engineering OR robotics OR manufacturing OR thermodynamics"
        elif "aerospace" in lower:
            query = "aerospace OR flight OR satellite OR space technology"
        elif "materials" in lower or "materials science" in lower:
            query = "materials science OR nanomaterials OR composites OR metallurgy"
        elif "software" in lower or "ai" in lower or "programming" in lower:
            query = "software engineering OR AI OR machine learning OR programming"
        else:
            query = "engineering OR technology OR innovation OR discovery OR breakthrough"

        # Fetch and summarize articles
        articles = fetch_engineering_news(query=query, limit=3)
        
        if not articles:
            reply_text = "Sorry — I couldn't fetch engineering news right now. Try again later."
            return JsonResponse({
                "status": "success",
                "type": "message", 
                "message": reply_text,
                "conversation_id": conversation_id,
                "timestamp": timezone.now().isoformat()
            })

        # Format response with articles
        bullets = []
        for art in articles:
            title = art.get("title") or "No title"
            desc = art.get("description") or ""
            url = art.get("url") or ""
            text_for_summary = desc if desc else title
            summary = summarize_with_hf(text_for_summary)
            bullets.append(f"• {title}\n{summary}\n{url}")

            # Save to database if model exists
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

        # Return in A2A format
        return JsonResponse({
            "status": "success",
            "type": "message",
            "message": reply_text,
            "conversation_id": conversation_id,
            "timestamp": timezone.now().isoformat(),
            "metadata": {
                "articles_count": len(articles),
                "query_used": query,
                "processed_at": timezone.now().isoformat()
            }
        })

    except Exception as e:
        print("A2A webhook error:", str(e))
        traceback.print_exc()
        
        return JsonResponse({
            "status": "error",
            "type": "error",
            "message": f"An error occurred while processing your request: {str(e)}",
            "timestamp": timezone.now().isoformat()
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"]) 
def legacy_webhook(request):
    """
    Legacy webhook endpoint for backward compatibility
    Keep this if you have existing integrations
    """
    return telex_webhook(request)
