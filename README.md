# PitchBoost API Gateway + Telegram Bot

Прототип для хакатона. API на FastAPI, бот на aiogram.

## Local stack

1. `docker network create pitchboost-net` (если сети ещё нет).
2. Скопировать `.env.example` → `.env` и указать `BOT_TOKEN` и ключи S3.
3. Запустить сервисы:

   ```bash
   docker compose up -d --build
   ```

Сервисы `api`, `bot`, `kafka` и `db` подключаются к общей сети `pitchboost-net`.
Платформа Никиты может присоединиться командой:

```bash
docker network connect pitchboost-net <container>
```

### Kafka contract

Сообщения в `KAFKA_TOPIC_IN` имеют вид:

```json
{
  "user_id": "<tg_chat_id>",
  "audio_id": "<s3_key>",
  "request_message": "",
  "scenario": "investor|client|academic",
  "duration_minutes": 1|3|5
}
```

Результаты возвращаются в `KAFKA_TOPIC_OUT` тем же `user_id`.

### Ограничения

* Максимальная длительность аудио: 5 минут.
* Команда `/buy` показывает кнопку со ссылкой на тестовую страницу оплаты (20 попыток за 700 ₽).

### База данных

Используется PostgreSQL. Создание пользователя с минимальными правами:

```sql
CREATE USER pitchboost WITH PASSWORD 'change_me';
CREATE DATABASE pitchboost OWNER pitchboost;
```
