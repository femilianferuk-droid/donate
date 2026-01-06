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

# Хранилище данных (в реальном проекте используйте БД)
users_data = {}
purchases_history = []
pending_checks = []  # Чеки на проверку
admin_state = {}  # Состояния для админ-команд

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

# Главное меню
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton(text="🛒 Купить донат", callback_data="buy_donate")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")],
        [InlineKeyboardButton(text="📝 О нас", callback_data="about")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Меню админа
def get_admin_menu():
    keyboard = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="💰 Изменить курс", callback_data="change_rate")],
        [InlineKeyboardButton(text="⭐ Создать фейк отзывы", callback_data="create_fake_reviews")],
        [InlineKeyboardButton(text="📨 Чеки на проверку", callback_data="check_pending")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Меню покупки
def get_buy_menu():
    keyboard = [
        [InlineKeyboardButton(text="🎮 Black Russia", callback_data="buy_black_russia")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Клавиатура для отмены
def get_cancel_keyboard():
    keyboard = [[InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

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
    
    # Проверка на админа
    if user_id == ADMIN_ID:
        keyboard = get_admin_menu()
        await message.answer(f"👑 Добро пожаловать, администратор!", reply_markup=keyboard)
    else:
        await message.answer(
            f"👋 Привет, {username}!\n"
            f"Добро пожаловать в бота для покупки доната!",
            reply_markup=get_main_menu()
        )

# Команда /admin (только для админа)
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("👑 Панель администратора", reply_markup=get_admin_menu())

# Обработчик главного меню
@dp.callback_query(F.data == "main_menu")
async def main_menu(callback: types.CallbackQuery):
    if callback.from_user.id == ADMIN_ID:
        await callback.message.edit_text(
            "👑 Панель администратора",
            reply_markup=get_admin_menu()
        )
    else:
        await callback.message.edit_text(
            "Главное меню:",
            reply_markup=get_main_menu()
        )
    await callback.answer()

# Купить донат
@dp.callback_query(F.data == "buy_donate")
async def buy_donate(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎮 Выберите игру:",
        reply_markup=get_buy_menu()
    )
    await callback.answer()

# Black Russia
@dp.callback_query(F.data == "buy_black_russia")
async def black_russia(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎮 Black Russia\n\n"
        "Введите количество Black Coin (от 30 до 10000):\n"
        f"📊 Текущий курс: 1 BC = {CURRENT_RATE}₽\n"
        "⚠️ При X2 в игре получите X2 доната\n\n"
        "Просто отправьте число в чат:",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

# Обработка ввода количества BC
@dp.message(F.text.regexp(r'^\d+$'))
async def process_bc_amount(message: types.Message):
    user_id = message.from_user.id
    try:
        bc_amount = int(message.text)
        
        # Проверка диапазона
        if bc_amount < 30:
            await message.answer("❌ Минимальная сумма покупки: 30 BC", reply_markup=get_cancel_keyboard())
            return
        elif bc_amount > 10000:
            await message.answer("❌ Максимальная сумма покупки: 10000 BC", reply_markup=get_cancel_keyboard())
            return
        
        # Расчет стоимости
        total_price = bc_amount * CURRENT_RATE
        
        # Сохраняем временные данные
        users_data[user_id]["temp_purchase"] = {
            "bc_amount": bc_amount,
            "total_price": total_price,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Показываем реквизиты
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Я оплатил", callback_data="confirm_payment")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]
        ])
        
        await message.answer(
            f"📋 Детали заказа:\n\n"
            f"🎮 Игра: Black Russia\n"
            f"💰 Black Coin: {bc_amount} BC\n"
            f"💸 Сумма к оплате: {total_price:.2f}₽\n"
            f"📊 Курс: 1 BC = {CURRENT_RATE}₽\n\n"
            f"💳 Реквизиты для оплаты:\n"
            f"Карта: {CARD_NUMBER}\n\n"
            f"После оплаты отправьте скриншот чека (фото) в этот чат.",
            reply_markup=keyboard
        )
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число от 30 до 10000", reply_markup=get_cancel_keyboard())

# Подтверждение оплаты
@dp.callback_query(F.data == "confirm_payment")
async def confirm_payment(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📤 Теперь отправьте скриншот чека об оплате (фото)\n"
        "Админ проверит и подтвердит ваш донат.",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

# Обработка фото (чеков)
@dp.message(F.photo)
async def process_receipt(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in users_data or "temp_purchase" not in users_data[user_id]:
        await message.answer("❌ Сначала создайте заказ через меню", reply_markup=get_main_menu())
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
            caption=f"📨 Новый чек на проверку!\n\n"
                   f"👤 Пользователь: @{users_data[user_id]['username']} (ID: {user_id})\n"
                   f"🎮 Игра: Black Russia\n"
                   f"💰 Black Coin: {purchase_data['bc_amount']} BC\n"
                   f"💸 Сумма: {purchase_data['total_price']:.2f}₽\n"
                   f"⏰ Время: {purchase_data['timestamp']}",
            reply_markup=admin_keyboard
        )
    except Exception as e:
        logger.error(f"Ошибка отправки админу: {e}")
    
    # Ответ пользователю
    await message.answer(
        "✅ Чек получен и отправлен на проверку!\n"
        "Админ проверит ваш платеж в ближайшее время.\n"
        "Вы получите уведомление, когда донат будет зачислен.",
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
    
    user_data = users_data[user_id]
    total_spent = sum(p["total_price"] for p in user_data["purchases"] if p.get("status") == "approved")
    
    profile_text = (
        f"👤 Ваш профиль:\n\n"
        f"📛 Имя: {user_data['username']}\n"
        f"🆔 ID: {user_data['id']}\n"
        f"📅 Дата регистрации: {user_data['join_date']}\n"
        f"💰 Всего потрачено: {total_spent:.2f}₽\n"
        f"🛒 Количество покупок: {len([p for p in user_data['purchases'] if p.get('status') == 'approved'])}\n\n"
        f"📋 История покупок:\n"
    )
    
    if user_data["purchases"]:
        for i, purchase in enumerate(user_data["purchases"][-5:], 1):  # Последние 5 покупок
            status_icon = "✅" if purchase.get("status") == "approved" else "⏳" if purchase.get("status") == "pending" else "❌"
            profile_text += f"{i}. {purchase['timestamp']} - {purchase['bc_amount']} BC ({purchase['total_price']:.2f}₽) {status_icon}\n"
    else:
        profile_text += "📭 Пока нет покупок"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="profile")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(profile_text, reply_markup=keyboard)
    await callback.answer()

# Поддержка
@dp.callback_query(F.data == "support")
async def support(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🆘 Поддержка\n\n"
        "По всем вопросам обращайтесь к нашему администратору:\n"
        "@starfizovoi\n\n"
        "Мы ответим вам в ближайшее время!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ])
    )
    await callback.answer()

# О нас
@dp.callback_query(F.data == "about")
async def about(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📝 О нас\n\n"
        "Мы предоставляем быстрые и надежные услуги по пополнению игровых валют.\n\n"
        "⭐ Отзывы наших клиентов:\n"
        "👉 nezeexdonate.t.me\n\n"
        "Наши преимущества:\n"
        "• Мгновенная доставка\n"
        "• Выгодные курсы\n"
        "• Круглосуточная поддержка\n"
        "• Гарантия качества",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ])
    )
    await callback.answer()

# ==================== АДМИН ПАНЕЛЬ ====================

# Статистика
@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    total_users = len(users_data)
    total_purchases = len([p for p in purchases_history if p.get("status") == "approved"])
    total_pending = len([p for p in purchases_history if p.get("status") == "pending"])
    total_revenue = sum(p["total_price"] for p in purchases_history if p.get("status") == "approved")
    
    stats_text = (
        f"📊 Статистика бота:\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"🛒 Всего покупок: {total_purchases}\n"
        f"⏳ Ожидают проверки: {total_pending}\n"
        f"💰 Общая выручка: {total_revenue:.2f}₽\n"
        f"📈 Текущий курс: 1 BC = {CURRENT_RATE}₽\n\n"
        f"📅 Данные на: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(stats_text, reply_markup=keyboard)
    await callback.answer()

# Изменение курса
@dp.callback_query(F.data == "change_rate")
async def change_rate(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    admin_state[ADMIN_ID] = "awaiting_rate"
    
    await callback.message.edit_text(
        f"💰 Изменение курса\n\n"
        f"Текущий курс: 1 BC = {CURRENT_RATE}₽\n\n"
        f"Введите новый курс (в рублях):\n"
        f"Пример: 0.65",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")]
        ])
    )
    await callback.answer()

# Создание фейк отзывов
@dp.callback_query(F.data == "create_fake_reviews")
async def create_fake_reviews(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    admin_state[ADMIN_ID] = "awaiting_reviews_count"
    
    await callback.message.edit_text(
        "⭐ Создание фейк отзывов\n\n"
        "Введите количество отзывов (от 1 до 20):\n"
        "Каждый отзыв будет отправлен в отдельном сообщении.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")]
        ])
    )
    await callback.answer()

# Просмотр чеков на проверку
@dp.callback_query(F.data == "check_pending")
async def check_pending(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    if not pending_checks:
        await callback.message.edit_text(
            "📨 Чеки на проверку\n\n"
            "Нет чеков, ожидающих проверки.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Обновить", callback_data="check_pending")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
            ])
        )
    else:
        checks_text = "📨 Чеки на проверку:\n\n"
        for i, check in enumerate(pending_checks):
            checks_text += f"{i+1}. @{check['username']} - {check['bc_amount']} BC ({check['total_price']:.2f}₽) - {check['timestamp']}\n"
        
        checks_text += f"\nВсего: {len(pending_checks)} чеков"
        
        await callback.message.edit_text(
            checks_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Обновить", callback_data="check_pending")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
            ])
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
        status_text = "✅ Ваш платеж подтвержден! Донат зачислен." if action == "approve" else "❌ Ваш платеж отклонен. Свяжитесь с поддержкой."
        
        try:
            await bot.send_message(
                chat_id=check["user_id"],
                text=f"📢 Статус вашего заказа:\n\n{status_text}"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки пользователю: {e}")
        
        # Удаляем из ожидающих
        del pending_checks[check_index]
        
        await callback.message.edit_text(
            f"✅ Чек успешно {'подтвержден' if action == 'approve' else 'отклонен'}!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📨 К чекам", callback_data="check_pending")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
            ])
        )
    
    await callback.answer()

# Админ меню
@dp.callback_query(F.data == "admin_menu")
async def admin_menu(callback: types.CallbackQuery):
    if callback.from_user.id == ADMIN_ID:
        await callback.message.edit_text(
            "👑 Панель администратора",
            reply_markup=get_admin_menu()
        )
    await callback.answer()

# Обработка текстовых сообщений от админа
@dp.message(F.from_user.id == ADMIN_ID)
async def handle_admin_messages(message: types.Message):
    global CURRENT_RATE
    
    if ADMIN_ID in admin_state:
        state = admin_state[ADMIN_ID]
        
        if state == "awaiting_rate":
            try:
                new_rate = float(message.text.replace(',', '.'))
                if new_rate > 0:
                    CURRENT_RATE = new_rate
                    del admin_state[ADMIN_ID]
                    
                    await message.answer(
                        f"✅ Курс успешно изменен!\n"
                        f"Новый курс: 1 BC = {CURRENT_RATE}₽",
                        reply_markup=get_admin_menu()
                    )
                else:
                    await message.answer("❌ Курс должен быть больше 0")
            except ValueError:
                await message.answer("❌ Пожалуйста, введите корректное число (например: 0.65)")
                
        elif state == "awaiting_reviews_count":
            try:
                count = int(message.text)
                if 1 <= count <= 20:
                    del admin_state[ADMIN_ID]
                    
                    await message.answer(f"✅ Начинаю создание {count} отзывов...")
                    
                    # Создаем фейк отзывы
                    for i in range(count):
                        review = random.choice(FAKE_REVIEWS)
                        await message.answer(f"⭐ Отзыв {i+1}: {review}")
                        await asyncio.sleep(0.5)  # Небольшая задержка между сообщениями
                    
                    await message.answer(
                        f"✅ Успешно создано {count} отзывов!",
                        reply_markup=get_admin_menu()
                    )
                else:
                    await message.answer("❌ Введите число от 1 до 20")
            except ValueError:
                await message.answer("❌ Пожалуйста, введите число от 1 до 20")

# Запуск бота
async def main():
    logger.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
