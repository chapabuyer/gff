import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
    FSInputFile,
    CallbackQuery
)

# ТОКЕН БОТА (Получи в @BotFather)
TOKEN = "8610974193:AAGQNlFICUkS1mvTv_aNiobTk499LuwrdTw"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ДИНАМИЧЕСКАЯ БАЗА ДАННЫХ ТОВАРОВ (ЦЕНЫ ТОЛЬКО В ГРИВНАХ) ---
PRODUCTS_DB = {
    "autoregs": {
        "title": "⚡ Автореги ⚡",
        "category_name": "Автореги ⚡",
        "tech_text": "Cookies, User-Agent, родная почта в комплекте. Идеально подходят для залива.",
        "price_uah": 45,
        "geos": {
            "spain": {"name": "Испания", "flag": "🇪🇸", "count": 28},
            "italy": {"name": "Италия", "flag": "🇮🇹", "count": 420},
            "argentina": {"name": "Аргентина", "flag": "🇦🇷", "count": 45},
            "brazil": {"name": "Бразилия", "flag": "🇧🇷", "count": 51}
        }
    },
    "bm_pzrd": {
        "title": "💎 БМ ПЗРД 💎",
        "category_name": "БМ ПЗРД 💎",
        "tech_text": "Бизнес Менеджер с пройденным запретом рекламной деятельности (ПЗРД). Лимит БМ 50.",
        "price_uah": 195,
        "geos": {
            "spain": {"name": "Испания", "flag": "🇪🇸", "count": 10},
            "italy": {"name": "Италия", "flag": "🇮🇹", "count": 10},
            "argentina": {"name": "Аргентина", "flag": "🇦🇷", "count": 10},
            "brazil": {"name": "Бразилия", "flag": "🇧🇷", "count": 10}
        }
    },
    "manual_farm": {
        "title": "⭐ Ручной фарм ПЗРД ⭐",
        "category_name": "Ручной фарм ПЗРД ⭐",
        "tech_text": "Высококачественные аккаунты ручного фарма с пройденным ПЗРД. Полностью готовы к запуску рекламы.",
        "price_uah": 450,
        "geos": {
            "spain": {"name": "Испания", "flag": "🇪🇸", "count": 10},
            "italy": {"name": "Италия", "flag": "🇮🇹", "count": 10},
            "argentina": {"name": "Аргентина", "flag": "🇦🇷", "count": 10},
            "brazil": {"name": "Бразилия", "flag": "🇧🇷", "count": 10}
        }
    },
    "kings": {
        "title": "👑 Кинги ПЗРД 👑",
        "category_name": "👑 Кинги ПЗРД 👑",
        "tech_text": "Топовые Кинг аккаунты (материнки) с пройденным ПЗРД для крепления личек и БМ.",
        "price_uah": 775,
        "geos": {
            "spain": {"name": "Испания", "flag": "🇪🇸", "count": 10},
            "italy": {"name": "Италия", "flag": "🇮🇹", "count": 10},
            "argentina": {"name": "Аргентина", "flag": "🇦🇷", "count": 10},
            "brazil": {"name": "Бразилия", "flag": "🇧🇷", "count": 10}
        }
    }
}

class BuyProductState(StatesGroup):
    waiting_for_amount = State()


# --- КЛАВИАТУРЫ ---

def get_main_reply_keyboard():
    buttons = [[KeyboardButton(text="⚡ Главное меню")]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_main_inline_keyboard(balance=0):
    buttons = [
        [InlineKeyboardButton(text=f"💰 Баланс ({balance}₴)", callback_data="shop_balance")],
        [
            InlineKeyboardButton(text="⚡ Купить", callback_data="shop_buy"),
            InlineKeyboardButton(text="🛍 Товары", callback_data="shop_products")
        ],
        [
            InlineKeyboardButton(text="🛒 Мои заказы", callback_data="shop_orders"),
            InlineKeyboardButton(text="📜 Правила", callback_data="shop_rules")
        ],
        [InlineKeyboardButton(text="🛟 Тех. Поддержка", url="https://t.me/твой_саппорт")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_deposit_keyboard():
    buttons = [
        [InlineKeyboardButton(text="👨‍💻 Через оператора [24/7]", url="https://t.me/StormShopSup")],
        [InlineKeyboardButton(text="💲 Криптовалюта [AUTO]", callback_data="deposit_crypto")],
        [InlineKeyboardButton(text="⚡ Главное меню", callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_to_deposit_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⚡ Назад", callback_data="shop_balance")]])

def get_categories_keyboard():
    buttons = [
        [InlineKeyboardButton(text="⚡ Автореги ⚡", callback_data="maincat_autoregs")],
        [InlineKeyboardButton(text="💎 БМ ПЗРД 💎", callback_data="maincat_bm_pzrd")],
        [InlineKeyboardButton(text="Ручной фарм ПЗРД", callback_data="maincat_manual_farm")],
        [InlineKeyboardButton(text="👑 Кинги ПЗРД", callback_data="maincat_kings")],
        [InlineKeyboardButton(text="⚡ Главное меню", callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_all_products_list_keyboard():
    buttons = []
    for key, data in PRODUCTS_DB.items():
        buttons.append([InlineKeyboardButton(text=data["title"], callback_data=f"maincat_{key}")])
    buttons.append([InlineKeyboardButton(text="⚡ Главное меню", callback_data="back_to_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_countries_keyboard(category_code):
    buttons = [
        [InlineKeyboardButton(text="Испания 🇪🇸", callback_data=f"selectgeo_{category_code}_spain")],
        [InlineKeyboardButton(text="Италия 🇮🇹", callback_data=f"selectgeo_{category_code}_italy")],
        [InlineKeyboardButton(text="Аргентина 🇦🇷", callback_data=f"selectgeo_{category_code}_argentina")],
        [InlineKeyboardButton(text="Бразилия 🇧🇷", callback_data=f"selectgeo_{category_code}_brazil")],
        [InlineKeyboardButton(text="⚡ Главное меню", callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_product_keyboard(category_code, geo_code):
    buttons = [
        [InlineKeyboardButton(text="⚡ Перейти к покупке", callback_data=f"checkout_{category_code}_{geo_code}")],
        [InlineKeyboardButton(text="⚡ Главное меню", callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_only_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⚡ Главное меню", callback_data="back_to_main_menu")]])


# --- ОСНОВНЫЕ ХЭНДЛЕРЫ ---

async def send_shop_main_menu(message: Message):
    caption_text = "👋 Добро пожаловать в STORM SHOP!\n\nИспользуй меню ниже для навигации по магазину."
    try:
        photo = FSInputFile("storm_banner.jpg")
        await message.answer_photo(photo=photo, caption=caption_text, reply_markup=get_main_inline_keyboard(0))
    except Exception:
        await message.answer(text=caption_text, reply_markup=get_main_inline_keyboard(0))

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Магазин запущен.", reply_markup=get_main_reply_keyboard())
    await send_shop_main_menu(message)

@dp.message(F.text == "⚡ Главное меню")
async def process_main_menu_button(message: Message, state: FSMContext):
    await state.clear()
    await send_shop_main_menu(message)


# --- ОБРАБОТКА ИНЛАЙН НАЖАТИЙ ---

@dp.callback_query(F.data == "shop_rules")
async def process_shop_rules(call: CallbackQuery):
    await call.answer()
    rules_text = (
        "📜 **Правила нашего магазина STORM SHOP:**\n\n"
        "1. ⚠️ **Проверка товара:** На проверку купленных аккаунтов / БМ дается 20 минут с момента покупки.\n"
        "2. 🛑 **Правила замены:** Замена производится только в случае невалидности аккаунта ДО совершения вами любых действий. Если вы успели запустить рекламу, привязать карту или совершить иные действия — замена невозможна.\n"
        "3. 💲 **Баланс:** Средства, внесенные на баланс магазина, не подлежат возврату и могут быть потрачены только на покупку позиций из ассортимента.\n\n"
        " Покупая товар, вы автоматически соглашаетесь с данными правилами."
    )
    try:
        photo = FSInputFile("storm_banner.jpg")
        await call.message.edit_media(
            media=types.InputMediaPhoto(media=photo, caption=rules_text, parse_mode="Markdown"),
            reply_markup=get_back_only_keyboard()
        )
    except Exception:
        await call.message.edit_text(text=rules_text, parse_mode="Markdown", reply_markup=get_back_only_keyboard())

@dp.callback_query(F.data == "shop_orders")
async def process_shop_orders(call: CallbackQuery):
    await call.answer()
    orders_text = "🛒 **История ваших заказов:**\n\n📭 _Вы еще не совершали покупок в нашем магазине._"
    try:
        photo = FSInputFile("storm_banner.jpg")
        await call.message.edit_media(
            media=types.InputMediaPhoto(media=photo, caption=orders_text, parse_mode="Markdown"),
            reply_markup=get_back_only_keyboard()
        )
    except Exception:
        await call.message.edit_text(text=orders_text, parse_mode="Markdown", reply_markup=get_back_only_keyboard())

@dp.callback_query(F.data == "shop_products")
async def process_all_products_view(call: CallbackQuery):
    await call.answer()
    products_text = "📍 **Ассортимент нашего магазина:**"
    try:
        photo = FSInputFile("storm_banner.jpg")
        await call.message.edit_media(
            media=types.InputMediaPhoto(media=photo, caption=products_text, parse_mode="Markdown"),
            reply_markup=get_all_products_list_keyboard()
        )
    except Exception:
        await call.message.edit_text(text=products_text, parse_mode="Markdown", reply_markup=get_all_products_list_keyboard())

@dp.callback_query(F.data == "shop_buy")
async def process_shop_buy(call: CallbackQuery):
    await call.answer()
    categories_text = "📍 **Выберите тип товара:**"
    try:
        photo = FSInputFile("storm_banner.jpg")
        await call.message.edit_media(media=types.InputMediaPhoto(media=photo, caption=categories_text), reply_markup=get_categories_keyboard())
    except Exception:
        await call.message.edit_text(text=categories_text, reply_markup=get_categories_keyboard())

@dp.callback_query(F.data.startswith("maincat_"))
async def process_main_category(call: CallbackQuery):
    await call.answer()
    category_code = call.data.replace("maincat_", "")
    
    if category_code not in PRODUCTS_DB:
        await call.message.answer("⚠️ Данный раздел временно пуст или находится в разработке.")
        return
        
    countries_text = "📍 **Выберите категорию:**"
    try:
        photo = FSInputFile("storm_banner.jpg")
        await call.message.edit_media(
            media=types.InputMediaPhoto(media=photo, caption=countries_text, parse_mode="Markdown"),
            reply_markup=get_countries_keyboard(category_code)
        )
    except Exception:
        await call.message.edit_text(text=countries_text, parse_mode="Markdown", reply_markup=get_countries_keyboard(category_code))

# --- КАРТОЧКА ТОВАРА БЕЗ ЛИШНЕГО МУСОРА ---
@dp.callback_query(F.data.startswith("selectgeo_"))
async def process_geo_selection(call: CallbackQuery):
    await call.answer()
    
    data_parts = call.data.split("_")
    geo_code = data_parts[-1]
    category_code = "_".join(data_parts[1:-1])
    
    cat_info = PRODUCTS_DB.get(category_code)
    if not cat_info:
        await call.message.answer("⚠️ Ошибка: Категория не найдена. Вернитесь в Главное меню.")
        return
        
    geo_info = cat_info["geos"].get(geo_code)
    if not geo_info:
        await call.message.answer("⚠️ Ошибка: Данное ГЕО временно недоступно.")
        return
    
    # Полностью чистый текст без "nighttime" и ">"
    product_text = (
        f"🌍 **Страна:** {geo_info['name']} {geo_info['flag']}\n"
        f"📦 **Категория:** {cat_info['category_name']}\n"
        f"📝 **Описание товара:** {cat_info['tech_text']}\n\n"
        f"💰 **Цена:** {cat_info['price_uah']}₴ / шт.\n"
        f"📉 **В наличии:** {geo_info['count']} шт."
    )
    
    try:
        photo = FSInputFile("storm_banner.jpg")
        await call.message.edit_media(
            media=types.InputMediaPhoto(media=photo, caption=product_text, parse_mode="Markdown"),
            reply_markup=get_product_keyboard(category_code, geo_code)
        )
    except Exception:
        await call.message.edit_text(text=product_text, parse_mode="Markdown", reply_markup=get_product_keyboard(category_code, geo_code))

@dp.callback_query(F.data.startswith("checkout_"))
async def process_checkout(call: CallbackQuery, state: FSMContext):
    await call.answer()
    
    data_parts = call.data.split("_")
    geo_code = data_parts[-1]
    category_code = "_".join(data_parts[1:-1])
    
    cat_info = PRODUCTS_DB.get(category_code)
    if not cat_info:
        await call.message.answer("⚠️ Ошибка при формировании заказа. Вернитесь в Главное меню.")
        return
        
    geo_info = cat_info["geos"].get(geo_code)
    
    info_text = (
        f"🌍 **Страна:** {geo_info['name']} {geo_info['flag']}\n"
        f"📦 **Категория:** {cat_info['category_name']}\n"
        f"📝 **Описание товара:** {cat_info['tech_text']}\n\n"
        f"💰 **Цена:** {cat_info['price_uah']}₴ / шт.\n"
        f"📉 **В наличии:** {geo_info['count']} шт.\n\n"
        f"✍️ **Введите необходимое кол-во товара для покупки:**"
    )
    
    await state.update_data(cat_code=category_code, geo_code=geo_code)
    await state.set_state(BuyProductState.waiting_for_amount)
    
    back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⚡ Главное меню", callback_data="back_to_main_menu")]])
    try:
        photo = FSInputFile("storm_banner.jpg")
        await call.message.edit_media(
            media=types.InputMediaPhoto(media=photo, caption=info_text, parse_mode="Markdown"),
            reply_markup=back_kb
        )
    except Exception:
        await call.message.edit_text(text=info_text, parse_mode="Markdown", reply_markup=back_kb)

@dp.message(BuyProductState.waiting_for_amount)
async def process_amount_input(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("❌ Пожалуйста, введите корректное число больше нуля:")
        return
        
    amount = int(message.text)
    user_data = await state.get_data()
    
    cat_info = PRODUCTS_DB.get(user_data["cat_code"])
    geo_info = cat_info["geos"].get(user_data["geo_code"])
    
    if amount > geo_info["count"]:
        await message.answer(f"❌ Недостаточно товара! Доступно всего: {geo_info['count']} шт.\nВведите другое количество:")
        return
        
    total_price = amount * cat_info["price_uah"]
    await state.clear()
    
    await message.answer(
        f"🛒 **Заказ сформирован!**\n\n"
        f"📦 Товар: {cat_info['title']} ({geo_info['name']} {geo_info['flag']})\n"
        f"🔢 Количество: {amount} шт.\n"
        f"💰 Сумма к оплате: **{total_price}₴**\n\n"
        f"ℹ️ _Для завершения покупки на вашем балансе должно быть достаточно средств._",
        parse_mode="Markdown",
        reply_markup=get_main_reply_keyboard()
    )

@dp.callback_query(F.data == "shop_balance")
async def process_shop_balance(call: CallbackQuery):
    await call.answer()
    deposit_text = "💰 **Выберите способ пополнения:**"
    try:
        photo = FSInputFile("storm_banner.jpg")
        await call.message.edit_media(media=types.InputMediaPhoto(media=photo, caption=deposit_text, parse_mode="Markdown"), reply_markup=get_deposit_keyboard())
    except Exception:
        await call.message.edit_text(text=deposit_text, parse_mode="Markdown", reply_markup=get_deposit_keyboard())

@dp.callback_query(F.data == "deposit_crypto")
async def process_deposit_crypto(call: CallbackQuery):
    await call.answer()
    crypto_text = "💲 **Пополнение криптовалютой**\n\n**USDT TRC20:**\n\n`TZCkafGLM655H8HVVo1n1n6PLQw5Dt7DAn`\n\n_После перевода отправьте хэш транзакции в чат, средства автоматически зачислятся на баланс._"
    try:
        photo = FSInputFile("storm_banner.jpg")
        await call.message.edit_media(media=types.InputMediaPhoto(media=photo, caption=crypto_text, parse_mode="Markdown"), reply_markup=get_back_to_deposit_keyboard())
    except Exception:
        await call.message.edit_text(text=crypto_text, parse_mode="Markdown", reply_markup=get_back_to_deposit_keyboard())

@dp.callback_query(F.data == "back_to_main_menu")
async def process_back_to_main(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    try:
        await call.message.delete()
    except Exception:
        pass
    await send_shop_main_menu(call.message)

async def main():
    print("[LOG] Баг с текстом исправлен. Описания очищены.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
