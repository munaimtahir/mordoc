# Setup.md — local dev

## Prereqs
- Docker + Docker Compose

## Start
1) Copy env files
- backend: `cp backend/.env.example backend/.env`
- frontend: `cp frontend/.env.example frontend/.env`

2) Run
- `docker compose up --build`

3) URLs
- Frontend: http://localhost:5173
- Backend health: http://localhost:8000/api/health/

## First run notes
- Parsing/export run as background tasks via Celery.
- In dev, they run in the worker container.
