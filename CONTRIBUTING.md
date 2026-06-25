# Contributing

Thanks for your interest in contributing to the Deutsch Learning App!

## Getting Started

1. Fork the repo and clone your fork
2. Follow the setup instructions in [README.md](README.md)
3. Create a branch for your change: `git checkout -b feature/your-feature-name`

## Project Structure

- `backend/` — FastAPI Python backend
- `frontend/` — Next.js frontend
- All API endpoints are in `backend/app/routers/`
- All frontend pages are in `frontend/app/`

## Making Changes

**Backend changes:**
- The server auto-reloads on file save (uvicorn `--reload`)
- Add new endpoints in `backend/app/routers/`
- Add new database tables in `backend/app/models.py` + create an Alembic migration

**Frontend changes:**
- The server auto-reloads on file save (Next.js HMR)
- Add new pages in `frontend/app/`
- The typed API client is in `frontend/lib/api.ts` — add new API calls there

## Running Checks Before Submitting

```bash
# Type-check the frontend
cd frontend && npx tsc --noEmit

# Check backend imports are healthy
cd backend && python -c "from app.main import app; print('OK')"
```

## Submitting a Pull Request

1. Make sure both checks above pass
2. Keep PRs focused — one feature or fix per PR
3. Write a clear PR description explaining what changed and why
4. Open the PR against the `main` branch

## What's Most Needed

Check the roadmap in the README for features not yet built:
- Sentence builder exercise (drag-and-drop with @dnd-kit)
- Achievement toast animations (Framer Motion)
- Progress page with per-document charts
- YouTube transcript import
- Deployment setup (Vercel + Railway)

## Questions

Open a GitHub Issue if you're unsure about anything before starting work.
