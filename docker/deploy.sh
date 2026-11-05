#!/bin/sh
set -eu
cd "$(dirname "$0")"

docker compose build
docker compose run --rm backend sh -c "python manage.py migrate --noinput && python manage.py invalidate all && python manage.py collectstatic --noinput"
if [ -n "$(docker compose ps -q backend)" ]; then docker rollout backend; else docker compose up -d backend; fi
docker compose run --rm --no-deps frontend
docker compose up -d --no-deps worker caddy
docker image prune -f
