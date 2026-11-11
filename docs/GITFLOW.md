# Gitflow en ProyectoPadel

## Ramas

| Rama | Sale de | Se fusiona en | Para qué |
|---|---|---|---|
| `main` | — | — | Producción. Cada commit es una versión desplegada y lleva tag `vX.Y.Z`. |
| `develop` | `main` | — | Integración. Lo que está aquí va en la próxima versión. |
| `feature/<tema>` | `develop` | `develop` | Funcionalidad nueva o cambio normal. |
| `release/X.Y.Z` | `develop` | `main` **y** `develop` | Congelar una versión: solo arreglos, versión y changelog. |
| `hotfix/X.Y.Z` | `main` | `main` **y** `develop` | Arreglo urgente en producción. |

- Nunca se hace commit directo en `main` ni en `develop`: todo entra por Pull Request.
- Nombres de rama en minúsculas y con guiones: `feature/encuesta-retomar`, `hotfix/0.1.1`.
- Al cerrar una `feature` se borra la rama.

## Commits (Conventional Commits)

```
<tipo>(<ámbito opcional>): <resumen en imperativo, minúsculas>
```

Tipos: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
Ámbitos habituales: `frontend`, `backend`, `db`, `jobs`, `ci`.

Ejemplos: `feat(frontend): retomar encuesta guardada`, `fix(backend): caducidad de sesión en UTC`.

El hook `.githooks/commit-msg` valida el formato. Actívalo una vez por clon:

```bash
git config core.hooksPath .githooks
```

## Versionado

SemVer `MAJOR.MINOR.PATCH`. Una `release` sube MINOR (o MAJOR); un `hotfix` sube PATCH.

## Comandos (`scripts/flow.sh`)

No hace falta instalar git-flow: el script cubre el ciclo completo y funciona en Git Bash.

```bash
scripts/flow.sh feature start encuesta-retomar   # crea feature/encuesta-retomar desde develop
scripts/flow.sh feature finish                   # rebase sobre develop y push; abre el PR a develop
scripts/flow.sh release start 0.2.0              # crea release/0.2.0 desde develop
scripts/flow.sh release finish                   # fusiona en main + tag v0.2.0 + vuelta a develop
scripts/flow.sh hotfix start 0.2.1               # crea hotfix/0.2.1 desde main
scripts/flow.sh hotfix finish                    # fusiona en main + tag + vuelta a develop
```

`feature finish` no fusiona en local: la integración en `develop` es siempre por PR, con CI en verde y
revisión (humana o del agente `code-reviewer`). `release finish` y `hotfix finish` sí fusionan en local
porque deben llegar a dos ramas a la vez; después se hace `git push --follow-tags` de ambas.

## Pull Requests

- `feature/*` → `develop`. `release/*` y `hotfix/*` → `main` (y luego a `develop`).
- CI (`.github/workflows/ci.yml`) debe pasar: ruff + pytest en backend, `astro check` + build en frontend,
  y nombre de rama válido.
- Rellena la plantilla del PR. Squash merge en features; merge commit en release/hotfix.

## Protección de ramas (configurar en GitHub)

En *Settings → Branches* para `main` y `develop`: exigir PR, exigir el check `CI`, prohibir force-push.

## Agentes IA

En `.claude/agents/` hay dos agentes de Claude Code que aplican estas reglas:

- **gitflow**: crea y cierra ramas, redacta commits convencionales y prepara PRs.
- **code-reviewer**: revisa el diff contra las convenciones del proyecto y ejecuta lint y tests.
