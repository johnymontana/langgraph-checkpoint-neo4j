.PHONY: install install-backend install-frontend backend frontend

# Install all dependencies
install: install-backend install-frontend

# Install backend dependencies
install-backend:
	cd demo/backend && uv sync

# Install frontend dependencies
install-frontend:
	cd demo/frontend && npm install

# Run backend server
backend:
	cd demo/backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run frontend dev server
frontend:
	cd demo/frontend && npm run dev
