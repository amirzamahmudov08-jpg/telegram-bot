import sqlite3
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = "8992988911:AAHob29mHQdgy1Vh7rkQLfksZ3DQpwFXncc"
ADMIN_ID = 6695116909

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    photo TEXT,
    price TEXT
)
""")
conn.commit()

admin_state = {}

admin_keyboard = ReplyKeyboardMarkup(
    [["➕ Add", "📋 List"],
     ["✏️ Edit", "🗑 Delete"]],
    resize_keyboard=True
)

def user_keyboard():
    cursor.execute("SELECT DISTINCT category FROM products")
    categories = cursor.fetchall()

    keyboard = [[c[0]] for c in categories]
    keyboard.append(["📞 Bog‘lanish"])

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("👨‍💼 ADMIN PANEL", reply_markup=admin_keyboard)
    else:
        await update.message.reply_text("🏠 Kategoriyani tanlang:", reply_markup=user_keyboard())

async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("Mahsulotlar yo‘q.")
        return

    text = "📦 MAHSULOTLAR\n\n"
    for row in rows:
        text += f"ID: {row[0]} | {row[1]} | {row[3]}\n"

    await update.message.reply_text(text)

async def delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT id, category, price FROM products")
    rows = cursor.fetchall()

    keyboard = []
    for row in rows:
        keyboard.append([
            InlineKeyboardButton(
                f"{row[1]} | {row[2]}",
                callback_data=f"delete_{row[0]}"
            )
        ])

    await update.message.reply_text(
        "🗑 O‘chirish uchun tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT id, category, price FROM products")
    rows = cursor.fetchall()

    keyboard = []
    for row in rows:
        keyboard.append([
            InlineKeyboardButton(
                f"{row[1]} | {row[2]}",
                callback_data=f"edit_{row[0]}"
            )
        ])

    await update.message.reply_text(
        "✏️ Tahrirlash uchun tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("delete_"):
        product_id = data.replace("delete_", "")
        cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()
        await query.edit_message_text("🗑 Mahsulot o‘chirildi!")
        return

    if data.startswith("edit_"):
        product_id = data.replace("edit_", "")
        admin_state["step"] = "edit_price"
        admin_state["product_id"] = product_id
        await query.edit_message_text("💰 Yangi narx yozing:")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text if update.message.text else ""

    if user_id == ADMIN_ID:
        if text == "➕ Add":
            admin_state["step"] = "category"
            await update.message.reply_text("📂 Kategoriya yozing:")
            return

        if text == "📋 List":
            await list_products(update, context)
            return

        if text == "🗑 Delete":
            await delete_product(update, context)
            return

        if text == "✏️ Edit":
            await edit_product(update, context)
            return

    if user_id == ADMIN_ID and "step" in admin_state:

        if admin_state["step"] == "category":
            admin_state["category"] = text
            admin_state["step"] = "photo"
            await update.message.reply_text("📸 Rasm yuboring:")
            return

        if admin_state["step"] == "photo":
            if not update.message.photo:
                await update.message.reply_text("❗ Rasm yuboring")
                return

            admin_state["photo"] = update.message.photo[-1].file_id
            admin_state["step"] = "price"
            await update.message.reply_text("💰 Narx yozing:")
            return

        if admin_state["step"] == "price":
            cursor.execute(
                "INSERT INTO products (category, photo, price) VALUES (?, ?, ?)",
                (admin_state["category"], admin_state["photo"], text)
            )
            conn.commit()
            admin_state.clear()
            await update.message.reply_text("✅ Mahsulot qo‘shildi!")
            return

        if admin_state["step"] == "edit_price":
            cursor.execute(
                "UPDATE products SET price=? WHERE id=?",
                (text, admin_state["product_id"])
            )
            conn.commit()
            admin_state.clear()
            await update.message.reply_text("✏️ Narx yangilandi!")
            return

    cursor.execute("SELECT photo, price FROM products WHERE category=?", (text,))
    products = cursor.fetchall()

    if products:
        for product in products:
            await update.message.reply_photo(
                photo=product[0],
                caption=f"💰 {product[1]}"
            )
        return

    if text == "📞 Bog‘lanish":
        await update.message.reply_text(
            "📞 BOG‘LANISH\n\n"
            "👤 Telegram: @Mirzamahmudov\n"
            "📱 Tel: +998 50 200 30 50"
        )

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT, handle))
    app.add_handler(MessageHandler(filters.PHOTO, handle))

    print("Bot ishladi...")
    app.run_polling()

if __name__ == "__main__":
    main()
