import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatPermissions
from datetime import datetime, timedelta

TOKEN = "ТВОЙ_ТОКЕН"
bot = Bot(token=TOKEN)
dp = Dispatcher()

resale_topic_id = None  # ID гілки для оголошень
user_last_message_time = {}  # Час останнього повідомлення користувача
user_message_count = {}  # Лічильник повідомлень користувача


@dp.message(lambda message: message.text and message.text.startswith("/resale_topic"))
async def set_resale_topic(message: types.Message):
    global resale_topic_id
    resale_topic_id = message.message_thread_id  # Запам’ятовуємо ID гілки
    await message.answer("✅ Бот тепер контролює цю гілку на відповідність правилам.")


@dp.message(lambda message: resale_topic_id and message.message_thread_id == resale_topic_id)
async def delete_wrong_messages(message: types.Message):
    chat_admins = [admin.user.id for admin in await bot.get_chat_administrators(message.chat.id)]
    if message.from_user.id in chat_admins:
        return  # Адмінам можна все

    user_id = message.from_user.id
    current_time = datetime.now()

    # Лічильник повідомлень
    if user_id not in user_message_count:
        user_message_count[user_id] = 0
    user_message_count[user_id] += 1

    # Перевірка на дотримання КД (60 хвилин після 3 повідомлень)
    if user_message_count[user_id] > 3:
        if user_id in user_last_message_time:
            last_time = user_last_message_time[user_id]
            if current_time - last_time < timedelta(minutes=60):
                await message.delete()
                await message.answer(f"@{message.from_user.username}, ви можете надсилати повідомлення у цю гілку лише раз на 60 хвилин!")
                return

    user_last_message_time[user_id] = current_time  # Оновлення часу останнього повідомлення

    # Перевірка на відповідність правилам
    if not any(word in message.text.lower() for word in ["#куплю", "#продам"]):
        await message.delete()
        await message.answer(f"@{message.from_user.username}, ваше повідомлення було видалено, оскільки воно не містить хештегів '#куплю' або '#продам'.")
        user_message_count[user_id] -= 1  # Якщо видалено, не враховуємо у ліміті


@dp.message(lambda message: message.new_chat_members)
async def welcome_new_member(message: types.Message):
    for new_member in message.new_chat_members:
        username = f"@{new_member.username}" if new_member.username else "новий учасник"

        # Надсилаємо привітальне повідомлення
        welcome_msg = await message.answer(
            f"👋 Вітаємо, {username}! Будь ласка, ознайомтеся з правилами чату."
        )
        await asyncio.sleep(15)

        # Видаляємо привітальне і системне повідомлення
        await welcome_msg.delete()
        await message.delete()


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    dp.include_router(dp)  # Додаємо роутер у диспетчер
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
