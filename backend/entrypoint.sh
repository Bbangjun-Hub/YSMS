#!/bin/bash

# 데이터베이스가 준비될 때까지 대기
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Database started"

# 마이그레이션 실행
echo "Running migrations..."
python manage.py migrate

# Django 서버 시작
echo "Starting Django server..."
exec "$@" 