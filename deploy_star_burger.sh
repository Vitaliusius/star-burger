#!/bin/bash

set -e
echo "Обновление кода репозитория"
git pull

echo "Обновление зависимостей..."
cd /opt/star-burger/
source venv/bin/activate
pip install -r requirements.txt

echo "Сборка фронтенда"
cd /opt/star-burger/
npm ci --dev
./node_modules/.bin/parcel watch bundles-src/index.js --dist-dir bundles --public-url="./"

echo "Сборка статики..."
./venv/bin/python manage.py collectstatic --noinput

echo "Применение миграций..."
./venv/bin/python manage.py migrate --noinput

echo "Перезапуск Systemd"
sudo systemctl restart starburger
sudo systemctl reload nginx

echo "Деплой успешно завершен"
echo "Уведомление Rollbar о новом деплое..."

curl https://api.rollbar.com/api/1/deploy \
  -H "X-Rollbar-Access-Token: 9654fff7642249c0ace4d1d87c7ddc8f" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"environment": "production", "revision": "'$(git rev-parse HEAD)'", "local_username": "'$(whoami)'", "comment": "Автоматический деплой"}'
