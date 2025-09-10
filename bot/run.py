# bot/run.py
import asyncio
import json
import os
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from confluent_kafka import Consumer, KafkaException, KafkaError

# --- ENV ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC_OUT = os.getenv("KAFKA_TOPIC_OUT", "aith.messages.result")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "ai-gateway-bot")

AUDIO_MAX_SECONDS = int(os.getenv("AUDIO_MAX_SECONDS", "420"))

# --- Telegram ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ---------- UI helpers ----------
SCENARIO_LABELS = {
    "investor": "Инвестор",
    "client": "Клиент",
    "academic": "Академический",
}
SCENARIO_ORDER = ["investor", "client", "academic"]
DURATION_ORDER = [1, 3, 5]  # минуты


def tg_file_url(token: str, file_path: str) -> str:
    return f"https://api.telegram.org/file/bot{token}/{file_path}"


@dataclass
class UserSession:
    audio_url: Optional[str] = None
    scenario: str = "investor"
    duration_minutes: int = 1
    menu_message_id: Optional[int] = None
    menu_chat_id: Optional[int] = None
    media_duration_sec: Optional[int] = None


# Estado simple en memoria para el hackatón
sessions: Dict[int, UserSession] = {}


def build_menu(session: UserSession) -> "InlineKeyboardMarkup":
    """
    Teclado con selección de escenario + duración + acciones.
    Marca la opción elegida con '✅'.
    """
    kb = InlineKeyboardBuilder()

    # Escenarios (fila 1)
    row = []
    for sc in SCENARIO_ORDER:
        label = SCENARIO_LABELS[sc]
        if sc == session.scenario:
            text = f"✅ {label}"
        else:
            text = label
        kb.button(text=text, callback_data=f"sc:{sc}")
    kb.adjust(3)

    # Duraciones (fila 2)
    for dur in DURATION_ORDER:
        if dur == session.duration_minutes:
            text = f"✅ {dur} мин"
        else:
            text = f"{dur} мин"
        kb.button(text=text, callback_data=f"du:{dur}")
    kb.adjust(3, 3)

    # Acciones (fila 3)
    kb.button(text="🚀 Отправить на анализ", callback_data="go:analyze")
    kb.button(text="🔄 Сбросить", callback_data="go:reset")
    kb.adjust(3, 3, 2)

    return kb.as_markup()


def menu_text(session: UserSession) -> str:
    return (
        "🎙️ *Анализ питча*\n\n"
        "Выберите *сценарий* и *длительность* обзора.\n\n"
        f"• Сценарий: *{SCENARIO_LABELS.get(session.scenario, '—')}*\n"
        f"• Длительность: *{session.duration_minutes} мин*\n\n"
        "Когда всё готово — нажмите _«Отправить на анализ»_."
    )


# ---------- Handlers ----------
@dp.message(F.text == "/start")
async def cmd_start(msg: Message):
    text = (
        "👋 Добро пожаловать в *PitchBoost Bot*!\n\n"
        "Отправьте мне голосовое сообщение 🎙️ со своим питчем.\n\n"
        "После этого вы сможете выбрать:\n"
        "• *Сценарий*: 💼 Инвестор | 🤝 Клиент | 🎓 Академический\n"
        "• *Длительность*: ⏱️ 1, 3 или 5 минут\n\n"
        "Я дам вам обратную связь 💡: сильные стороны, зоны роста и улучшенную версию питча."
    )
    await msg.answer(text, parse_mode="Markdown")


@dp.message(F.voice)
async def handle_voice(msg: Message):
    """
    1) Получаем file_path от Telegram → собираем прямой file URL.
    2) Запоминаем URL в сессии пользователя.
    3) Показываем меню выбора сценария и длительности.
    """
    user_id = msg.from_user.id
    duration = msg.voice.duration
    if duration and duration > AUDIO_MAX_SECONDS:
        await msg.answer(
            "⚠️ Аудио дольше 7 минут. Пожалуйста, отправьте запись короче (до 7 минут)."
        )
        return

    # Получить прямой URL на файл
    file_id = msg.voice.file_id
    f = await bot.get_file(file_id)
    url = tg_file_url(BOT_TOKEN, f.file_path)

    # Обновить / создать сессию
    session = sessions.get(user_id) or UserSession()
    session.audio_url = url
    session.media_duration_sec = duration
    sessions[user_id] = session

    try:
        await bot.send_chat_action(user_id, "typing")
    except Exception:
        pass

    text = (
        "💡 *Шаг 1/2*. Я получил голосовое сообщение.\n"
        "Теперь выберите *сценарий* и *длительность* для анализа.\n"
        "После этого я отправлю запрос и пришлю итог, как только он будет готов."
    )
    await msg.answer(text, parse_mode="Markdown")

    # Mostrar/actualizar menú principal
    menu_msg = await msg.answer(
        menu_text(session), parse_mode="Markdown", reply_markup=build_menu(session)
    )
    session.menu_message_id = menu_msg.message_id
    session.menu_chat_id = msg.chat.id
    sessions[user_id] = session


@dp.message(F.audio)
async def handle_audio(msg: Message):
    """Handle regular audio files."""
    user_id = msg.from_user.id
    duration = msg.audio.duration
    if duration and duration > AUDIO_MAX_SECONDS:
        await msg.answer(
            "⚠️ Аудио дольше 7 минут. Пожалуйста, отправьте запись короче (до 7 минут)."
        )
        return

    file_id = msg.audio.file_id
    f = await bot.get_file(file_id)
    url = tg_file_url(BOT_TOKEN, f.file_path)

    session = sessions.get(user_id) or UserSession()
    session.audio_url = url
    session.media_duration_sec = duration
    sessions[user_id] = session

    try:
        await bot.send_chat_action(user_id, "typing")
    except Exception:
        pass

    text = (
        "💡 *Шаг 1/2*. Я получил аудиофайл.\n"
        "Теперь выберите *сценарий* и *длительность* для анализа.\n"
        "После этого я отправлю запрос и пришлю итог, как только он будет готов."
    )
    await msg.answer(text, parse_mode="Markdown")

    menu_msg = await msg.answer(
        menu_text(session), parse_mode="Markdown", reply_markup=build_menu(session)
    )
    session.menu_message_id = menu_msg.message_id
    session.menu_chat_id = msg.chat.id
    sessions[user_id] = session


@dp.callback_query(F.data.startswith("sc:"))
async def set_scenario(call: CallbackQuery):
    user_id = call.from_user.id
    session = sessions.get(user_id) or UserSession()
    session.scenario = call.data.split(":", 1)[1]
    sessions[user_id] = session
    await call.answer(f"Сценарий: {SCENARIO_LABELS[session.scenario]}")
    # Actualizar interfaz
    try:
        await call.message.edit_text(
            menu_text(session), parse_mode="Markdown", reply_markup=build_menu(session)
        )
    except Exception:
        # Algunos clientes no permiten editar texto demasiado a menudo — actualizamos sólo клавиатуру
        await call.message.edit_reply_markup(build_menu(session))


@dp.callback_query(F.data.startswith("du:"))
async def set_duration(call: CallbackQuery):
    user_id = call.from_user.id
    session = sessions.get(user_id) or UserSession()
    try:
        session.duration_minutes = int(call.data.split(":", 1)[1])
    except Exception:
        session.duration_minutes = 1
    sessions[user_id] = session
    await call.answer(f"Длительность: {session.duration_minutes} мин")
    # Actualizar interfaz
    try:
        await call.message.edit_text(
            menu_text(session), parse_mode="Markdown", reply_markup=build_menu(session)
        )
    except Exception:
        await call.message.edit_reply_markup(build_menu(session))


@dp.callback_query(F.data == "go:reset")
async def reset_session(call: CallbackQuery):
    user_id = call.from_user.id
    sessions[user_id] = UserSession()
    await call.answer("Сброшено.")
    await call.message.edit_text(
        "Сессия сброшена. Отправьте новое голосовое сообщение 🎙️",
        parse_mode="Markdown",
    )


@dp.callback_query(F.data == "go:analyze")
async def run_analysis(call: CallbackQuery):
    """
    Когда пользователь нажимает «Отправить на анализ», шлём POST в API:
    { user_id, scenario, duration_minutes, audio_url }.
    Дальше результат придёт через Kafka → бот отправит ответ в чат.
    """
    user_id = call.from_user.id
    session = sessions.get(user_id)
    if not session or not session.audio_url:
        await call.answer("Сначала отправьте голосовое сообщение.", show_alert=True)
        return

    payload = {
        "user_id": str(user_id),
        "scenario": session.scenario,
        "duration_minutes": session.duration_minutes,
        "audio_url": session.audio_url,
        "media_duration_sec": session.media_duration_sec,
    }

    try:
        await call.answer("Отправляю…")
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{API_BASE_URL}/v1/analyze", json=payload)
            if r.status_code == 402:
                await call.message.answer(
                    "💳 Кредиты закончились. Пополнить можно командой /buy.",
                )
                return
            if r.status_code >= 300:
                await call.message.answer(f"Ошибка API: {r.status_code}")
                return
    except Exception as e:
        await call.message.answer(f"Ошибка анализа: {e}")
        return

    # UX: подтвердить и напомнить что ответ придёт позже (через Kafka)
    await call.message.answer(
        "✅ Запрос принят! Я пришлю результат, как только он будет готов.\n\n"
        f"• Сценарий: *{SCENARIO_LABELS.get(session.scenario, '—')}*\n"
        f"• Длительность: *{session.duration_minutes} мин*",
        parse_mode="Markdown",
    )


# ---- payments ----
@dp.message(F.text == "/buy")
async def cmd_buy(msg: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="Buy 20 attempts for 700 RUB", callback_data="buy:20")
    await msg.answer(
        "Чтобы купить попытки, нажмите кнопку ниже:", reply_markup=kb.as_markup()
    )


@dp.callback_query(F.data == "buy:20")
async def process_buy(call: CallbackQuery):
    user_id = call.from_user.id
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{API_BASE_URL}/v1/buy", json={"telegram_id": str(user_id)}
            )
            r.raise_for_status()
            new_attempts = r.json().get("new_attempts", 0)
    except Exception as e:
        await call.message.answer(f"Ошибка оплаты: {e}")
        await call.answer()
        return
    await call.answer("Оплачено")
    await call.message.answer(f"Оплачено. Попыток: {new_attempts}")


@dp.message(F.text == "/balance")
async def cmd_balance(msg: Message):
    user_id = msg.from_user.id
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{API_BASE_URL}/v1/balance/{user_id}")
            data = r.json()
    except Exception:
        await msg.answer("Ошибка запроса баланса")
        return
    await msg.answer(f"Попыток осталось: {data.get('attempts', 0)}")


# ---------- Kafka consumer (result) ----------
def start_kafka_consumer(loop: asyncio.AbstractEventLoop):
    def _run():
        conf = {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "group.id": KAFKA_GROUP_ID,
            "auto.offset.reset": "earliest",
        }
        consumer = Consumer(conf)
        while True:
            try:
                consumer.subscribe([KAFKA_TOPIC_OUT])
                while True:
                    msg = consumer.poll(1.0)
                    if msg is None:
                        continue
                    if msg.error():
                        if msg.error().code() in (KafkaError._PARTITION_EOF,):
                            continue
                        if msg.error().code() in (KafkaError.UNKNOWN_TOPIC_OR_PART,):
                            time.sleep(2)
                            break  # re-subscribe
                        raise KafkaException(msg.error())
                    try:
                        data = json.loads(msg.value().decode("utf-8"))
                        user_id = str(data.get("user_id"))
                        feedback = data.get("feedback") or "Готово. (пустой ответ)"
                        fut = asyncio.run_coroutine_threadsafe(
                            bot.send_message(chat_id=user_id, text=feedback), loop
                        )
                        fut.result(timeout=30)
                    except Exception:
                        pass
            except Exception:
                time.sleep(2)
            finally:
                try:
                    consumer.unsubscribe()
                except Exception:
                    pass

    t = threading.Thread(target=_run, daemon=True)
    t.start()


# ---------- Entrypoint ----------
async def main():
    loop = asyncio.get_running_loop()
    start_kafka_consumer(loop)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
