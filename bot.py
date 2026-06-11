
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8992988911:AAGrYmUjg3Fg34p-8Hoc2lmogiYQZfRDpK4"
ADMIN_ID = 474428019  # <- o'zingni ID qo'y

keyboard = [
    ["🛋 Oshxona mebellari", "🚪 Shkaflar"],
    ["🛋 Mehmonxona mebellari", "🛏 Yotoqxona mebellari"],
    ["🏢 Ofis mebellari"],
    ["📞 Bog'lanish"]
]

admin_keyboard = ReplyKeyboardMarkup(
    [
        ["🛋 Oshxona mebellari", "🚪 Shkaflar"],
        ["🛋 Mehmonxona mebellari", "🛏 Yotoqxona mebellari"],
        ["🏢 Ofis mebellari"]
    ],
    resize_keyboard=True
)

reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# vaqtincha saqlash
pending = {}  # admin yuborgan rasm file_id

# DATABASE (RAM ichida)
db = {
    "🛋 Oshxona mebellari": [],
    "🚪 Shkaflar": [],
    "🛋 Mehmonxona mebellari": [],
    "🛏 Yotoqxona mebellari": [],
    "🏢 Ofis mebellari": []
}


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏠 *Mebelchik Bola* botiga xush kelibsiz!\nKerakli bo'limni tanlang:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


# 📸 ADMIN rasm yuborsa
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz")
        return

    file_id = update.message.photo[-1].file_id
    pending[user_id] = file_id

    await update.message.reply_text(
        "📂 Qaysi kategoriyaga qo‘shamiz Asadbek?",
        reply_markup=admin_keyboard
    )


# 📂 TEXT handler (user + admin)
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    # 👨‍💼 ADMIN rasmni kategoriya bilan saqlaydi
    if user_id == ADMIN_ID and user_id in pending:
        file_id = pending[user_id]

        if text in db:
            db[text].append(file_id)
            del pending[user_id]

            await update.message.reply_text(f"✅ Rasm '{text}' ga qo‘shildi", reply_markup=reply_markup)
        else:
            await update.message.reply_text("❌ Noto‘g‘ri kategoriya")
        return

    # 👤 USER ko'rish
    if text in db:
        if len(db[text]) == 0:
            await update.message.reply_text("Bu kategoriya bo‘sh 😔")
        else:
            for photo in db[text]:
                await update.message.reply_photo(photo=photo, caption=text)

    elif text == "📞 Bog'lanish":
        await update.message.reply_text("📞 Tel: +998 50 200 30 50")

    else:
        await update.message.reply_text("Bo‘limni tanlang 👇")


# MAIN
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))

    print("Bot ishladi...")
    app.run_polling()


if __name__ == "__main__":
    main()