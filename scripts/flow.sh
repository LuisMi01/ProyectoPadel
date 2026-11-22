#!/usr/bin/env bash
# Gitflow ligero sin dependencias (ver docs/GITFLOW.md).
#   scripts/flow.sh feature start <nombre> | feature finish
#   scripts/flow.sh release start <X.Y.Z>  | release finish
#   scripts/flow.sh hotfix  start <X.Y.Z>  | hotfix  finish
set -euo pipefail

MAIN=main
DEVELOP=develop

die() { echo "✗ $*" >&2; exit 1; }
rama_actual() { git rev-parse --abbrev-ref HEAD; }
hay_remoto() { git remote get-url origin >/dev/null 2>&1; }
limpio() { git diff --quiet && git diff --cached --quiet || die "Hay cambios sin commitear."; }
actualizar() {
  git switch "$1" --quiet
  if hay_remoto; then git pull --ff-only --quiet origin "$1"; fi
}
semver() { [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "Versión no válida: '$1' (usa X.Y.Z)"; }

tipo="${1:-}"; accion="${2:-}"; arg="${3:-}"

case "$tipo:$accion" in
  feature:start)
    [[ "$arg" =~ ^[a-z0-9][a-z0-9-]*$ ]] || die "Nombre en minúsculas y guiones: feature start encuesta-retomar"
    limpio; actualizar "$DEVELOP"
    git switch -c "feature/$arg"
    ;;
  feature:finish)
    rama=$(rama_actual); [[ "$rama" == feature/* ]] || die "No estás en una rama feature/*"
    limpio; actualizar "$DEVELOP"; git switch "$rama" --quiet
    git rebase "$DEVELOP"
    if hay_remoto; then
      git push -u origin "$rama" --force-with-lease
      echo "✓ Abre el PR: $rama → $DEVELOP  (gh pr create --base $DEVELOP --fill)"
    else
      echo "✓ Rebase hecho. Sin remoto 'origin': fusiona con 'git switch $DEVELOP && git merge --squash $rama'"
    fi
    ;;
  release:start|hotfix:start)
    semver "$arg"; limpio
    base=$([[ "$tipo" == release ]] && echo "$DEVELOP" || echo "$MAIN")
    actualizar "$base"
    git switch -c "$tipo/$arg"
    echo "✓ $tipo/$arg creada desde $base. Actualiza versión/changelog y haz commit."
    ;;
  release:finish|hotfix:finish)
    rama=$(rama_actual); [[ "$rama" == "$tipo"/* ]] || die "No estás en una rama $tipo/*"
    version="${rama#*/}"; semver "$version"; limpio
    actualizar "$MAIN"
    git merge --no-ff "$rama" -m "chore($tipo): $version"
    git tag -a "v$version" -m "v$version"
    actualizar "$DEVELOP"
    git merge --no-ff "$rama" -m "chore($tipo): $version en $DEVELOP"
    git branch -d "$rama"
    echo "✓ v$version en $MAIN y $DEVELOP. Publica con: git push origin $MAIN $DEVELOP --follow-tags"
    ;;
  *)
    sed -n '2,6p' "$0"; exit 1
    ;;
esac
