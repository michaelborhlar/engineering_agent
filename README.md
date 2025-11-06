# AI Engineering News Agent

An AI-powered Django agent that fetches engineering & tech news, summarizes articles using the Hugging Face Inference API, and replies to Telex.im (A2A) webhook requests.  
This README is a single, copy-ready file you can paste into `README.md`.

---

## Table of Contents
- [What it is](#what-it-is)  
- [Features](#features)  
- [Tech stack](#tech-stack)  
- [Prerequisites](#prerequisites)  
- [Quick start (local)](#quick-start-local)  
- [Environment variables (.env)](#environment-variables-env)  
- [Project structure](#project-structure)  
- [How it works (flow)](#how-it-works-flow)  
- [API endpoints & testing (Postman / curl)](#api-endpoints--testing-postman--curl)  
- [Deploy to Railway (production)](#deploy-to-railway-production)  
- [Telex (A2A) integration](#telex-a2a-integration)  
- [Troubleshooting & tips](#troubleshooting--tips)  
- [Extending ideas](#extending-ideas)  
- [License & author](#license--author)

---

## What it is
This project provides a simple web service (Django) that:
1. Accepts webhook POSTs (from Telex or any client).  
2. Fetches engineering/tech news (NewsAPI or other provider).  
3. Summarizes each article using Hugging Face Inference API.  
4. Returns a Telex-friendly JSON payload (so Telex displays the summaries as messages).

---

## Features
- Fetch latest engineering/tech news
- Summarize articles via Hugging Face (free inference API token)
- Telex-compatible webhook responses: `reply_to` + `actions`
- Local development (SQLite) and Railway-ready (Postgres via `DATABASE_URL`)
- Health endpoint for uptime checks

---

## Tech stack
- Python 3.10+  
- Django  
- requests (HTTP)  
- Hugging Face Inference API (`facebook/bart-large-cnn` or similar)  
- NewsAPI.org (or alternative)  
- Railway for deployment

---

## Prerequisites
- Python 3.10+ installed  
- Git & GitHub account  
- Railway account (for deployment)  
- API keys:
  - `NEWS_API_KEY` — get at https://newsapi.org
  - `HF_API_KEY` — get at https://huggingface.co/settings/tokens

---

## Quick start (local)

```bash
# clone repo
git clone https://github.com/<your-username>/<repo>.git
cd <repo>

# create & activate venv
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows (PowerShell)
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt

# add .env in project root (see below)
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
DJANGO_SECRET_KEY=replace-with-a-secret
DEBUG=1
HF_API_KEY=hf_your_huggingface_token_here
NEWS_API_KEY=your_newsapi_key_here
ALLOWED_HOSTS=127.0.0.1,localhost
#Product tree
engineering_agent/
├─ agent/
│  ├─ views.py        # telex_webhook, health
│  ├─ utils.py        # fetch_engineering_news, summarize_with_hf
│  ├─ urls.py
│  └─ models.py       # optional Article model
├─ engineering_agent/
│  ├─ settings.py
│  └─ urls.py
├─ manage.py
├─ requirements.txt
├─ Procfile
└─ README.md
#Testing
GET /agent/health/
curl https://<your-app>.up.railway.app/agent/health/

POST /agent/webhook/
Content-Type: application/json
Body example:
{
  "messageId": "test1",
  "text": "engineering news"
}

python manage.py migrate
python manage.py collectstatic --noinput   # if using static files


