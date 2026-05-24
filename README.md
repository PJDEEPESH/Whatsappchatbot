# Gem - WhatsApp RAG Chatbot 

**Gem** is a multilingual WhatsApp chatbot that recommends events, bars, restaurants, cafés, clubs, cultural centers and communities in **Buenos Aires**. It uses a **RAG (Retrieval-Augmented Generation)** pipeline built on **OpenAI embeddings + Milvus vector search** for events, and **PostgreSQL keyword search** for businesses, all wrapped in a Twilio WhatsApp webhook.

---

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [How It Works (Request Flow)](#how-it-works-request-flow)
4. [Tech Stack](#tech-stack)
5. [Environment Variables](#environment-variables)
6. [Local Setup](#local-setup)
7. [Deployment](#deployment)
8. [Project Structure](#project-structure)
9. [Notes & Known Issues](#notes--known-issues)

---

## Features

- **WhatsApp-native chat** via Twilio (incoming + outgoing messages, typing indicators / blue ticks).
- **Multilingual** — understands and replies in English, Spanish, Portuguese, French, German, Italian, Russian, Arabic, Hebrew, Hindi, Telugu, Tamil, Chinese, Japanese, Korean and more (auto-detected per message).
- **AI intent analysis** with `gpt-4o-mini` — extracts:
  - `is_greeting`, `is_identity_question`, `wants_to_upload`, `is_out_of_scope`
  - `date_range` (today / tomorrow / this week / weekend / next week ...)
  - `target_mood` (romantic, chill, energetic, party, upscale...)
  - `social_context` (date, friends, solo, family, business)
  - `category` (event, bar, restaurant, cafe, club, theater, cultural_center, communities...)
  - `specific_keywords` + `inferred_keywords`
  - `user_language` (ISO 639-1 code)
- **RAG event retrieval** — Milvus vector search over an `events` collection using `text-embedding-3-small` embeddings, followed by an LLM filter/format pass.
- **Smart business search** — strict-first, loose-fallback keyword search over PostgreSQL `businesses` table with restricted-content filtering (women-only, 18+ etc. unless explicitly requested).
- **Onboarding flow** — captures user mood → name → age and stores in PostgreSQL, then enters `ready` state.
- **Personalised one-liners** — `✨ Just for you:` recommendation generated per result, age- and context-aware, in the user's language.
- **Recurring events handling** — events with a `recurring_day` are surfaced when their weekday falls inside the user's requested date range.
- **Expert fallback** — when no DB/Milvus result fits, an OpenAI "Yara expert" prompt produces a curated answer instead of failing.
- **Thread-pooled processing** — incoming webhook returns immediately; heavy work runs in a `ThreadPoolExecutor` so Twilio doesn't time out.
- **Connection pooled DB** — `psycopg2.pool.SimpleConnectionPool` (1–50 connections).

---

## Architecture

```
       WhatsApp user
            │
            ▼
     Twilio WhatsApp
            │  (POST /webhook)
            ▼
   ┌──────────────────────┐
   │   Flask app          │
   │   (twilioo.py)       │
   │                      │
   │  ThreadPoolExecutor  │──► send typing indicator (Twilio API)
   │        │             │
   │        ▼             │
   │  process_message     │
   │        │             │
   │        ├─► PostgreSQL ── users table (onboarding state)
   │        │
   │        ├─► OpenAI gpt-4o-mini ── intent analysis (JSON)
   │        │
   │        ├─► EVENT?  ──► OpenAI embeddings ──► Milvus search
   │        │                                       │
   │        │                                       ▼
   │        │                              gpt-4o-mini re-rank/filter
   │        │
   │        ├─► BUSINESS? ─► PostgreSQL businesses (strict → loose)
   │        │
   │        └─► FALLBACK ──► OpenAI "Yara expert" prompt
   │                            │
   │                            ▼
   │                Twilio send WhatsApp message(s)
   └──────────────────────┘
```

**Data stores**

| Store | Purpose |
|-------|---------|
| **PostgreSQL** | `users` (phone, name, age, conversation_step, last_mood) and `businesses` (name, description, category, location, ...) |
| **Milvus** (Zilliz Cloud or self-hosted) | `events` collection with `embedding` field (vector), `title`, `text` (JSON event payload), `metadata` (JSON) |

---

## How It Works (Request Flow)

1. **Twilio** posts the inbound WhatsApp message to `POST /webhook`.
2. Flask returns an empty TwiML response immediately and hands the work to a background thread (`process_message_thread`).
3. A **typing indicator** is sent to WhatsApp (also marks the message as read / blue ticks).
4. The user is looked up / created in PostgreSQL. If `conversation_step != 'ready'`, the **onboarding flow** runs (mood → name+age).
5. `analyze_user_intent()` calls OpenAI to produce a structured JSON describing intent, language, date range, mood, category and keywords.
6. Routing:
   - **Greeting / identity / out-of-scope / upload-intent** → canned multilingual reply.
   - **Event query** → `retrieve_events_direct()`:
     - Build an enhanced query string from user text + AI keywords/mood/dates.
     - Embed with `text-embedding-3-small`.
     - `COSINE` search top-25 in the Milvus `events` collection.
     - `llm_filter_events()` re-ranks with `gpt-4o-mini` and formats up to 6 results (preserving `recurring_day`).
   - **Business query** → `smart_search()` runs a strict SQL query first, falls back to a loose `OR`-joined query if it returns fewer than 3 results.
   - **Nothing matches** → `ask_chatgpt_expert_fallback()` answers as Yara, the Buenos Aires expert.
7. For each result, `generate_just_for_you()` adds a personalised one-liner; `translate_text()` localises copy where needed.
8. Twilio sends one outbound WhatsApp message per result (plus an optional closing message from `generate_closing_message()`).

---

## Tech Stack

- **Python 3.10.12** (see [runtime.txt](runtime.txt))
- **Flask 3.1** + **Gunicorn 23** (see [Procfile](Procfile))
- **Twilio 9.8** — WhatsApp messaging
- **OpenAI 2.8** — `gpt-4o-mini` (chat) + `text-embedding-3-small` (embeddings)
- **pymilvus 2.6** — vector search (Zilliz Cloud compatible)
- **psycopg2-binary 2.9** — PostgreSQL access with connection pooling
- **python-dotenv** — local `.env` loading

Full pinned list in [requirements.txt](requirements.txt).

---

## Environment Variables

Create a `.env` file in the project root with the following keys:

```env
# --- OpenAI ---
OPENAI_API_KEY=sk-...

# --- Twilio (WhatsApp) ---
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886   # your Twilio WhatsApp sender (sandbox or approved number)

# --- PostgreSQL ---
# Full URI: postgresql://user:password@host:port/dbname
DATABASE_URL=postgresql://user:password@host:5432/yara

# --- Milvus / Zilliz Cloud (vector DB for events RAG) ---
MILVUS_ENDPOINT=https://your-cluster.api.gcp-us-west1.zillizcloud.com
MILVUS_TOKEN=your_milvus_api_token
```

### `.env.example`

A safe template you can commit:

```env
OPENAI_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=
DATABASE_URL=
MILVUS_ENDPOINT=
MILVUS_TOKEN=
```

> Notes
> - `MILVUS_ENDPOINT` + `MILVUS_TOKEN` are **optional**. If missing or unreachable, event RAG is disabled but the bot still runs (business search + expert fallback work).
> - `TWILIO_WHATSAPP_NUMBER` must include the `whatsapp:` prefix.
> - The expected Milvus collection is named **`events`** with fields: `id`, `title`, `text` (JSON string of event), `metadata` (JSON string), `embedding` (float vector).

### Expected PostgreSQL tables

```sql
CREATE TABLE public.users (
  phone               TEXT PRIMARY KEY,
  name                TEXT,
  age                 TEXT,
  conversation_step   TEXT DEFAULT 'welcome',
  last_mood           TEXT
);

CREATE TABLE public.businesses (
  id           SERIAL PRIMARY KEY,
  name         TEXT,
  description  TEXT,
  category     TEXT,
  location     TEXT,
  image_url    TEXT,
  instagram_link TEXT
  -- add any other columns your data has
);
```

---

## Local Setup

```bash
# 1. Clone
git clone https://github.com/PJDEEPESH/Whatsappchatbot.git
cd Whatsappchatbot

# 2. Create venv (do NOT commit it)
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 3. Install deps
pip install -r requirements.txt

# 4. Create your .env (see above)

# 5. Run
gunicorn twilioo:app
# or for local dev:
python twilioo.py
```

### Exposing the webhook to Twilio

Twilio needs a public URL. Use **ngrok** locally:

```bash
ngrok http 8000
```

Then in the Twilio Console → WhatsApp Sandbox → set **"When a message comes in"** to:

```
https://<your-ngrok-id>.ngrok-free.app/webhook    (POST)
```

---

## Deployment

The repo ships with a [Procfile](Procfile) for **Heroku-style** platforms (Heroku, Render, Railway, Fly):

```
web: gunicorn twilioo:app
```

Steps:

1. Push the repo to your platform.
2. Set every variable from [Environment Variables](#environment-variables) in the platform's dashboard.
3. Point the Twilio WhatsApp webhook at `https://<your-app>/webhook`.

---

## Project Structure

```
Whatsappchatbot/
├── twilioo.py         # Flask app, Twilio webhook, AI + RAG + DB logic (active code at the bottom)
├── requirements.txt   # Pinned Python dependencies
├── runtime.txt        # Python version for PaaS buildpacks
├── Procfile           # `web: gunicorn twilioo:app`
├── env/               # ⚠️ committed virtualenv — should be deleted and gitignored
└── README.md
```

---

## Notes & Known Issues

- **`twilioo.py` is ~5000 lines** because earlier iterations of the code are kept commented out at the top. The **active code starts around line 3336**. Consider splitting it into modules (`ai.py`, `rag.py`, `db.py`, `twilio_io.py`, `app.py`) when you next refactor.
- **`env/` directory is a committed Python virtualenv.** Delete it and add a `.gitignore`:
  ```gitignore
  .env
  env/
  .venv/
  __pycache__/
  *.pyc
  ```
- The app is **Buenos Aires-specific** (Yara persona, hard-coded city context in prompts). Adapting to another city = editing the system prompts in `analyze_user_intent`, `ask_chatgpt_expert_fallback`, `generate_closing_message`, `generate_just_for_you`.
- Cost note: every inbound message triggers at least 1 chat completion (intent analysis) and, for event queries, 1 embedding + 1 more chat completion (LLM re-rank). Plan OpenAI quota accordingly.
