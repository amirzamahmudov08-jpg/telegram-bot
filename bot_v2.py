import os
import sqlite3
from uuid import uuid4

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultCachedPhoto,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN", "8992988911:AAHX4PHVOX7Zgh_WvOm-uVb16pZI5ptzKRw")
ADMIN_ID = 7755546814
BOT_USERNAME = "MebelchiBolaBot"

CONTACT_TEXT = (
    "📞 *BOG‘LANISH*\n\n"

    "📱 Telefon:\n"
    "+998 50 200 30 50\n\n"

    "📸 [Instagram sahifamiz](https://www.instagram.com/mebelchik_bola)\n\n"

    "📍 [Manzilimiz: Namangan viloyati, Uychi tumani](https://maps.app.goo.gl/bpoyyMWTBmsoV5Jk9?g_st=ic)\n\n"

    "👤 [Telegram](https://t.me/Mebelchik_bola)"
)

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER,
    name TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER,
    type_id INTEGER,
    name TEXT,
    photo TEXT,
    price INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")

conn.commit()

admin_state = {}
user_state = {}


def format_price(price):
    try:
        return f"{int(price):,}".replace(",", " ") + " so'm"
    except Exception:
        return str(price)


def clean_price(text):
    return (
        text.replace(" ", "")
        .replace("so'm", "")
        .replace("sum", "")
        .replace("сум", "")
        .replace(",", "")
        .strip()
    )

async def save_user(user_id):
    if user_id == ADMIN_ID:
        return

    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user_id,)
    )
    conn.commit()
   

async def notify_users(context: ContextTypes.DEFAULT_TYPE, text="📢 Katalog yangilandi"):
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    for user in users:
        if user[0] == ADMIN_ID:
            continue

        try:
            await context.bot.send_message(
                chat_id=user[0],
                text=text,
                reply_markup=main_user_keyboard()
            )
        except Exception:
            pass


def admin_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["➕ Kategoriya", "✏️ Kategoriya", "🗑 Kategoriya"],
            ["➕ Tur", "✏️ Tur", "🗑 Tur"],
            ["➕ Mahsulot", "✏️ Mahsulot", "🗑 Mahsulot"],
            ["📋 Mahsulotlar"],
            ["🏠 Admin menyu"],
        ],
        resize_keyboard=True
    )


def main_user_keyboard():
    cursor.execute("SELECT name FROM categories ORDER BY name")
    categories = cursor.fetchall()

    keyboard = [[c[0]] for c in categories]
    keyboard.append(["📞 Bog‘lanish"])

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def admin_back_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["⬅️ Ortga"],
            ["🏠 Admin menyu"],
        ],
        resize_keyboard=True
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await save_user(user_id)

    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "👨‍💼 ADMIN PANEL\n\nKerakli bo‘limni tanlang:",
            reply_markup=admin_keyboard()
        )
    else:
        await update.message.reply_text(
            "🏠 Mebel katalogiga xush kelibsiz!\n\nKategoriyani tanlang:",
            reply_markup=main_user_keyboard()
        )


async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_state.clear()
    await update.message.reply_text(
        "👨‍💼 ADMIN PANEL\n\nKerakli bo‘limni tanlang:",
        reply_markup=admin_keyboard()
    )


async def show_user_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state.pop(user_id, None)

    await update.message.reply_text(
        "🏠 Bosh menyu\n\nKategoriyani tanlang:",
        reply_markup=main_user_keyboard()
    )


async def cancel_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_state.clear()
    await update.message.reply_text(
        "❌ Amal bekor qilindi.",
        reply_markup=admin_keyboard()
    )


async def show_products_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("""
        SELECT
            products.id,
            products.name,
            products.price,
            categories.name,
            types.name
        FROM products
        JOIN categories ON products.category_id = categories.id
        JOIN types ON products.type_id = types.id
        ORDER BY products.id DESC
    """)
    products = cursor.fetchall()

    if not products:
        await update.message.reply_text("Mahsulotlar yo‘q.", reply_markup=admin_keyboard())
        return

    msg = "📋 MAHSULOTLAR:\n\n"
    for p in products:
        msg += (
            f"ID: {p[0]}\n"
            f"📦 {p[1]}\n"
            f"📂 {p[3]} > {p[4]}\n"
            f"💰 {format_price(p[2])}\n\n"
        )

    await update.message.reply_text(msg, reply_markup=admin_keyboard())


async def start_add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_state.clear()
    admin_state["step"] = "add_category_name"

    await update.message.reply_text(
        "➕ Kategoriya nomini yozing:",
        reply_markup=admin_back_keyboard()
    )


async def start_edit_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cursor.fetchall()

    if not categories:
        await update.message.reply_text("Kategoriya yo‘q.", reply_markup=admin_keyboard())
        return

    keyboard = [
        [InlineKeyboardButton(c[1], callback_data=f"editcat_{c[0]}")]
        for c in categories
    ]

    await update.message.reply_text(
        "✏️ Tahrirlash uchun kategoriyani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def start_delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cursor.fetchall()

    if not categories:
        await update.message.reply_text("Kategoriya yo‘q.", reply_markup=admin_keyboard())
        return

    keyboard = [
        [InlineKeyboardButton(c[1], callback_data=f"delcat_{c[0]}")]
        for c in categories
    ]

    await update.message.reply_text(
        "🗑 O‘chirish uchun kategoriyani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def start_add_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cursor.fetchall()

    if not categories:
        await update.message.reply_text("Avval kategoriya qo‘shing.", reply_markup=admin_keyboard())
        return

    keyboard = [
        [InlineKeyboardButton(c[1], callback_data=f"addtype_cat_{c[0]}")]
        for c in categories
    ]

    await update.message.reply_text(
        "➕ Tur qo‘shish uchun kategoriyani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def start_edit_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("""
        SELECT types.id, types.name, categories.name
        FROM types
        JOIN categories ON types.category_id = categories.id
        ORDER BY categories.name, types.name
    """)
    types = cursor.fetchall()

    if not types:
        await update.message.reply_text("Tur yo‘q.", reply_markup=admin_keyboard())
        return

    keyboard = [
        [InlineKeyboardButton(f"{t[2]} > {t[1]}", callback_data=f"edittype_{t[0]}")]
        for t in types
    ]

    await update.message.reply_text(
        "✏️ Tahrirlash uchun turni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def start_delete_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("""
        SELECT types.id, types.name, categories.name
        FROM types
        JOIN categories ON types.category_id = categories.id
        ORDER BY categories.name, types.name
    """)
    types = cursor.fetchall()

    if not types:
        await update.message.reply_text("Tur yo‘q.", reply_markup=admin_keyboard())
        return

    keyboard = [
        [InlineKeyboardButton(f"{t[2]} > {t[1]}", callback_data=f"deltype_{t[0]}")]
        for t in types
    ]

    await update.message.reply_text(
        "🗑 O‘chirish uchun turni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def start_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cursor.fetchall()

    if not categories:
        await update.message.reply_text("Avval kategoriya qo‘shing.", reply_markup=admin_keyboard())
        return

    keyboard = [
        [InlineKeyboardButton(c[1], callback_data=f"addprod_cat_{c[0]}")]
        for c in categories
    ]

    await update.message.reply_text(
        "➕ Mahsulot qo‘shish uchun kategoriyani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def start_edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("""
        SELECT products.id, products.name, products.price, categories.name, types.name
        FROM products
        JOIN categories ON products.category_id = categories.id
        JOIN types ON products.type_id = types.id
        ORDER BY products.id DESC
    """)
    products = cursor.fetchall()

    if not products:
        await update.message.reply_text("Mahsulotlar yo‘q.", reply_markup=admin_keyboard())
        return

    keyboard = [
        [InlineKeyboardButton(f"{p[1]} | {format_price(p[2])}", callback_data=f"editprod_{p[0]}")]
        for p in products
    ]

    await update.message.reply_text(
        "✏️ Tahrirlash uchun mahsulotni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def start_delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("""
        SELECT products.id, products.name, products.price, categories.name, types.name
        FROM products
        JOIN categories ON products.category_id = categories.id
        JOIN types ON products.type_id = types.id
        ORDER BY products.id DESC
    """)
    products = cursor.fetchall()

    if not products:
        await update.message.reply_text("Mahsulotlar yo‘q.", reply_markup=admin_keyboard())
        return

    keyboard = [
        [InlineKeyboardButton(f"{p[1]} | {format_price(p[2])}", callback_data=f"delprod_{p[0]}")]
        for p in products
    ]

    await update.message.reply_text(
        "🗑 O‘chirish uchun mahsulotni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_admin_steps(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    if "step" not in admin_state:
        return False

    step = admin_state["step"]

    if step == "add_category_name":
        name = text.strip()
        if not name:
            await update.message.reply_text("Kategoriya nomi bo‘sh bo‘lmasin.")
            return True

        try:
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            conn.commit()
            admin_state.clear()
            await update.message.reply_text("✅ Kategoriya qo‘shildi.", reply_markup=admin_keyboard())
            await notify_users(context)
        except sqlite3.IntegrityError:
            await update.message.reply_text("Bu kategoriya oldin qo‘shilgan.")
        return True

    if step == "edit_category_name":
        name = text.strip()
        if not name:
            await update.message.reply_text("Kategoriya nomi bo‘sh bo‘lmasin.")
            return True

        try:
            cursor.execute(
                "UPDATE categories SET name=? WHERE id=?",
                (name, admin_state["category_id"])
            )
            conn.commit()
            admin_state.clear()
            await update.message.reply_text("✅ Kategoriya yangilandi.", reply_markup=admin_keyboard())
            await notify_users(context)
        except sqlite3.IntegrityError:
            await update.message.reply_text("Bu nomdagi kategoriya bor.")
        return True

    if step == "add_type_name":
        name = text.strip()
        if not name:
            await update.message.reply_text("Tur nomi bo‘sh bo‘lmasin.")
            return True

        cursor.execute(
            "INSERT INTO types (category_id, name) VALUES (?, ?)",
            (admin_state["category_id"], name)
        )
        conn.commit()
        admin_state.clear()
        await update.message.reply_text("✅ Tur qo‘shildi.", reply_markup=admin_keyboard())
        await notify_users(context)
        return True

    if step == "edit_type_name":
        name = text.strip()
        if not name:
            await update.message.reply_text("Tur nomi bo‘sh bo‘lmasin.")
            return True

        cursor.execute(
            "UPDATE types SET name=? WHERE id=?",
            (name, admin_state["type_id"])
        )
        conn.commit()
        admin_state.clear()
        await update.message.reply_text("✅ Tur yangilandi.", reply_markup=admin_keyboard())
        await notify_users(context)
        return True

    if step == "add_product_name":
        name = text.strip()
        if not name:
            await update.message.reply_text("Mahsulot nomi bo‘sh bo‘lmasin.")
            return True

        admin_state["product_name"] = name
        admin_state["step"] = "add_product_photo"
        await update.message.reply_text("📸 Mahsulot rasmini yuboring:")
        return True

    if step == "add_product_photo":
        if not update.message.photo:
            await update.message.reply_text("❗ Rasm yuboring.")
            return True

        admin_state["photo"] = update.message.photo[-1].file_id
        admin_state["step"] = "add_product_price"
        await update.message.reply_text("💰 Narxni raqam bilan yozing. Masalan: 3500000")
        return True

    if step == "add_product_price":
        price_text = clean_price(text)
        if not price_text.isdigit():
            await update.message.reply_text("Narx faqat raqam bo‘lsin. Masalan: 3500000")
            return True

        cursor.execute(
            """
            INSERT INTO products (category_id, type_id, name, photo, price)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                admin_state["category_id"],
                admin_state["type_id"],
                admin_state["product_name"],
                admin_state["photo"],
                int(price_text)
            )
        )
        conn.commit()
        admin_state.clear()
        await update.message.reply_text("✅ Mahsulot qo‘shildi.", reply_markup=admin_keyboard())
        await notify_users(context)
        return True

    if step == "edit_product_name":
        name = text.strip()
        if not name:
            await update.message.reply_text("Nom bo‘sh bo‘lmasin.")
            return True

        cursor.execute(
            "UPDATE products SET name=? WHERE id=?",
            (name, admin_state["product_id"])
        )
        conn.commit()
        admin_state.clear()
        await update.message.reply_text("✅ Mahsulot nomi yangilandi.", reply_markup=admin_keyboard())
        await notify_users(context)
        return True

    if step == "edit_product_price":
        price_text = clean_price(text)
        if not price_text.isdigit():
            await update.message.reply_text("Narx faqat raqam bo‘lsin. Masalan: 3500000")
            return True

        cursor.execute(
            "UPDATE products SET price=? WHERE id=?",
            (int(price_text), admin_state["product_id"])
        )
        conn.commit()
        admin_state.clear()
        await update.message.reply_text("✅ Narx yangilandi.", reply_markup=admin_keyboard())
        await notify_users(context)
        return True

    if step == "edit_product_photo":
        if not update.message.photo:
            await update.message.reply_text("❗ Rasm yuboring.")
            return True

        cursor.execute(
            "UPDATE products SET photo=? WHERE id=?",
            (update.message.photo[-1].file_id, admin_state["product_id"])
        )
        conn.commit()
        admin_state.clear()
        await update.message.reply_text("✅ Rasm yangilandi.", reply_markup=admin_keyboard())
        await notify_users(context)
        return True

    return False


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("addtype_cat_"):
        category_id = int(data.replace("addtype_cat_", ""))
        admin_state.clear()
        admin_state["step"] = "add_type_name"
        admin_state["category_id"] = category_id
        await query.edit_message_text("➕ Shu kategoriya uchun tur nomini yozing:")
        return

    if data.startswith("editcat_"):
        category_id = int(data.replace("editcat_", ""))
        admin_state.clear()
        admin_state["step"] = "edit_category_name"
        admin_state["category_id"] = category_id
        await query.edit_message_text("✏️ Yangi kategoriya nomini yozing:")
        return

    if data.startswith("delcat_"):
        category_id = int(data.replace("delcat_", ""))

        cursor.execute("SELECT id FROM types WHERE category_id=?", (category_id,))
        type_rows = cursor.fetchall()

        for t in type_rows:
            cursor.execute("DELETE FROM products WHERE type_id=?", (t[0],))

        cursor.execute("DELETE FROM types WHERE category_id=?", (category_id,))
        cursor.execute("DELETE FROM categories WHERE id=?", (category_id,))
        conn.commit()

        await query.edit_message_text("🗑 Kategoriya, unga tegishli turlar va mahsulotlar o‘chirildi.")
        await notify_users(context)
        return

    if data.startswith("edittype_"):
        type_id = int(data.replace("edittype_", ""))
        admin_state.clear()
        admin_state["step"] = "edit_type_name"
        admin_state["type_id"] = type_id
        await query.edit_message_text("✏️ Yangi tur nomini yozing:")
        return

    if data.startswith("deltype_"):
        type_id = int(data.replace("deltype_", ""))
        cursor.execute("DELETE FROM products WHERE type_id=?", (type_id,))
        cursor.execute("DELETE FROM types WHERE id=?", (type_id,))
        conn.commit()

        await query.edit_message_text("🗑 Tur va unga tegishli mahsulotlar o‘chirildi.")
        await notify_users(context)
        return

    if data.startswith("addprod_cat_"):
        category_id = int(data.replace("addprod_cat_", ""))

        cursor.execute(
            "SELECT id, name FROM types WHERE category_id=? ORDER BY name",
            (category_id,)
        )
        types = cursor.fetchall()

        if not types:
            await query.edit_message_text("Bu kategoriyada hali tur yo‘q. Avval ➕ Tur qo‘shing.")
            return

        keyboard = [
            [InlineKeyboardButton(t[1], callback_data=f"addprod_type_{category_id}_{t[0]}")]
            for t in types
        ]

        await query.edit_message_text(
            "📂 Turni tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("addprod_type_"):
        parts = data.split("_")
        category_id = int(parts[2])
        type_id = int(parts[3])

        admin_state.clear()
        admin_state["step"] = "add_product_name"
        admin_state["category_id"] = category_id
        admin_state["type_id"] = type_id

        await query.edit_message_text("📦 Mahsulot nomini yozing:")
        return

    if data.startswith("editprod_"):
        product_id = int(data.replace("editprod_", ""))

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📦 Nomi", callback_data=f"editname_{product_id}"),
                InlineKeyboardButton("💰 Narxi", callback_data=f"editprice_{product_id}")
            ],
            [
                InlineKeyboardButton("📸 Rasmi", callback_data=f"editphoto_{product_id}")
            ]
        ])

        await query.edit_message_text(
            "✏️ Nimani tahrirlaysiz?",
            reply_markup=keyboard
        )
        return

    if data.startswith("editname_"):
        product_id = int(data.replace("editname_", ""))
        admin_state.clear()
        admin_state["step"] = "edit_product_name"
        admin_state["product_id"] = product_id
        await query.edit_message_text("📦 Yangi mahsulot nomini yozing:")
        return

    if data.startswith("editprice_"):
        product_id = int(data.replace("editprice_", ""))
        admin_state.clear()
        admin_state["step"] = "edit_product_price"
        admin_state["product_id"] = product_id
        await query.edit_message_text("💰 Yangi narxni raqam bilan yozing:")
        return

    if data.startswith("editphoto_"):
        product_id = int(data.replace("editphoto_", ""))
        admin_state.clear()
        admin_state["step"] = "edit_product_photo"
        admin_state["product_id"] = product_id
        await query.edit_message_text("📸 Yangi rasm yuboring:")
        return

    if data.startswith("delprod_"):
        product_id = int(data.replace("delprod_", ""))
        cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()

        await query.edit_message_text("🗑 Mahsulot o‘chirildi.")
        await notify_users(context)
        return


async def show_types_for_category(update: Update, context: ContextTypes.DEFAULT_TYPE, category_name: str):
    user_id = update.effective_user.id

    cursor.execute("SELECT id, name FROM categories WHERE name=?", (category_name,))
    category = cursor.fetchone()

    if not category:
        return False

    category_id = category[0]

    cursor.execute(
        "SELECT id, name FROM types WHERE category_id=? ORDER BY name",
        (category_id,)
    )
    types = cursor.fetchall()

    if not types:
        await update.message.reply_text(
            "Bu kategoriyada hali tur yo‘q.",
            reply_markup=main_user_keyboard()
        )
        return True

    user_state[user_id] = {
        "category_id": category_id,
        "category_name": category_name
    }

    keyboard = [[t[1]] for t in types]
    keyboard.append(["⬅️ Orqaga"])
    keyboard.append(["🏠 Bosh menyu"])

    await update.message.reply_text(
        f"📂 {category_name}\n\nTurni tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return True


async def show_inline_catalog_button(update: Update, context: ContextTypes.DEFAULT_TYPE, type_name: str):
    user_id = update.effective_user.id

    if user_id not in user_state:
        return False

    category_id = user_state[user_id]["category_id"]
    category_name = user_state[user_id]["category_name"]

    cursor.execute(
        "SELECT id, name FROM types WHERE category_id=? AND name=?",
        (category_id, type_name)
    )
    type_row = cursor.fetchone()

    if not type_row:
        return False

    type_id = type_row[0]
    query_text = f"cat{category_id}_type{type_id}"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔍 Katalogni ochish",
                switch_inline_query_current_chat=query_text
            )
        ]
    ])

    await update.message.reply_text(
        f"📂 {category_name} > {type_name}\n\nKatalogni ochish uchun tugmani bosing:",
        reply_markup=keyboard
    )

    return True


async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = update.inline_query.query.strip()
    results = []

    category_id = None
    type_id = None

    if query_text.startswith("cat") and "_type" in query_text:
        try:
            left, right = query_text.split("_type")
            category_id = int(left.replace("cat", ""))
            type_id = int(right)
        except Exception:
            pass

    if category_id and type_id:
        cursor.execute(
            """
            SELECT
                products.id,
                products.name,
                products.photo,
                products.price,
                categories.name,
                types.name
            FROM products
            JOIN categories ON products.category_id = categories.id
            JOIN types ON products.type_id = types.id
            WHERE products.category_id=? AND products.type_id=?
            ORDER BY products.id DESC
            """,
            (category_id, type_id)
        )
    else:
        cursor.execute(
            """
            SELECT
                products.id,
                products.name,
                products.photo,
                products.price,
                categories.name,
                types.name
            FROM products
            JOIN categories ON products.category_id = categories.id
            JOIN types ON products.type_id = types.id
            ORDER BY products.id DESC
            LIMIT 20
            """
        )

    products = cursor.fetchall()

    for product in products:
        product_name = product[1]
        photo = product[2]
        price = product[3]
        category_name = product[4]
        type_name = product[5]

        caption = (
            f"📦 {product_name}\n\n"
            f"📂 {category_name} > {type_name}\n"
            f"💰 {format_price(price)}\n\n"
            f"📞 @Mirzamahmudov\n"
            f"📱 +998 50 200 30 50"
        )

        results.append(
            InlineQueryResultCachedPhoto(
                id=str(uuid4()),
                photo_file_id=photo,
                title=product_name,
                description=f"{category_name} > {type_name} | {format_price(price)}",
                caption=caption
            )
        )

    await update.inline_query.answer(results, cache_time=1)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text if update.message.text else ""

    await save_user(user_id)

    if user_id == ADMIN_ID:
        if text == "🏠 Admin menyu":
            await show_admin_menu(update, context)
            return

        if text == "⬅️ Ortga":
            await show_admin_menu(update, context)
            return

        if text == "➕ Kategoriya":
            await start_add_category(update, context)
            return

        if text == "✏️ Kategoriya":
            await start_edit_category(update, context)
            return

        if text == "🗑 Kategoriya":
            await start_delete_category(update, context)
            return

        if text == "➕ Tur":
            await start_add_type(update, context)
            return

        if text == "✏️ Tur":
            await start_edit_type(update, context)
            return

        if text == "🗑 Tur":
            await start_delete_type(update, context)
            return

        if text == "➕ Mahsulot":
            await start_add_product(update, context)
            return

        if text == "✏️ Mahsulot":
            await start_edit_product(update, context)
            return

        if text == "🗑 Mahsulot":
            await start_delete_product(update, context)
            return

        if text == "📋 Mahsulotlar":
            await show_products_list(update, context)
            return

        handled = await handle_admin_steps(update, context, text)
        if handled:
            return

    if text == "🏠 Bosh menyu":
        await show_user_main_menu(update, context)
        return

    if text == "⬅️ Orqaga":
        await show_user_main_menu(update, context)
        return

    category_handled = await show_types_for_category(update, context, text)
    if category_handled:
        return

    type_handled = await show_inline_catalog_button(update, context, text)
    if type_handled:
        return

    if text == "📞 Bog‘lanish":
        await update.message.reply_text(
    CONTACT_TEXT,
    parse_mode="Markdown",
    disable_web_page_preview=True
)
        return


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT, handle))
    app.add_handler(MessageHandler(filters.PHOTO, handle))

    print("✅ MebelchiBolaBot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
