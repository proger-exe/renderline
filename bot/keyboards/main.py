from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu():
    """Main menu keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Новый проект"),
                KeyboardButton(text="📋 Мои проекты"),
            ],
            [KeyboardButton(text="📁 Ассеты"), KeyboardButton(text="🎬 Таймлайн")],
            [
                KeyboardButton(text="📝 Субтитры"),
                KeyboardButton(text="🔊 Аудио (BGM / SFX)"),
            ],
            [
                KeyboardButton(text="🖼️ Оверлеи"),
                KeyboardButton(text="📊 Таймлайн (просмотр)"),
            ],
            [KeyboardButton(text="⚙️ Пресет"), KeyboardButton(text="🚀 Рендер")],
        ],
        resize_keyboard=True,
        row_width=2,
    )
    return keyboard
