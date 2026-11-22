# ProyectoPadel — guía para agentes

Recomendador de palas de pádel: encuesta → recomendación → enlace a tienda (afiliación).
La marca de cara al público es **palaideal** (`frontend/src/lib/sitio.ts`).
Idioma del código, comentarios, commits y UI: **español**.

## Estructura

```
frontend/   Astro + Preact + TypeScript. Web estática (dist/). Despliegue previsto: Vercel (vercel.json).
            wrangler.jsonc es la configuración anterior para Cloudflare Workers.
backend/    Python 3.13 + FastAPI + Pydantic + SQLAlchemy 2 + psycopg 3 + Alembic. Despliegue previsto: Render.
docs/       GITFLOW.md y documentación.
scripts/    flow.sh (gitflow sin dependencias).
.claude/   agentes de Claude Code (gitflow, code-reviewer, pr-reviewer): fuente única.
.codex/    los mismos agentes para Codex, generados con scripts/sincronizar-agentes.py.
```

Los cuatro diseños de referencia (portada, cuestionario, recomendación y ficha) están fuera del repo,
en `../Diseños/`. De ellos salen los valores de `frontend/src/styles/global.css`.

### Backend (`backend/app/`)

Ciclo de una petición: uvicorn → FastAPI (router) → Pydantic (`schemas.py`) → servicio (`services/`)
→ SQLAlchemy (`models/`) → psycopg → PostgreSQL.

- `api/routes/`: un archivo por grupo de la tabla *Peticiones* (recomendaciones, tienda, analítica,
  acceso, cuenta, internas). Solo validan y delegan.
- `services/`: lógica de negocio. Lo no implementado lanza `core.errores.Pendiente` → HTTP 501.
- `models/`: tablas en dos esquemas de PostgreSQL (docs/BASE_DE_DATOS.md): `public` (catálogo,
  usuarios, recomendaciones, `vocab_map`) y `staging` (catálogos de tiendas en bruto: `staging.py`).
- `jobs/`: crons `python -m app.jobs daily|weekly|monthly [--solo tarea]`.
- Acceso sin contraseña (docs/ACCESO.md): `token_acceso` (enlace por correo) → `sesion` en cookie
  httpOnly. Crear cuenta e iniciar sesión son el mismo paso. Solo se guardan hashes. Correo por SMTP
  (`core/correo.py`); en local se escribe en la terminal.

### Frontend (`frontend/src/`)

La web funciona entera sin backend: el catálogo es de ejemplo, la recomendación se calcula en el
navegador y lo que el usuario guarda vive en `localStorage`. Solo el acceso por correo usa la API.

- `lib/rutas.ts`: **única** fuente de URLs. Enlaza siempre con `rutas.*`.
- `lib/sitio.ts`: nombre de marca y datos legales del titular (pendientes de rellenar).
- `lib/encuesta.ts`: máquina de estados del cuestionario (pura, sin DOM) y su persistencia.
- `lib/recomendador.ts`: motor de recomendación **provisional** (función pura). Se sustituirá por
  `POST /recomendaciones` cuando el backend lo implemente.
- `lib/catalogo.ts` + `data/catalogo.ts`: tipos y catálogo **de ejemplo** (marcas, tiendas y precios
  ficticios) mientras no exista `GET /internas/catalogo`. Los `id` son los `modelo_id`/`oferta_id` de la API.
- `lib/cuenta.ts`: palas guardadas, avisos e historial en `localStorage`; sesión contra la API.
- `lib/api.ts`: cliente de la API. Sin `PUBLIC_API_URL` en producción, la API se da por no disponible.
- `data/guias.ts`, `data/legal.ts`: contenido en bloques tipados (los textos legales son provisionales).
- `components/*.tsx`: islas Preact (Encuesta, Recomendacion, Cuenta, AvisoPrecio, GuardarPala,
  FormularioAcceso, VerificarAcceso) y piezas que también se pintan en estático (Icono, dibujos, PalaMini).
- `styles/`: `global.css` (tokens y piezas comunes) y una hoja por isla grande.
- `pages/`: portada, encuesta, recomendacion, palas (índice y ficha), ir/[oferta] (salida a tienda),
  guias, como-ganamos-dinero, legal/[slug], acceso, cuenta/*, 404.

Las molestias físicas son un dato de salud: solo viven en `sessionStorage` y nunca se escriben en
`localStorage`, en el historial ni se envían a la API.

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
  Ramas `feature/<tema>`; el PR necesita los checks **CI** y **Reglas del PR** y 1 aprobación humana.
  Un agente puede abrir PRs, pero nunca los aprueba ni los fusiona.
- Los agentes se editan solo en `.claude/agents/`; después `python scripts/sincronizar-agentes.py`.
- Cambios en `models/` ⇒ migración Alembic en el mismo PR.
- Nunca guardar datos de salud, tokens en claro ni secretos en el repo o en variables `PUBLIC_*`.
- Antes de dar algo por terminado: lint + tests backend y `npm run build` frontend.
