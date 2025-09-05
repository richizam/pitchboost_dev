# PitchBoost API Gateway + Telegram Bot

Прототип для хакатона. API на FastAPI, бот на aiogram.  
Сейчас ответы мокаются (без реальной обработки).

## Запуск
1. Склонировать репозиторий и перейти в папку.
2. Скопировать `.env.example` → `.env` и указать `BOT_TOKEN`.
3. Запустить:
   ```bash
   docker compose up --build
