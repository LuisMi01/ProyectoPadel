## Qué cambia

<!-- Resumen en 1-3 frases. Enlaza la tarea si existe. -->

## Tipo

- [ ] feature → develop
- [ ] release → main
- [ ] hotfix → main

## Cómo probarlo

<!-- Pasos o comandos. -->

## Checklist

- [ ] Título del PR en formato Conventional Commits
- [ ] `uv run ruff check . && uv run pytest` (backend) en verde
- [ ] `npm run build` (frontend) en verde
- [ ] Si cambian modelos: migración Alembic nueva incluida
- [ ] Sin secretos ni datos de salud en código, logs o base de datos
