.PHONY: dev-backend dev-frontend dev install migrate seed

# Start backend dev server
dev-backend:
	cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Start frontend dev server
dev-frontend:
	cd frontend && npm run dev

# Install all dependencies
install:
	cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt
	cd frontend && npm install

# Install spaCy + German model (large download ~600MB, run once)
install-nlp:
	cd backend && .venv/bin/pip install "spacy>=3.8,<4.0" && .venv/bin/python -m spacy download de_core_news_lg

# Run database migrations
migrate:
	cd backend && PYTHONPATH=. .venv/bin/alembic upgrade head

# Create a new migration (usage: make migration name="add_something")
migration:
	cd backend && PYTHONPATH=. .venv/bin/alembic revision --autogenerate -m "$(name)"

# Check backend imports
check-backend:
	cd backend && .venv/bin/python -c "from app.main import app; print('OK')"

# Type-check frontend
check-frontend:
	cd frontend && npx tsc --noEmit
