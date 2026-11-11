# ProyectoPadel — guía para agentes

Recomendador de palas de pádel: encuesta → recomendación → enlace a tienda (afiliación).
Idioma del código, comentarios, commits y UI: **español**.

## Estructura

```
frontend/   Astro + Preact + TypeScript. Web estática servida por Cloudflare Workers (wrangler.jsonc).
backend/    Python 3.13 + FastAPI + Pydantic + SQLAlchemy 2 + psycopg 3 + Alembic. Railway (Ámsterdam).
docs/       GITFLOW.md y documentación.
scripts/    flow.sh (gitflow sin dependencias).
.claude/    agentes: gitflow, code-reviewer.
```

### Backend (`backend/app/`)

Ciclo de una petición: uvicorn → FastAPI (router) → Pydantic (`schemas.py`) → servicio (`services/`)
→ SQLAlchemy (`models/`) → psycopg → PostgreSQL.

- `api/routes/`: un archivo por grupo de la tabla *Peticiones* (recomendaciones, tienda, analítica,
  acceso, cuenta, internas). Solo validan y delegan.
- `services/`: lógica de negocio. Lo no implementado lanza `core.errores.Pendiente` → HTTP 501.
- `models/`: tablas del modelo relacional de Figma (catálogo, usuarios, recomendaciones).
- `jobs/`: crons `python -m app.jobs daily|weekly|monthly [--solo tarea]`.
- Acceso sin contraseña: `token_acceso` (enlace por email) → `sesion` en cookie httpOnly. Solo se guardan hashes.

### Frontend (`frontend/src/`)

- `lib/rutas.ts`: **única** fuente de URLs. Enlaza siempre con `rutas.*`.
- `lib/encuesta.ts`: máquina de estados del flujo de la encuesta (pura, sin DOM).
- `lib/api.ts`: cliente de la API (`PUBLIC_API_URL`).
- `components/*.tsx`: islas Preact (Encuesta, Recomendacion).
- `pages/`: inicio, encuesta, recomendacion, palas/[slug], guias/[slug], acceso, cuenta/*, 404.

## Comandos

```bash
docker compose up -d                                   # PostgreSQL local
cd backend && uv sync && cp .env.example .env
uv run alembic upgrade head                            # aplicar migraciones
uv run python -m uvicorn app.main:app --reload         # API en :8000 (docs en /docs)
uv run python -m pytest -q && uv run ruff check .      # tests + lint
uv run alembic revision --autogenerate -m "..."        # tras cambiar models/

cd frontend && npm install && npm run dev              # web en :4321
npm run build                                          # astro check + build
```

En este equipo Windows, los .exe de `.venv/Scripts` (pytest, uvicorn) pueden estar bloqueados por
Control de aplicaciones: usa `uv run python -m <herramienta>`.

## Reglas

- Gitflow obligatorio (docs/GITFLOW.md): nada directo a `main`/`develop`; Conventional Commits.
- Cambios en `models/` ⇒ migración Alembic en el mismo PR.
- Nunca guardar datos de salud, tokens en claro ni secretos en el repo o en variables `PUBLIC_*`.
- Antes de dar algo por terminado: lint + tests backend y `npm run build` frontend.
