# Networking Copilot - Docker Setup

This repository now includes a Docker Compose setup that runs the backend, frontend, and Redis together.

## Prerequisites

- Docker 24+
- Docker Compose 2+
- A copy of `agents/networking/.env` populated with your API keys (see `agents/networking/.env.example`).

## Quick Start

```bash
docker compose build
docker compose up
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Redis: localhost:6379

Environment variables:
- `agents/networking/.env` should contain your OpenAI, BrightData, and other required keys.
- `CORS_ALLOW_ORIGINS` is set in `docker-compose.yml` to allow `http://localhost:3000` and the internal `frontend` hostname.

To stop:
```bash
docker compose down
```

To rebuild after code changes:
```bash
docker compose build frontend backend
```

## Notes
- The Next.js frontend is built in production mode and served with `npm run start`.
- The backend uses `uv` to install dependencies from `pyproject.toml`/`uv.lock` and runs `uvicorn`.
- Redis persists only in the running container (no external volume configured). Add a volume if you need persistence across restarts.
