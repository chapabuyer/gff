# database.py
import aiosqlite
from datetime import datetime

async def init_db():
    async with aiosqlite.connect('users.db') as db:
        # Создаем таблицу, если ее еще не существовало
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                join_date TEXT
            )
        ''')
        await db.commit()
        
        # Защита: если база осталась от старых тестов, принудительно добавляем колонку join_date
        try:
            await db.execute('ALTER TABLE users ADD COLUMN join_date TEXT')
            await db.commit()
        except aiosqlite.OperationalError:
            pass  # Если колонка уже на месте, просто идем дальше

async def add_user(user_id):
    async with aiosqlite.connect('users.db') as db:
        async with db.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,)) as cursor:
            if not await cursor.fetchone():
                # Пишем реальную дату первого нажатия /start (ГГГГ-ММ-ДД)
                current_date = datetime.now().strftime("%Y-%m-%d")
                await db.execute('INSERT INTO users (user_id, join_date) VALUES (?, ?)', (user_id, current_date))
                await db.commit()

async def get_user_join_date(user_id):
    async with aiosqlite.connect('users.db') as db:
        async with db.execute('SELECT join_date FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                return datetime.strptime(row[0], "%Y-%m-%d")
            return None

async def get_all_users():
    async with aiosqlite.connect('users.db') as db:
        async with db.execute('SELECT user_id FROM users') as cursor:
            return [row[0] for row in await cursor.fetchall()]
