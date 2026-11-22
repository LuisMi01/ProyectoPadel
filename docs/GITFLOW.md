# Gitflow en ProyectoPadel

Guía para personas y para sus agentes IA (Claude Code y Codex). Si solo lees una sección, lee
[El ciclo de una feature](#el-ciclo-de-una-feature).

## Ramas

| Rama | Sale de | Se fusiona en | Para qué |
|---|---|---|---|
| `main` | — | — | Producción. Cada commit es una versión desplegada y lleva tag `vX.Y.Z`. |
| `develop` | `main` | — | Integración. Rama por defecto; lo que está aquí va en la próxima versión. |
| `feature/<tema>` | `develop` | `develop` | Funcionalidad nueva o cambio normal. |
| `release/X.Y.Z` | `develop` | `main` **y** `develop` | Congelar una versión: solo arreglos, versión y changelog. |
| `hotfix/X.Y.Z` | `main` | `main` **y** `develop` | Arreglo urgente en producción. |

- Nunca se hace commit directo en `main` ni en `develop`: todo entra por Pull Request.
- Nombres en minúsculas y con guiones: `feature/sesion-usuarios`, `hotfix/0.1.1`.
  Una rama como `WebBack` **no pasa** el check "Reglas del PR".

## El ciclo de una feature

```bash
git switch develop && git pull                     # 1. parte de develop actualizado
scripts/flow.sh feature start sesion-usuarios      # 2. crea feature/sesion-usuarios
# … commits pequeños en Conventional Commits …
scripts/flow.sh feature finish                     # 3. rebase sobre develop, push y PR a develop
```

4. **CI**: en el PR se ejecutan dos checks obligatorios:
   - **CI**: lint y tests del backend con PostgreSQL real, migraciones, build del frontend y
     sincronización de los agentes IA.
   - **Reglas del PR**: rama de origen/destino válida y título en Conventional Commits.
5. **Revisión**: otra persona del equipo revisa y aprueba (1 aprobación). Puede apoyarse en el agente
   `pr-reviewer` ("revisa el PR 12"). Quien abre el PR no se aprueba a sí mismo.
6. **Fusión**: con los dos checks en verde, la aprobación y las conversaciones resueltas, el autor pulsa
   **Squash and merge**. El título del PR será el mensaje del commit en `develop`; la rama se borra sola.

## Si un check falla

| Check | Qué significa | Cómo se arregla |
|---|---|---|
| Reglas del PR → *Rama no válida* | La rama no se llama `feature/…` (o va al destino equivocado). | Relanzar o cambiar el título **no sirve**. Renombra la rama y abre un PR nuevo (abajo). El resumen del job trae los comandos exactos. |
| Reglas del PR → *Título no válido* | El título no es `tipo(ámbito): resumen`. | Edita el título del PR; el check se relanza solo. |
| CI → backend | Lint, tests o migraciones. | Abre el job, lee el error y corrígelo en la rama. |
| CI → frontend | `astro check` o el build. | Ídem. |
| CI → Agentes IA sincronizados | Se editó un agente en `.claude/agents/` sin regenerar `.codex/agents/` (o al revés). | `python scripts/sincronizar-agentes.py` y commit. |

Renombrar una rama que no sigue gitflow (GitHub no deja cambiar la rama de un PR abierto):

```bash
git switch WebBack
git branch -m feature/web-palaideal
git push -u origin feature/web-palaideal
gh pr create --base develop --fill
gh pr close <número del PR antiguo> --delete-branch
```

## Commits (Conventional Commits)

```
<tipo>(<ámbito opcional>): <resumen en imperativo, minúsculas>
```

Tipos: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
Ámbitos habituales: `frontend`, `backend`, `db`, `jobs`, `ci`, `docs`.

Ejemplos: `feat(frontend): retomar encuesta guardada`, `fix(backend): caducidad de sesión en UTC`.

Hooks locales (validan el mensaje y bloquean el push directo a `main`/`develop`). Actívalos una vez
por clon:

```bash
git config core.hooksPath .githooks
```

## Releases y hotfixes

SemVer `MAJOR.MINOR.PATCH`. Una `release` sube MINOR (o MAJOR); un `hotfix` sube PATCH.

```bash
scripts/flow.sh release start 0.2.0    # release/0.2.0 desde develop → PR a main
scripts/flow.sh release finish         # fusiona en main + tag v0.2.0 + vuelta a develop
scripts/flow.sh hotfix start 0.2.1     # hotfix/0.2.1 desde main → PR a main
scripts/flow.sh hotfix finish          # fusiona en main + tag + vuelta a develop
```

Las releases y hotfixes se fusionan con **merge commit** (no squash) para conservar el historial en las
dos ramas. Tras `finish`: `ALLOW_PROTECTED_PUSH=1 git push origin main develop --follow-tags`
(requiere permisos de administrador mientras las ramas estén protegidas).

## Configuración de GitHub (una vez, la hace el propietario)

```bash
bash scripts/proteger-ramas.sh
```

Deja `develop` como rama por defecto, activa el borrado de ramas al fusionar y protege `main` y
`develop`: PR obligatorio con 1 aprobación, checks **CI** y **Reglas del PR** en verde, conversaciones
resueltas y sin force-push. Solo puede ejecutarlo un administrador del repositorio.

## Agentes IA

La fuente única son los archivos de `.claude/agents/`. Los de `.codex/agents/` se generan con
`python scripts/sincronizar-agentes.py`; no se editan a mano (la CI lo comprueba).

| Agente | Para qué |
|---|---|
| `gitflow` | Crear y cerrar ramas, redactar commits y abrir PRs. |
| `code-reviewer` | Revisar el diff local antes de abrir un PR. |
| `pr-reviewer` | Revisar un PR de GitHub (gitflow, CI, tests en un worktree y código). Publica solo si se le pide. |

Reglas para cualquier agente IA:

- Sigue este documento; no hace commit en `main`/`develop` ni usa `--no-verify` o `push --force`.
- Abre PRs, pero **no los aprueba ni los fusiona**: eso lo decide una persona.
- Antes de abrir un PR ejecuta lo mismo que la CI (ver `CLAUDE.md` / `AGENTS.md`, sección Comandos).
