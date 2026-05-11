import asyncio
import os
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Валидация конфигурации
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")
if not WEATHER_API_KEY:
    logging.warning("WEATHER_API_KEY не найден — погода не будет работать")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==================== КЛАВИАТУРЫ ====================
def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Погода", callback_data="weather")],
        [InlineKeyboardButton(text="Новости", callback_data="news")],
        [InlineKeyboardButton(text="О боте", callback_data="info")]
    ])

# ==================== ОБРАБОТЧИКИ ====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я информационный помощник.\nВыбери действие:",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data == "weather")
async def callback_weather(callback: CallbackQuery):
    city = "Moscow"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    
    await callback.answer()
    
    if not WEATHER_API_KEY:
        await callback.message.edit_text("API-ключ погоды не настроен.")
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    raise Exception(f"API returned {response.status}")
                    
                data = await response.json()
                temp = data.get("main", {}).get("temp", "N/A")
                desc = data.get("weather", [{}])[0].get("description", "нет данных")
                city_name = data.get("name", city)
                
                await callback.message.edit_text(
                    f"Погода в {city_name}:\n"
                    f"{temp}°C\n"
                    f"{desc.capitalize()}"
                )
    except asyncio.TimeoutError:
        await callback.message.edit_text("⏱ Таймаут при запросе к погодному API.")
    except Exception as e:
        logging.error(f"Weather API error: {e}")
        await callback.message.edit_text("Ошибка при получении данных о погоде.")

@dp.callback_query(F.data == "news")
async def callback_news(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "Раздел новостей находится в разработке.\n"
        "План: интеграция с RSS-лентами или NewsAPI в следующем релизе."
    )

@dp.callback_query(F.data == "info")
async def callback_info(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "Бот v1.0\n"
        "Разработан в рамках индивидуального проекта\n"
        "Стек: Python 3.10+, aiogram 3.x, aiohttp\n"
        "Автор: Мищенко Эльдар"
    )

# ==================== ЗАПУСК ====================
async def main():
    logging.info("🚀 Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем")
    except Exception as e:
        logging.critical(f"Критическая ошибка: {e}")
