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
.claude/    agentes: gitflow, code-reviewer.
```

Los cuatro diseños de referencia (portada, cuestionario, recomendación y ficha) están fuera del repo,
en `../Diseños/`. De ellos salen los valores de `frontend/src/styles/global.css`.

### Backend (`backend/app/`)

Ciclo de una petición: uvicorn → FastAPI (router) → Pydantic (`schemas.py`) → servicio (`services/`)
→ SQLAlchemy (`models/`) → psycopg → PostgreSQL.

- `api/routes/`: un archivo por grupo de la tabla *Peticiones* (recomendaciones, tienda, analítica,
  acceso, cuenta, internas). Solo validan y delegan.
- `services/`: casos de uso; coordinan dominio, adaptadores y BD. Lo no implementado lanza
  `core.errores.Pendiente` → HTTP 501.
- `domain/`: Python puro, sin FastAPI, Pydantic, SQLAlchemy ni otras capas de `app` (lo comprueba
  `tests/test_arquitectura.py`). `motor.py` es el **mismo algoritmo** que
  `frontend/src/lib/recomendador.ts`; `tests/test_motor.py` compara los dos con casos calculados en
  el frontend (`tests/datos/motor_casos.json`). Si cambias las reglas, cámbialas en los dos sitios,
  regenera los casos y sube `MOTOR_VERSION`. La recomendación la decide el navegador; el motor de
  Python sirve para pregenerar explicaciones. También: tipos (`modelos.py`), puertos
  (`puertos.py`), normalización de feeds, fichas de palas nuevas, enlaces, histórico de precios y
  enlace de afiliado.
- `adapters/`: catálogo en PostgreSQL y en el formato JSON del frontend, Claude (explicaciones),
  feeds por HTTP (CSV/JSON) y email (pendiente).
- `models/`: tablas de los esquemas `public` y `staging` (feeds sin normalizar).
- `semillas/`: catálogo de ejemplo de la web (mismos ids). `python -m app.semillas` lo carga en la BD.
- `jobs/`: crons `python -m app.jobs daily|weekly|monthly [--solo tarea]`. Cada ejecución queda en
  `job_run`; lo que ya salió bien en su periodo no se repite.
- La recomendación se calcula en el navegador y la API **no la recalcula**: `POST /recomendaciones`
  guarda las respuestas (`camino`, `exp`, `frec`, `estilo`, `edad`, `ppto`, con los valores de
  `lib/encuesta.ts`) y los `modelo_id` enseñados, y devuelve el id. La API no recibe nunca datos de
  salud: `mol`, `salud` o cualquier campo de más dan 422.
- La explicación se pide con ese id: entera (`GET /recomendaciones/{id}/explicacion`) o según la IA
  la escribe (`.../explicacion/flujo`, Server-Sent Events `texto` y `fin`). Con caché, tope diario y
  plantilla si no hay clave (`ANTHROPIC_API_KEY`) o el texto no vale.
- `GET /internas/catalogo` devuelve el catálogo en el formato de `frontend/src/data/catalogo.ts`
  (protegido con `X-Token-Interno` si hay `TOKEN_INTERNO`).
- `GET /tienda/{oferta_id}` registra el clic y redirige con el enlace de afiliado de la tienda; el id
  del clic viaja como SubID.
- Acceso sin contraseña: `token_acceso` (enlace por email) → `sesion` en cookie httpOnly. Solo se guardan hashes.

### Frontend (`frontend/src/`)

La web funciona entera sin backend: el catálogo es de ejemplo, la recomendación se calcula en el
navegador y lo que el usuario guarda vive en `localStorage`. Si hay API (`PUBLIC_API_URL`), además
registra cada recomendación (sin molestias), pinta la explicación con IA y los botones «Ir a la
tienda» pasan por `GET /tienda/{oferta}` para contar el clic.

- `lib/rutas.ts`: **única** fuente de URLs. Enlaza siempre con `rutas.*`.
- `lib/sitio.ts`: nombre de marca y datos legales del titular (pendientes de rellenar).
- `lib/encuesta.ts`: máquina de estados del cuestionario (pura, sin DOM) y su persistencia.
- `lib/recomendador.ts`: motor de recomendación (función pura). Es el que decide; el backend tiene
  el mismo en `app/domain/motor.py` y un test comprueba que dan lo mismo.
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
uv run python -m app.semillas                          # catálogo de ejemplo en la BD
uv run python -m uvicorn app.main:app --reload         # API en :8000 (docs en /docs)
uv run python -m pytest -q && uv run ruff check .      # tests + lint (los de BD usan padel_test)
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
