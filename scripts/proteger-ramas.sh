#!/usr/bin/env bash
# Configura GitHub para el gitflow de docs/GITFLOW.md. Lo ejecuta UNA VEZ un administrador del
# repositorio (el propietario), con `gh` autenticado:
#
#   bash scripts/proteger-ramas.sh                 # usa el repositorio de 'origin'
#   bash scripts/proteger-ramas.sh dueño/repo
#
# Es idempotente: se puede volver a ejecutar para restaurar la configuración.
set -euo pipefail

REPO="${1:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
echo "Repositorio: $REPO"

if [[ "$(gh api "repos/$REPO" --jq .permissions.admin)" != "true" ]]; then
  echo "✗ Tu cuenta no es administradora de $REPO. Pídeselo al propietario." >&2
  exit 1
fi

# 1. Ajustes del repositorio: develop por defecto, squash para features, borrar ramas al fusionar.
gh api -X PATCH "repos/$REPO" --silent \
  -f default_branch=develop \
  -F allow_squash_merge=true \
  -F allow_merge_commit=true \
  -F allow_rebase_merge=false \
  -F delete_branch_on_merge=true \
  -F allow_update_branch=true \
  -f squash_merge_commit_title=PR_TITLE \
  -f squash_merge_commit_message=PR_BODY
echo "✓ Ajustes: develop por defecto, squash/merge permitidos, ramas borradas al fusionar"

# 2. Protección de main y develop.
#    - Exige PR con 1 aprobación (se descarta si llegan commits nuevos) y conversaciones resueltas.
#    - Exige los checks "CI" (tests y build) y "Reglas del PR" (rama y título).
#    - Sin force-push ni borrado. Los administradores pueden saltarse las reglas en una urgencia.
proteger() {
  gh api -X PUT "repos/$REPO/branches/$1/protection" --silent --input - <<'EOF'
{
  "required_status_checks": { "strict": false, "contexts": ["CI", "Reglas del PR"] },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false
  },
  "required_conversation_resolution": true,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
  echo "✓ $1 protegida"
}

proteger main
proteger develop

echo
echo "Listo. Comprueba en https://github.com/$REPO/settings/branches"
