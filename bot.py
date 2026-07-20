import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from groq import Groq

# این دو مقدار را از متغیرهای محیطی (Environment Variables) می‌خوانیم
# نیازی نیست توکن یا کلید API را داخل همین فایل بنویسید
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

# حافظه گفتگو برای هر کاربر (ساده - در حافظه رم نگه داشته می‌شود)
user_histories = {}

SYSTEM_PROMPT = (
    "تو یک دستیار گفتگوی دوستانه، صمیمی و مفید هستی که در تلگرام به فارسی صحبت می‌کنی. "
    "پاسخ‌هایت طبیعی، کوتاه و روان باشند، مثل یک مکالمه واقعی."
)

MAX_HISTORY_MESSAGES = 20  # چند پیام آخر را برای حفظ زمینه گفتگو نگه می‌داریم


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_histories[update.effective_chat.id] = []
    await update.message.reply_text(
        "سلام! 👋 من اینجام تا هر موضوعی که بخوای باهم گفتگو کنیم. "
        "کافیه پیام بدی.\n\nدستور /reset رو بفرست تا گفتگو از نو شروع بشه."
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_histories[update.effective_chat.id] = []
    await update.message.reply_text("حافظه گفتگو پاک شد ✅ از نو شروع می‌کنیم.")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_message = update.message.text

    history = user_histories.setdefault(chat_id, [])
    history.append({"role": "user", "content": user_message})
    history = history[-MAX_HISTORY_MESSAGES:]

    # به کاربر نشون بدیم که ربات داره تایپ می‌کنه
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        messages_for_api = [{"role": "system", "content": SYSTEM_PROMPT}] + history
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            messages=messages_for_api,
        )
        reply_text = response.choices[0].message.content
    except Exception as e:
        reply_text = "متاسفم، یک مشکل فنی پیش اومد. لطفاً دوباره امتحان کن."
        print(f"Error calling Groq API: {e}")

    history.append({"role": "assistant", "content": reply_text})
    user_histories[chat_id] = history[-MAX_HISTORY_MESSAGES:]

    await update.message.reply_text(reply_text)


def main():
    if not TELEGRAM_TOKEN:
        raise SystemExit("متغیر محیطی TELEGRAM_BOT_TOKEN تنظیم نشده است.")
    if not GROQ_API_KEY:
        raise SystemExit("متغیر محیطی GROQ_API_KEY تنظیم نشده است.")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("ربات در حال اجراست...")
    app.run_polling()


if __name__ == "__main__":
    main()
