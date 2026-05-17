import asyncio
import logging
import io
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile, Message, CallbackQuery
from config import TOKEN, ADMIN_ID
import database as db
from PIL import Image, ImageDraw, ImageFont

# Настройка логирования для отслеживания процессов в консоли
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Главное меню
def get_start_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile"),
            InlineKeyboardButton(text="🤖 Боты", callback_data="my_bots")
        ],
        [
            InlineKeyboardButton(text="❓ FAQ (Наш канал)", url="https://t.me/+8BsLCFy3o_RiMDVh")
        ],
        [
            InlineKeyboardButton(text="📚 Для ворка", callback_data="learning"),
            InlineKeyboardButton(text="🎙 ГС", callback_data="voice_messages")
        ],
        [
            InlineKeyboardButton(text="💳 Актуальные карты", callback_data="maps")
        ],
        [
            InlineKeyboardButton(text="🎬 О проекте", callback_data="about_project")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Меню раздела "Боты" (Кнопка ФБ + Назад)
def get_bots_keyboard():
    buttons = [
        [InlineKeyboardButton(text="👥 ФБ", callback_data="bot_fb")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ИСПРАВЛЕНО: Теперь все кнопки идут строго вертикально (каждая на новой строчке)
def get_learning_keyboard():
    buttons = [
        [InlineKeyboardButton(text="📖 Обучение и FAQ", url="https://t.me/+8BsLCFy3o_RiMDVh")],
        [InlineKeyboardButton(text="🌐 Бесплатный прокси", url="https://t.me/ProxyMTProto")],
        [InlineKeyboardButton(text="⭕ Сделать кружок", url="https://t.me/VideoInCircleBot")],
        [InlineKeyboardButton(text="👩 Паки девушек", url="https://t.me/+uPwvor2qLdNhNGRi")],
        [InlineKeyboardButton(text="🗣 Голосовые сообщения", url="https://t.me/+VKzsDnz_F_o3MGFh")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Стандартная кнопка "Назад" для остальных разделов
def get_back_keyboard():
    buttons = [[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Функция генерации карточки по твоим точным координатам Image Map
async def generate_profile_image(user_id, bot):
    try:
        background = Image.open("profile_bg.png").convert("RGBA")
        draw = ImageDraw.Draw(background)

        try:
            user_profile_photos = await bot.get_user_profile_photos(user_id, limit=1)
            if user_profile_photos.total_count > 0:
                file_id = user_profile_photos.photos[0][-1].file_id
                file = await bot.get_file(file_id)
                
                avatar_bytes = io.BytesIO()
                await bot.download_file(file.file_path, avatar_bytes)
                avatar_bytes.seek(0)
                
                avatar = Image.open(avatar_bytes).convert("RGBA")
                avatar_size = (337, 317) 
                avatar = avatar.resize(avatar_size)
                
                mask = Image.new("L", avatar_size, 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.rounded_rectangle([(0, 0), avatar_size], radius=45, fill=255)
                
                rounded_avatar = Image.new("RGBA", avatar_size, (0, 0, 0, 0))
                rounded_avatar.paste(avatar, (0, 0), mask=mask)
                
                background.paste(rounded_avatar, (83, 205), mask=rounded_avatar)
        except Exception as avatar_err:
            logging.error(f"Не удалось загрузить аватарку для {user_id}: {avatar_err}")

        days_in_team = 0
        try:
            join_date = await db.get_user_join_date(user_id)
            if join_date:
                days_in_team = (datetime.now() - join_date).days
        except Exception as db_err:
            logging.error(f"Ошибка при запросе даты из БД для {user_id}: {db_err}")
            days_in_team = 0
            
        text_days = str(days_in_team)

        font_path = "arial.ttf"  
        try:
            font_days = ImageFont.truetype(font_path, 65)  
        except IOError:
            logging.error("Файл arial.ttf не найден. Применен дефолтный шрифт.")
            font_days = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text_days, font=font_days)
        w_text = bbox[2] - bbox[0]
        h_text = bbox[3] - bbox[1]
        
        draw.text((634 - w_text / 2, 404 - h_text / 2), text_days, fill="#ffffff", font=font_days)

        image_bytes = io.BytesIO()
        background.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        
        return BufferedInputFile(image_bytes.read(), filename="profile.png")

    except Exception as e:
        logging.error(f"Критическая ошибка внутри generate_profile_image: {e}")
        return None

# Вспомогательная функция отправки профиля
async def process_and_send_profile(user, target_message: Message, bot: Bot):
    try:
        user_id = user.id
        username = f"@{user.username}" if user.username else user.first_name
        user_role = "Воркер"
        user_rep = 0

        profile_photo = await generate_profile_image(user_id, bot)
        
        if profile_photo:
            caption_text = (
                f"🚨 Профиль {username}\n\n"
                f"  ID: `{user_id}`\n\n"
                f"  🦅 Должность: {user_role}\n"
                f"  ┗ Репутация: {user_rep} 👍"
            )
            await target_message.answer_photo(
                photo=profile_photo,
                caption=caption_text,
                parse_mode="Markdown",
                reply_markup=get_back_keyboard()
            )
        else:
            await target_message.answer("❌ Ошибка: Скрипт не смог собрать картинку профиля. Проверьте логи.")
    except Exception as e:
        error_message = f"❌ Ошибка хэндлера профиля: {type(e).__name__} -> {str(e)}"
        logging.error(error_message)
        await target_message.answer(error_message)

# Функция отправки главного меню
async def send_main_menu(user_id, full_name, target_message: Message):
    try:
        await db.add_user(user_id)
    except Exception as db_err:
        logging.error(f"Не удалось добавить пользователя в БД: {db_err}")
        
    caption_text = f"Привет, {full_name}! 👋\n\nДобро пожаловать в GUCCI FAM.\nВыбирай нужный раздел на кнопках меню:"
    try:
        photo = FSInputFile("start_banner.jpg") 
        await target_message.answer_photo(photo=photo, caption=caption_text, reply_markup=get_start_keyboard())
    except Exception:
        await target_message.answer(caption_text, reply_markup=get_start_keyboard())

# --- ХЭНДЛЕРЫ ---

@dp.message(Command("start"))
async def cmd_start(message: Message):
    try: await message.delete()
    except Exception: pass
    await send_main_menu(message.from_user.id, message.from_user.full_name, message)

@dp.message(Command("profile"))
async def show_profile_message(message: Message, bot: Bot):
    try: await message.delete()
    except Exception: pass
    await process_and_send_profile(message.from_user, message, bot)

@dp.callback_query(F.data == "profile")
async def show_profile_callback(call: CallbackQuery, bot: Bot):
    await call.answer()
    try: await call.message.delete()
    except Exception: pass
    
    status_message = await call.message.answer("🔄 Синхронизация данных...")
    await asyncio.sleep(0.1)
    try:
        await process_and_send_profile(call.from_user, call.message, bot)
    finally:
        try: await status_message.delete()
        except Exception: pass

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback(call: CallbackQuery):
    await call.answer()
    try: await call.message.delete()
    except Exception: pass
    await send_main_menu(call.from_user.id, call.from_user.full_name, call.message)

# РАЗДЕЛ БОТЫ
@dp.callback_query(F.data == "my_bots")
async def open_bots(call: CallbackQuery):
    await call.answer()
    try: await call.message.delete()
    except Exception: pass
    await call.message.answer("🤖 Выберите интересующего вас бота из списка:", reply_markup=get_bots_keyboard())

# ПОДРАЗДЕЛ ФБ
@dp.callback_query(F.data == "bot_fb")
async def open_bot_fb(call: CallbackQuery):
    await call.answer()
    try: await call.message.delete()
    except Exception: pass
    
    fb_info_text = (
        f"👥 **ФБ**\n\n"
        f"🤖 **Бот для ворка:**\n"
        f" ┗ @StormsShopBot\n\n"
        f"📚 **Мануалы:**\n"
        f" ┗ [Мануал по ФБ](https://t.me/+eaAMi8nA-UA5YWQx)\n\n"
    )
    await call.message.answer(fb_info_text, parse_mode="Markdown", reply_markup=get_back_keyboard(), disable_web_page_preview=True)

# РАЗДЕЛ ДЛЯ ВОРКА
@dp.callback_query(F.data == "learning")
async def open_learning(call: CallbackQuery):
    await call.answer()
    try: await call.message.delete()
    except Exception: pass
    await call.message.answer("📚 **Инструменты и мануалы для эффективного ворка:**", parse_mode="Markdown", reply_markup=get_learning_keyboard())


@dp.callback_query(F.data == "voice_messages")
async def open_voice(call: CallbackQuery):
    await call.answer()
    try: await call.message.delete()
    except Exception: pass
    await call.message.answer("Запись голосовых сообщений и звонки. в случае если мамонт просит ГС или звонок. За прозвоном обращайтесь в чат.", reply_markup=get_back_keyboard())

@dp.callback_query(F.data == "maps")
async def open_maps(call: CallbackQuery):
    await call.answer()
    try: await call.message.delete()
    except Exception: pass
    await call.message.answer("🇺🇦 - 4400 0055 5151 7177", reply_markup=get_back_keyboard())

# ИСПРАВЛЕНО И ОБНОВЛЕНО: Новый текст для раздела "О проекте"
@dp.callback_query(F.data == "about_project")
async def open_about(call: CallbackQuery):
    await call.answer()
    try: await call.message.delete()
    except Exception: pass
    
    about_text = (
        "🏛 **О проекте • GUCCI FAM**\n\n"
        "    Дата запуска: 07.05.2026.\n\n"
        "🎯 **Статистика**\n\n"
        "   Количество профитов: 73.\n"
        "   Общая сумма профитов: N/A.\n\n"
        "🥩 **Выплаты воркерам**\n\n"
        "   Самостоятельно - 60%\n"
        "   Процент платы за наставничество выбирает сам наставник (указан в боте)\n"
        "   Работа с ТП - 50%\n\n"
        "💥 **Рабочие сервисы**\n\n"
        "   Нарко 🧪\n"
        "   Шантаж 👨‍👩‍👦\n"
        "   ФБ 👥"
    )
    await call.message.answer(about_text, parse_mode="Markdown", reply_markup=get_back_keyboard())

@dp.message(Command("broadcast"))
async def broadcast(message: Message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text.replace("/broadcast", "").strip()
    if not text: return await message.answer("Пиши: `/broadcast твой текст`")
    
    try:
        users = await db.get_all_users()
        count = 0
        for user_id in users:
            try:
                await bot.send_message(user_id, text)
                count += 1
            except: pass
        await message.answer(f"✅ Рассылка на {count} человек завершена.")
    except Exception as e:
        await message.answer(f"Ошибка рассылки: {e}")

async def main():
    try: await db.init_db()  
    except Exception as db_err: logging.error(f"Не удалось инициализировать БД в main: {db_err}")
        
    print("[LOG] Бот GUCCI FAM успешно запущен и готов к работе!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
