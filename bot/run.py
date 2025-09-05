import asyncio, os, httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def tg_file_url(token: str, file_path: str) -> str:
    return f"https://api.telegram.org/file/bot{token}/{file_path}"

@dp.message(F.voice)
async def handle_voice(msg: Message):
    await msg.reply("Принял голосовое, анализирую…")
    # 1) Obtener file_path desde Telegram
    file_id = msg.voice.file_id
    f = await bot.get_file(file_id)
    url = tg_file_url(BOT_TOKEN, f.file_path)

    # 2) Llamar a tu API Gateway
    payload = {
        "user_id": str(msg.from_user.id),
        "scenario": "investor",
        "audio_url": url
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{API_BASE_URL}/v1/analyze", json=payload)
        r.raise_for_status()
        data = r.json()

    # 3) Formatear respuesta
    scores = data["scores"]
    strengths = "\n• " + "\n• ".join(data["strengths"])
    improvements = "\n• " + "\n• ".join(data["improvements"])
    rewritten = data["rewritten_pitch_60s"]

    text = (
        f"🟩 *Оценки*\n"
        f"- Ясность: {scores['clarity']}\n"
        f"- Структура: {scores['structure']}\n"
        f"- Убедительность: {scores['persuasion']}\n"
        f"- Итог: *{scores['total']}*\n\n"
        f"🟢 *Сильные стороны*:{strengths}\n\n"
        f"🔴 *Зоны роста*:{improvements}\n\n"
        f"✍️ *Версия на 60 сек*\n{rewritten}"
    )
    await msg.reply(text, parse_mode="Markdown")

@dp.message()
async def fallback(msg: Message):
    await msg.reply("Отправьте голосовое сообщение (voice), и я дам фидбек.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
