from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    MessageHandler, filters
)

async def print_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    await context.bot.send_message(
        chat_id=chat.id,
        text=f"✅ معرف هذه القناة هو:\n`{chat.id}`",
        parse_mode="Markdown"
    )
    print(f"Channel ID: {chat.id}")

app = ApplicationBuilder().token("7697015463:AAFmvGVndiVDUH7U2WAYT1iLrz2OE5SiGCQ").build()

# هنا نتحقق من المنشورات في القناة
app.add_handler(
    MessageHandler(filters.UpdateType.CHANNEL_POST, print_channel_id)
)

app.run_polling()
