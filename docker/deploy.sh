#!/bin/sh
set -eu
cd "$(dirname "$0")"

if [ -n "${PULL:-}" ]; then docker compose pull backend frontend caddy; else docker compose build; fi # PULL=1 for prod
docker compose run --rm backend sh -c "python manage.py migrate --noinput && python manage.py invalidate all && python manage.py collectstatic --noinput && python manage.py gen_schema"
if [ -n "$(docker compose ps -q backend)" ]; then docker rollout backend; else docker compose up -d backend; fi
docker compose run --rm --no-deps frontend
docker compose up -d --no-deps worker caddy
docker image prune -f
