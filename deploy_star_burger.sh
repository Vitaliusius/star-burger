#!/bin/bash
set -e

echo " Pulling changes from Git "
git pull origin main

echo " Building and starting Docker containers "
docker compose -f docker-compose.prod.yaml up -d --build

echo " Running Django Migrations "
docker compose -f docker-compose.prod.yaml exec -T backend python manage.py migrate --no-input

echo " Collecting Static Files "
docker compose -f docker-compose.prod.yaml exec -T backend python manage.py collectstatic --no-input

echo " Reloading Nginx "
sudo systemctl reload nginx

echo " Deployment finished "