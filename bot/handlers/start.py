from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from bot.keyboards.main import get_main_menu

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    await message.answer(
        "👋 Добро пожаловать в Video Script Engine!\n\n"
        "Создавайте вертикальные видео для TikTok/Shorts через простой интерфейс.\n\n"
        "Используйте меню для навигации.",
        reply_markup=get_main_menu(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    await message.answer(
        "📖 Помощь по использованию бота:\n\n"
        "1. ➕ Создайте новый проект\n"
        "2. 📁 Загрузите видео-ассеты\n"
        "3. 🎬 Соберите таймлайн из сегментов\n"
        "4. 📝 Добавьте субтитры (опционально)\n"
        "5. 🔊 Добавьте аудио (опционально)\n"
        "6. 🚀 Запустите рендер\n\n"
        "Используйте /start для возврата в главное меню."
    )
