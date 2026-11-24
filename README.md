# ProyectoPadel

Recomendador de palas de pádel: una encuesta corta, una recomendación personalizada y las mejores
ofertas de cada pala. La marca de la web es **palaideal**.

| Parte | Tecnología | Despliegue previsto |
|---|---|---|
| Frontend | Astro + Preact + TypeScript (web estática) | Vercel |
| Backend | FastAPI + Pydantic + SQLAlchemy + psycopg + Alembic | Render |
| Base de datos | PostgreSQL | Render |
| Tareas programadas | `python -m app.jobs daily/weekly/monthly` | Cron de Render |

## Estado

La web funciona entera **sin backend**: el catálogo es de ejemplo (`frontend/src/data/catalogo.ts`),
la recomendación se calcula en el navegador (`frontend/src/lib/recomendador.ts`) y las palas guardadas,
los avisos y el historial se guardan en el navegador. El acceso por correo sí necesita la API.

Pendiente en el backend: motor de recomendación, catálogo real (feeds de tiendas), envío de correos
(enlace de acceso y avisos de precio) y sincronizar lo guardado con la cuenta.

## Despliegue

- **Frontend (Vercel):** web estática; toda la configuración está en `vercel.json`, en la raíz del
  repositorio (`npm ci` y `npm run build` dentro de `frontend/`, salida `frontend/dist`, barra final en
  las URL, cabeceras de seguridad y caché).
  1. *Add New → Project* e importar el repositorio de GitHub.
  2. *Root Directory*: vacío (la raíz del repositorio). Vercel solo lee el `vercel.json` de esa carpeta;
     si se pone `frontend`, lo ignora.
  3. *Production Branch* (Settings → Git): `main`. Cada PR y `develop` generan una *preview*.
  4. *Node.js Version* (Settings → Build and Deployment): `24.x`, la misma que la CI. Con la raíz del
     repositorio como *Root Directory*, Vercel no lee el `engines` de `frontend/package.json`.
  5. Variables de entorno (opcionales):
     - `PUBLIC_API_URL`: URL del backend. Sin ella la web se publica sin acceso por correo.
     - `SITE_URL`: dominio propio (p. ej. `https://palaideal.es`). Sin ella, las canónicas usan el
       dominio `*.vercel.app` de producción del proyecto.
  - Solo se construye si el commit cambia algo en `frontend/` o en `vercel.json` (`ignoreCommand`).
- **Backend (Render):** servicio web con `uvicorn app.main:app` y una base PostgreSQL. Hay que definir
  `ENTORNO` (distinto de `local`), `DATABASE_URL` y `CORS_ORIGINS` con el dominio del frontend.
- La sesión viaja en una cookie `SameSite=Lax`: frontend y API deben compartir dominio (por ejemplo
  `palaideal.es` y `api.palaideal.es`) o la API debe servirse tras un *rewrite* del frontend.

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
| `/encuesta/` | Cuestionario (`?camino=primera\|cambio` salta el primer paso; `?editar=1` reabre las últimas respuestas) |
| `/recomendacion/` | Resultado del cuestionario (`?h=<id>` muestra una del historial) |
| `/palas/`, `/palas/<slug>/` | Catálogo (`?forma=`, `?precio=`, `?orden=`) y ficha de pala |
| `/ir/<oferta>/` | Salida a tienda: destino de todos los botones «Ir a la tienda» |
| `/guias/`, `/guias/<slug>/` | Guías |
| `/como-ganamos-dinero/` | Transparencia |
| `/legal/afiliacion/`, `/legal/aviso-legal/`, `/legal/privacidad/`, `/legal/cookies/` | Textos legales (provisionales) |
| `/acceso/`, `/acceso/verificar/` | Acceso por enlace al correo |
| `/cuenta/`, `/cuenta/palas-guardadas/`, `/cuenta/alertas/`, `/cuenta/historial/` | Área de cuenta |

## Flujo de trabajo

Gitflow con `main`, `develop`, `feature/*`, `release/*` y `hotfix/*`. Ver [docs/GITFLOW.md](docs/GITFLOW.md).
Agentes IA (`gitflow`, `code-reviewer`, `pr-reviewer`) en `.claude/agents/`, con su versión para Codex en
`.codex/agents/` generada por `scripts/sincronizar-agentes.py`.
