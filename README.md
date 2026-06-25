# Deutsch Learning App

A German language learning app that transforms content **you personally choose** — PDFs, YouTube transcripts, movie subtitles, articles — into a Duolingo-style gamified learning experience.

Instead of generic textbook sentences, you learn vocabulary and grammar from real material that interests you. The AI explains **why** each grammar structure is used, not just what it is.

---

## Features

- **Upload anything** — PDF, SRT subtitles, plain text
- **AI vocabulary analysis** — translations, gender, CEFR level (A1–C2), example sentences
- **Grammar WHY explanations** — modal verbs, um…zu, separable verbs, cases, subordinate clauses, and more
- **Exercises generated from your content** — fill-in-the-blank, multiple choice, translation
- **Spaced repetition flashcards** — SM-2 algorithm (Again / Hard / Good / Easy)
- **Gamification** — XP, levels, streaks, 11 achievements

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 (App Router), Tailwind CSS, Shadcn/UI, Framer Motion |
| Backend | FastAPI (Python 3.13), async SQLAlchemy 2.0 |
| Database | Supabase (PostgreSQL) |
| AI | GPT-4o (grammar + vocabulary), GPT-4o-mini (exercises) |
| NLP | spaCy `de_core_news_lg` (German model) |
| Spaced Repetition | SM-2 algorithm (custom Python) |

---

## Project Structure

```
Deutsch_Learning_App/
├── backend/          # FastAPI Python backend
│   ├── app/
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── routers/         # API endpoints
│   │   ├── services/
│   │   │   ├── ai/          # GPT-4o integration
│   │   │   ├── extraction/  # PDF + text parsing
│   │   │   ├── nlp/         # spaCy processing
│   │   │   ├── spaced_repetition/  # SM-2
│   │   │   └── gamification/
│   │   └── tasks/           # Background document processing
│   ├── alembic/             # Database migrations
│   ├── requirements.txt
│   └── requirements-nlp.txt
│
└── frontend/         # Next.js frontend
    ├── app/
    │   ├── dashboard/
    │   ├── upload/
    │   ├── documents/[id]/
    │   │   ├── exercises/   # Exercise hub + practice session
    │   │   └── flashcards/  # SM-2 flashcard review
    │   └── page.tsx         # Landing page
    └── lib/
        └── api.ts           # Typed API client
```

---

## Getting Started

> **Every time you work on the app** you need two terminals running — one for the backend, one for the frontend. See [Daily Development](#daily-development) below if you've already set everything up.

### Prerequisites

- Python 3.13
- Node.js 18+
- A [Supabase](https://supabase.com) project (free tier works)
- An [OpenAI](https://platform.openai.com) API key

### 1. Clone the repo

```bash
git clone https://github.com/arhs93/deutsch-learning-app.git
cd deutsch-learning-app
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install spaCy + German model (large download ~600MB, one-time only)
pip install "spacy>=3.8,<4.0"
python -m spacy download de_core_news_lg

# Copy and fill in environment variables
cp .env.example .env
# Edit .env with your Supabase and OpenAI credentials

# Run database migrations (one-time only)
PYTHONPATH=. .venv/bin/alembic upgrade head

# Start the backend (Terminal 1)
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend setup

```bash
cd frontend

npm install

# Copy and fill in environment variables
cp .env.local.example .env.local
# Edit .env.local with your Supabase and API URL

# Start the frontend (Terminal 2)
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Daily Development

Once set up, this is all you need each time you want to run the app:

**Terminal 1 — backend:**
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — frontend:**
```bash
cd frontend
npm run dev
```

Both must be running at the same time. Your data is stored in Supabase (cloud) so it persists between sessions.

---

## Environment Variables

### Backend (`backend/.env`)

See `backend/.env.example` for all required variables.

| Variable | Description |
|---|---|
| `DATABASE_URL` | Supabase PostgreSQL connection string |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anonymous key |
| `OPENAI_API_KEY` | OpenAI API key |
| `ENVIRONMENT` | `development` or `production` |

### Frontend (`frontend/.env.local`)

See `frontend/.env.local.example` for all required variables.

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key |
| `NEXT_PUBLIC_API_URL` | Backend URL (default: `http://localhost:8000`) |

---

## API Overview

All endpoints are prefixed with `/api/v1`.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/documents/upload` | Upload a document for processing |
| GET | `/documents` | List user's documents |
| GET | `/documents/{id}/vocabulary` | Get extracted vocabulary |
| GET | `/documents/{id}/grammar` | Get grammar patterns with WHY explanations |
| GET | `/exercises` | Get exercises for a document |
| POST | `/exercises/attempt` | Submit an answer, earn XP |
| GET | `/flashcards/due` | Get SM-2 due flashcards |
| POST | `/flashcards/{id}/review` | Rate a flashcard (0–5) |
| GET | `/progress` | User level, XP, streak |
| GET | `/achievements` | All achievements with earned status |

---

## Document Processing Pipeline

1. Upload file → stored on disk, `Document` record created
2. Background task extracts text (pdfplumber for PDF, cleaner for SRT/TXT)
3. spaCy tokenises and filters vocabulary candidates
4. GPT-4o enriches vocabulary (translation, gender, CEFR level) — runs in parallel
5. GPT-4o detects grammar patterns with WHY explanations — runs in parallel with vocab
6. GPT-4o-mini generates exercises in batches of 10 — runs concurrently
7. Everything saved to Supabase; document status → `ready`

---

## Roadmap

- [ ] Sentence builder (drag-and-drop word ordering)
- [ ] Reading comprehension exercises
- [ ] Achievement toast animations (Framer Motion)
- [ ] Progress page with per-document charts
- [ ] YouTube transcript import
- [ ] Vercel + Railway deployment
