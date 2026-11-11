# ProyectoPadel

Recomendador de palas de pádel: una encuesta corta, una recomendación personalizada y las mejores
ofertas de cada pala.

| Parte | Tecnología | Despliegue |
|---|---|---|
| Frontend | Astro + Preact + TypeScript | Cloudflare Workers |
| Backend | FastAPI + Pydantic + SQLAlchemy + psycopg + Alembic | Railway |
| Base de datos | PostgreSQL | Railway (Ámsterdam) |
| Tareas programadas | `python -m app.jobs daily/weekly/monthly` | Railway cron |

## Arranque rápido

```bash
git config core.hooksPath .githooks      # hooks de gitflow (una vez por clon)
docker compose up -d                     # PostgreSQL local

cd backend
uv sync
cp .env.example .env
uv run alembic upgrade head
uv run python -m uvicorn app.main:app --reload   # http://localhost:8000/docs

cd ../frontend
npm install
cp .env.example .env
npm run dev                              # http://localhost:4321
```

## Mapa de páginas

| Ruta | Página |
|---|---|
| `/` | Portada |
| `/encuesta/` | Elegir camino y encuesta (`?camino=primera\|cambiar`) |
| `/recomendacion/` | Resultado de la encuesta |
| `/palas/`, `/palas/<slug>/` | Catálogo y ficha de pala |
| `/guias/`, `/guias/<slug>/` | Guías |
| `/acceso/`, `/acceso/verificar/` | Acceso por enlace al email |
| `/cuenta/`, `/cuenta/palas-guardadas/`, `/cuenta/alertas/`, `/cuenta/historial/` | Área de cuenta |

## Flujo de trabajo

Gitflow con `main`, `develop`, `feature/*`, `release/*` y `hotfix/*`. Ver [docs/GITFLOW.md](docs/GITFLOW.md).
Los agentes de Claude Code `gitflow` y `code-reviewer` están en `.claude/agents/`.
