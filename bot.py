import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
import json
import os
import random

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = "8410632417:AAEFvdzCZz-0HthMZBVeHrTif2LkUHSrBJM"

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ID администратора
ADMIN_ID = 7973988177  # Ваш chat ID

# Курс по умолчанию
CURRENT_RATE = 0.6  # 1 BC = 0.6₽

# Хранилище данных
users_data = {}
purchases_history = []
pending_checks = []
admin_state = {}
user_state = {}

# Реквизиты карты
CARD_NUMBER = "2204120132703386"

# Шаблоны фейк-отзывов
FAKE_REVIEWS = [
    "Быстрый донат, все пришло моментально! Рекомендую 👍",
    "Скорость на высоте, донат пришел за пару минут. 5 звезд!",
    "Очень быстрый донат, все четко и без задержек. Лучший сервис!",
    "Донат пришел мгновенно, оперативно все сделали. Быстро и качественно!",
    "Скорость просто космическая, донат прилетел за секунды. Рекомендую всем!",
    "Быстрее всех на рынке, донат пришел за минуту. Супер!",
    "Оперативно, быстро, качественно. Донат пришел моментально!",
    "Самый быстрый донат из всех что пробовал, все на 5+!",
    "Молниеносный донат, все пришло сразу после оплаты. Быстро и четко!",
    "Быстро, качественно, надежно. Донат пришел за пару минут!"
]

# ========== КРАСИВЫЕ КЛАВИАТУРЫ С СИНИМ ДИЗАЙНОМ ==========

# Главное меню
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton(text="🛒 Купить донат", callback_data="buy_donate")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")],
        [InlineKeyboardButton(text="📝 О нас", callback_data="about")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Меню админа с синим дизайном
def get_admin_menu():
    keyboard = [
        [InlineKeyboardButton(text="📊 Статистика бота", callback_data="admin_stats")],
        [InlineKeyboardButton(text="💰 Изменить курс", callback_data="change_rate")],
        [InlineKeyboardButton(text="⭐ Создать отзывы", callback_data="create_fake_reviews")],
        [InlineKeyboardButton(text="📨 Чеки на проверку", callback_data="check_pending")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Меню покупки
def get_buy_menu():
    keyboard = [
        [InlineKeyboardButton(text="🎮 Black Russia", callback_data="buy_black_russia")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Кнопка "Назад" синяя
def get_back_button():
    keyboard = [[InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Клавиатура отмены
def get_cancel_keyboard():
    keyboard = [[InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Кнопки поддержки (ссылка)
def get_support_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="💬 Написать в поддержку", url="https://t.me/starfizovoi")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Кнопки "О нас" (ссылка на отзывы)
def get_about_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="⭐ Читать отзывы", url="https://nezeexdonate.t.me")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Кнопки оплаты
def get_payment_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data="confirm_payment")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Кнопки профиля
def get_profile_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="profile")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Кнопки админа для чеков
def get_admin_checks_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="check_pending")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ========== КРАСИВЫЕ СООБЩЕНИЯ ==========

# Приветственное сообщение с HTML-разметкой
WELCOME_MESSAGE = """
<b>🌟 Добро пожаловать в <span class='tg-spoiler'>DONATE SERVICE</span>! 🌟</b>

🚀 <b>Самый быстрый донат для игр!</b>

<code>────────────────────</code>

✨ <b>Наши преимущества:</b>
• ⚡ Мгновенная доставка
• 💎 Выгодные курсы
• 🛡️ Гарантия безопасности
• 📞 Круглосуточная поддержка

🎮 <b>Поддерживаемые игры:</b>
• Black Russia

<code>────────────────────</code>

👇 <b>Выберите действие:</b>
"""

# Сообщение о покупке доната
BUY_DONATE_MESSAGE = """
<b>🛒 КУПИТЬ ДОНАТ</b>

<code>────────────────────</code>

🎮 <b>Выберите игру для пополнения:</b>

👇 Нажмите на кнопку ниже:
"""

# Сообщение Black Russia
BLACK_RUSSIA_MESSAGE = """
<b>🎮 BLACK RUSSIA</b>

<code>────────────────────</code>

💰 <b>Введите количество Black Coin:</b>
• От <b>30</b> до <b>10000</b> BC
• Курс: <b>1 BC = {rate}₽</b>

⚠️ <i>При X2 в игре получите X2 доната!</i>

👇 <b>Отправьте число в чат:</b>
"""

# Сообщение с реквизитами
PAYMENT_DETAILS_MESSAGE = """
<b>💳 ОПЛАТА</b>

<code>────────────────────</code>

📋 <b>Детали заказа:</b>
🎮 Игра: <b>Black Russia</b>
💰 Black Coin: <b>{bc_amount} BC</b>
💸 Сумма к оплате: <b>{total_price:.2f}₽</b>
📊 Курс: <b>1 BC = {rate}₽</b>

<code>────────────────────</code>

💳 <b>Реквизиты для оплаты:</b>
<code>{card_number}</code>

<code>────────────────────</code>

📸 <b>После оплаты:</b>
1. Сделайте скриншот чека
2. Отправьте его в этот чат
3. Админ проверит и зачислит донат

⏱️ <i>Обычная проверка: 1-5 минут</i>
"""

# Профиль пользователя
def get_profile_message(user_data):
    total_spent = sum(p["total_price"] for p in user_data["purchases"] if p.get("status") == "approved")
    approved_purchases = [p for p in user_data["purchases"] if p.get("status") == "approved"]
    
    message = """
<b>👤 МОЙ ПРОФИЛЬ</b>

<code>────────────────────</code>

📛 <b>Имя:</b> {username}
🆔 <b>ID:</b> <code>{user_id}</code>
📅 <b>Дата регистрации:</b> {join_date}
💰 <b>Всего потрачено:</b> {total_spent:.2f}₽
🛒 <b>Количество покупок:</b> {purchases_count}

<code>────────────────────</code>
<b>📋 ИСТОРИЯ ПОКУПОК:</b>
""".format(
        username=user_data['username'],
        user_id=user_data['id'],
        join_date=user_data['join_date'],
        total_spent=total_spent,
        purchases_count=len(approved_purchases)
    )
    
    if user_data["purchases"]:
        for i, purchase in enumerate(user_data["purchases"][-5:][::-1], 1):  # Последние 5 покупок в обратном порядке
            status_icon = "✅" if purchase.get("status") == "approved" else "⏳" if purchase.get("status") == "pending" else "❌"
            message += f"\n{i}. {purchase['timestamp']} - {purchase['bc_amount']} BC ({purchase['total_price']:.2f}₽) {status_icon}"
    else:
        message += "\n📭 Пока нет покупок"
    
    return message

# Сообщение поддержки
SUPPORT_MESSAGE = """
<b>🆘 ПОДДЕРЖКА</b>

<code>────────────────────</code>

📞 <b>Мы всегда на связи!</b>

⚡ <b>По всем вопросам:</b>
• Проблемы с оплатой
• Задержка доната
• Технические вопросы
• Сотрудничество

<code>────────────────────</code>

👇 <b>Нажмите кнопку ниже для связи:</b>

⏱️ <i>Среднее время ответа: 5-15 минут</i>
"""

# Сообщение "О нас"
ABOUT_MESSAGE = """
<b>📝 О НАС</b>

<code>────────────────────</code>

🚀 <b>DONATE SERVICE</b> - лидер на рынке игровых пополнений!

✨ <b>Наша миссия:</b>
Предоставлять быстрые, надежные и безопасные услуги пополнения игровых валют.

<code>────────────────────</code>

🏆 <b>Наши достижения:</b>
• 🎯 1000+ довольных клиентов
• ⚡ Среднее время доставки: 3 минуты
• 💯 99% положительных отзывов
• 🔒 Полная безопасность транзакций

<code>────────────────────</code>

👇 <b>Читайте отзывы реальных клиентов:</b>
"""

# Сообщение админа о статистике
def get_admin_stats_message():
    total_users = len(users_data)
    total_purchases = len([p for p in purchases_history if p.get("status") == "approved"])
    total_pending = len([p for p in purchases_history if p.get("status") == "pending"])
    total_revenue = sum(p["total_price"] for p in purchases_history if p.get("status") == "approved")
    
    return """
<b>👑 АДМИН ПАНЕЛЬ | 📊 СТАТИСТИКА</b>

<code>────────────────────</code>

👥 <b>Пользователи:</b> {total_users}
✅ <b>Успешных покупок:</b> {total_purchases}
⏳ <b>Ожидают проверки:</b> {total_pending}
💰 <b>Общая выручка:</b> {total_revenue:.2f}₽
📈 <b>Текущий курс:</b> 1 BC = {current_rate}₽

<code>────────────────────</code>

⏰ <b>Данные на:</b> {current_time}
""".format(
        total_users=total_users,
        total_purchases=total_purchases,
        total_pending=total_pending,
        total_revenue=total_revenue,
        current_rate=CURRENT_RATE,
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

# ========== ОСНОВНЫЕ ОБРАБОТЧИКИ ==========

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Сохраняем пользователя
    if user_id not in users_data:
        users_data[user_id] = {
            "id": user_id,
            "username": username,
            "join_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "purchases": []
        }
    
    # Очищаем состояние пользователя
    if user_id in user_state:
        del user_state[user_id]
    
    # Проверка на админа
    if user_id == ADMIN_ID:
        keyboard = get_admin_menu()
        await message.answer("<b>👑 ДОБРО ПОЖАЛОВАТЬ, АДМИНИСТРАТОР!</b>\n\n<code>────────────────────</code>\n👇 <b>Выберите действие:</b>", 
                          parse_mode='HTML', reply_markup=keyboard)
    else:
        await message.answer(WELCOME_MESSAGE, parse_mode='HTML', reply_markup=get_main_menu())

# Команда /admin
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("<b>👑 АДМИН ПАНЕЛЬ</b>\n\n<code>────────────────────</code>\n👇 <b>Выберите действие:</b>", 
                          parse_mode='HTML', reply_markup=get_admin_menu())

# Главное меню
@dp.callback_query(F.data == "main_menu")
async def main_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    # Очищаем состояние пользователя
    if user_id in user_state:
        del user_state[user_id]
    
    if user_id == ADMIN_ID:
        await callback.message.edit_text(
            "<b>👑 АДМИН ПАНЕЛЬ</b>\n\n<code>────────────────────</code>\n👇 <b>Выберите действие:</b>",
            parse_mode='HTML',
            reply_markup=get_admin_menu()
        )
    else:
        await callback.message.edit_text(
            WELCOME_MESSAGE,
            parse_mode='HTML',
            reply_markup=get_main_menu()
        )
    await callback.answer()

# Купить донат
@dp.callback_query(F.data == "buy_donate")
async def buy_donate(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_state[user_id] = "awaiting_game_choice"
    
    await callback.message.edit_text(
        BUY_DONATE_MESSAGE,
        parse_mode='HTML',
        reply_markup=get_buy_menu()
    )
    await callback.answer()

# Black Russia
@dp.callback_query(F.data == "buy_black_russia")
async def black_russia(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_state[user_id] = "awaiting_bc_amount"
    
    await callback.message.edit_text(
        BLACK_RUSSIA_MESSAGE.format(rate=CURRENT_RATE),
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

# Обработка текстовых сообщений
@dp.message(F.text)
async def handle_text_messages(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Проверяем, является ли сообщение числом
    if text.isdigit():
        # Админ: ожидание количества отзывов
        if user_id == ADMIN_ID and ADMIN_ID in admin_state and admin_state[ADMIN_ID] == "awaiting_reviews_count":
            await process_reviews_count(message, int(text))
            return
        
        # Админ: ожидание курса
        elif user_id == ADMIN_ID and ADMIN_ID in admin_state and admin_state[ADMIN_ID] == "awaiting_rate":
            await process_rate_change(message, text)
            return
        
        # Пользователь: ожидание количества BC
        elif user_id in user_state and user_state[user_id] == "awaiting_bc_amount":
            await process_bc_amount(message, int(text))
            return
    
    # Обработка ошибок для админа
    elif user_id == ADMIN_ID and ADMIN_ID in admin_state:
        if admin_state[ADMIN_ID] == "awaiting_reviews_count":
            await message.answer("❌ <b>Ошибка!</b>\nВведите число от 1 до 20", parse_mode='HTML')
        elif admin_state[ADMIN_ID] == "awaiting_rate":
            await message.answer("❌ <b>Ошибка!</b>\nВведите корректное число (например: 0.65)", parse_mode='HTML')
    
    # Обработка ошибок для пользователя
    elif user_id in user_state and user_state[user_id] == "awaiting_bc_amount":
        await message.answer("❌ <b>Ошибка!</b>\nВведите число от 30 до 10000", 
                          parse_mode='HTML', reply_markup=get_cancel_keyboard())

# Обработка количества BC
async def process_bc_amount(message: types.Message, bc_amount: int):
    user_id = message.from_user.id
    
    # Проверка диапазона
    if bc_amount < 30:
        await message.answer("❌ <b>Минимальная сумма:</b> 30 BC\n👇 Попробуйте еще раз:", 
                          parse_mode='HTML', reply_markup=get_cancel_keyboard())
        return
    elif bc_amount > 10000:
        await message.answer("❌ <b>Максимальная сумма:</b> 10000 BC\n👇 Попробуйте еще раз:", 
                          parse_mode='HTML', reply_markup=get_cancel_keyboard())
        return
    
    # Расчет стоимости
    total_price = bc_amount * CURRENT_RATE
    
    # Сохраняем временные данные
    users_data[user_id]["temp_purchase"] = {
        "bc_amount": bc_amount,
        "total_price": total_price,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Меняем состояние пользователя
    user_state[user_id] = "awaiting_payment_confirmation"
    
    await message.answer(
        PAYMENT_DETAILS_MESSAGE.format(
            bc_amount=bc_amount,
            total_price=total_price,
            rate=CURRENT_RATE,
            card_number=CARD_NUMBER
        ),
        parse_mode='HTML',
        reply_markup=get_payment_keyboard()
    )

# Подтверждение оплаты
@dp.callback_query(F.data == "confirm_payment")
async def confirm_payment(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_state[user_id] = "awaiting_receipt"
    
    await callback.message.edit_text(
        "<b>📤 ОТПРАВЬТЕ ЧЕК</b>\n\n<code>────────────────────</code>\n"
        "📸 <b>Прикрепите скриншот чека об оплате</b>\n\n"
        "<i>Админ проверит и подтвердит ваш донат в течение 1-5 минут</i>",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

# Обработка фото (чеков)
@dp.message(F.photo)
async def process_receipt(message: types.Message):
    user_id = message.from_user.id
    
    # Проверяем, ожидает ли пользователь отправки чека
    if user_id not in user_state or user_state[user_id] != "awaiting_receipt":
        await message.answer("❌ <b>Сначала создайте заказ через меню</b>", 
                          parse_mode='HTML', reply_markup=get_main_menu())
        return
    
    if user_id not in users_data or "temp_purchase" not in users_data[user_id]:
        await message.answer("❌ <b>Сначала создайте заказ через меню</b>", 
                          parse_mode='HTML', reply_markup=get_main_menu())
        return
    
    purchase_data = users_data[user_id]["temp_purchase"]
    
    # Добавляем в историю покупок
    purchase_record = {
        "user_id": user_id,
        "username": users_data[user_id]["username"],
        "bc_amount": purchase_data["bc_amount"],
        "total_price": purchase_data["total_price"],
        "timestamp": purchase_data["timestamp"],
        "status": "pending"
    }
    
    purchases_history.append(purchase_record)
    users_data[user_id]["purchases"].append(purchase_record)
    
    # Отправляем админу на проверку
    check_info = {
        "user_id": user_id,
        "username": users_data[user_id]["username"],
        "bc_amount": purchase_data["bc_amount"],
        "total_price": purchase_data["total_price"],
        "message_id": message.message_id,
        "chat_id": message.chat.id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    pending_checks.append(check_info)
    
    # Уведомление админу
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"approve_check_{len(pending_checks)-1}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_check_{len(pending_checks)-1}")
        ]
    ])
    
    try:
        await bot.send_photo(
            chat_id=ADMIN_ID,
            photo=message.photo[-1].file_id,
            caption=f"📨 <b>НОВЫЙ ЧЕК НА ПРОВЕРКУ!</b>\n\n"
                   f"👤 <b>Пользователь:</b> @{users_data[user_id]['username']} (ID: {user_id})\n"
                   f"🎮 <b>Игра:</b> Black Russia\n"
                   f"💰 <b>Black Coin:</b> {purchase_data['bc_amount']} BC\n"
                   f"💸 <b>Сумма:</b> {purchase_data['total_price']:.2f}₽\n"
                   f"⏰ <b>Время:</b> {purchase_data['timestamp']}",
            parse_mode='HTML',
            reply_markup=admin_keyboard
        )
    except Exception as e:
        logger.error(f"Ошибка отправки админу: {e}")
    
    # Очищаем состояние пользователя
    if user_id in user_state:
        del user_state[user_id]
    
    # Ответ пользователю
    await message.answer(
        "✅ <b>ЧЕК ПОЛУЧЕН!</b>\n\n"
        "<code>────────────────────</code>\n"
        "📨 <b>Отправлен на проверку админу</b>\n\n"
        "⏱️ <i>Обычное время проверки: 1-5 минут</i>\n"
        "🔔 <i>Вы получите уведомление, когда донат будет зачислен</i>",
        parse_mode='HTML',
        reply_markup=get_main_menu()
    )
    
    # Очищаем временные данные
    if "temp_purchase" in users_data[user_id]:
        del users_data[user_id]["temp_purchase"]

# Профиль
@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id not in users_data:
        users_data[user_id] = {
            "id": user_id,
            "username": callback.from_user.username or callback.from_user.first_name,
            "join_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "purchases": []
        }
    
    profile_text = get_profile_message(users_data[user_id])
    
    await callback.message.edit_text(
        profile_text,
        parse_mode='HTML',
        reply_markup=get_profile_keyboard()
    )
    await callback.answer()

# Поддержка
@dp.callback_query(F.data == "support")
async def support(callback: types.CallbackQuery):
    await callback.message.edit_text(
        SUPPORT_MESSAGE,
        parse_mode='HTML',
        reply_markup=get_support_keyboard()
    )
    await callback.answer()

# О нас
@dp.callback_query(F.data == "about")
async def about(callback: types.CallbackQuery):
    await callback.message.edit_text(
        ABOUT_MESSAGE,
        parse_mode='HTML',
        reply_markup=get_about_keyboard()
    )
    await callback.answer()

# ========== АДМИН ПАНЕЛЬ ==========

# Статистика
@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    stats_message = get_admin_stats_message()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_stats")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")]
    ])
    
    await callback.message.edit_text(stats_message, parse_mode='HTML', reply_markup=keyboard)
    await callback.answer()

# Изменение курса
@dp.callback_query(F.data == "change_rate")
async def change_rate(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    admin_state[ADMIN_ID] = "awaiting_rate"
    
    await callback.message.edit_text(
        f"<b>💰 ИЗМЕНЕНИЕ КУРСА</b>\n\n"
        f"<code>────────────────────</code>\n"
        f"📊 <b>Текущий курс:</b> 1 BC = {CURRENT_RATE}₽\n\n"
        f"👇 <b>Введите новый курс (в рублях):</b>\n"
        f"<i>Пример: 0.65</i>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")]
        ])
    )
    await callback.answer()

# Обработка изменения курса
async def process_rate_change(message: types.Message, text: str):
    global CURRENT_RATE
    try:
        new_rate = float(text.replace(',', '.'))
        if new_rate > 0:
            CURRENT_RATE = new_rate
            del admin_state[ADMIN_ID]
            
            await message.answer(
                f"✅ <b>КУРС ИЗМЕНЕН!</b>\n\n"
                f"<code>────────────────────</code>\n"
                f"📈 <b>Новый курс:</b> 1 BC = {CURRENT_RATE}₽",
                parse_mode='HTML',
                reply_markup=get_admin_menu()
            )
        else:
            await message.answer("❌ <b>Курс должен быть больше 0</b>", parse_mode='HTML')
    except ValueError:
        await message.answer("❌ <b>Введите корректное число (например: 0.65)</b>", parse_mode='HTML')

# Создание фейк отзывов
@dp.callback_query(F.data == "create_fake_reviews")
async def create_fake_reviews(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    admin_state[ADMIN_ID] = "awaiting_reviews_count"
    
    await callback.message.edit_text(
        "<b>⭐ СОЗДАНИЕ ОТЗЫВОВ</b>\n\n"
        "<code>────────────────────</code>\n"
        "👇 <b>Введите количество отзывов:</b>\n"
        "• От <b>1</b> до <b>20</b>\n"
        "• Каждый отзыв в отдельном сообщении\n\n"
        "<i>Все отзывы будут с ключевыми словами: 'быстрый', 'донат'</i>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")]
        ])
    )
    await callback.answer()

# Обработка количества отзывов
async def process_reviews_count(message: types.Message, count: int):
    if 1 <= count <= 20:
        del admin_state[ADMIN_ID]
        
        await message.answer(f"✅ <b>Создаю {count} отзывов...</b>\n<code>────────────────────</code>", parse_mode='HTML')
        
        # Создаем фейк отзывы
        for i in range(count):
            review = random.choice(FAKE_REVIEWS)
            await message.answer(f"⭐ <b>Отзыв {i+1}:</b>\n{review}", parse_mode='HTML')
            await asyncio.sleep(0.3)  # Небольшая задержка
        
        await message.answer(
            f"✅ <b>ГОТОВО!</b>\n\n"
            f"<code>────────────────────</code>\n"
            f"🎉 Успешно создано <b>{count}</b> отзывов!",
            parse_mode='HTML',
            reply_markup=get_admin_menu()
        )
    else:
        await message.answer("❌ <b>Введите число от 1 до 20</b>", parse_mode='HTML')

# Просмотр чеков на проверку
@dp.callback_query(F.data == "check_pending")
async def check_pending(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    if not pending_checks:
        await callback.message.edit_text(
            "<b>📨 ЧЕКИ НА ПРОВЕРКУ</b>\n\n"
            "<code>────────────────────</code>\n"
            "📭 <b>Нет чеков, ожидающих проверки</b>\n\n"
            "<i>Все чеки обработаны</i>",
            parse_mode='HTML',
            reply_markup=get_admin_checks_keyboard()
        )
    else:
        checks_text = "<b>📨 ЧЕКИ НА ПРОВЕРКУ</b>\n\n<code>────────────────────</code>\n\n"
        for i, check in enumerate(pending_checks, 1):
            checks_text += f"{i}. @{check['username']} - {check['bc_amount']} BC ({check['total_price']:.2f}₽)\n   ⏰ {check['timestamp']}\n\n"
        
        checks_text += f"<code>────────────────────</code>\n<b>Всего:</b> {len(pending_checks)} чеков"
        
        await callback.message.edit_text(
            checks_text,
            parse_mode='HTML',
            reply_markup=get_admin_checks_keyboard()
        )
    await callback.answer()

# Подтверждение/отклонение чека
@dp.callback_query(F.data.startswith("approve_check_") | F.data.startswith("reject_check_"))
async def process_check_decision(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    action = "approve" if callback.data.startswith("approve_check_") else "reject"
    check_index = int(callback.data.split("_")[-1])
    
    if 0 <= check_index < len(pending_checks):
        check = pending_checks[check_index]
        
        # Обновляем статус в истории покупок
        for purchase in purchases_history:
            if (purchase["user_id"] == check["user_id"] and 
                purchase["bc_amount"] == check["bc_amount"] and
                purchase["total_price"] == check["total_price"]):
                purchase["status"] = "approved" if action == "approve" else "rejected"
                
                # Обновляем у пользователя
                if check["user_id"] in users_data:
                    for user_purchase in users_data[check["user_id"]]["purchases"]:
                        if (user_purchase["bc_amount"] == check["bc_amount"] and
                            user_purchase["total_price"] == check["total_price"]):
                            user_purchase["status"] = "approved" if action == "approve" else "rejected"
        
        # Уведомляем пользователя
        status_text = "✅ <b>Ваш платеж подтвержден!</b>\n🎮 Донат зачислен в игру." if action == "approve" else "❌ <b>Ваш платеж отклонен.</b>\n📞 Свяжитесь с поддержкой @starfizovoi"
        
        try:
            await bot.send_message(
                chat_id=check["user_id"],
                text=f"<b>📢 СТАТУС ЗАКАЗА</b>\n\n<code>────────────────────</code>\n{status_text}",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Ошибка отправки пользователю: {e}")
        
        # Удаляем из ожидающих
        del pending_checks[check_index]
        
        await callback.message.edit_text(
            f"✅ <b>ЧЕК {'ПОДТВЕРЖДЕН' if action == 'approve' else 'ОТКЛОНЕН'}!</b>\n\n"
            f"<code>────────────────────</code>\n"
            f"👤 Пользователь: @{check['username']}\n"
            f"💰 Сумма: {check['total_price']:.2f}₽\n"
            f"⏰ Время: {check['timestamp']}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📨 К чекам", callback_data="check_pending")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")]
            ])
        )
    
    await callback.answer()

# Админ меню
@dp.callback_query(F.data == "admin_menu")
async def admin_menu(callback: types.CallbackQuery):
    if callback.from_user.id == ADMIN_ID:
        await callback.message.edit_text(
            "<b>👑 АДМИН ПАНЕЛЬ</b>\n\n<code>────────────────────</code>\n👇 <b>Выберите действие:</b>",
            parse_mode='HTML',
            reply_markup=get_admin_menu()
        )
    await callback.answer()

# Запуск бота
async def main():
    logger.info("🚀 Бот запущен!")
    logger.info(f"👑 Админ ID: {ADMIN_ID}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
