from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.api_client import api_client
from bot.utils.storage import get_active_project
from bot.keyboards.main import get_main_menu

router = Router()


def get_preset_keyboard(current_preset: str) -> InlineKeyboardMarkup:
    """Keyboard for preset selection"""
    presets = {"tiktok": "TikTok (9:16)", "youtube": "YouTube (16:9)"}

    buttons = []
    for preset_key, preset_name in presets.items():
        marker = "✅ " if preset_key == current_preset else "  "
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{marker}{preset_name}",
                    callback_data=f"preset_select_{preset_key}",
                )
            ]
        )
    buttons.append(
        [InlineKeyboardButton(text="❌ Отмена", callback_data="preset_cancel")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == "⚙️ Пресет")
async def preset_menu(message: Message):
    """Show preset menu"""
    project_id = get_active_project(message.from_user.id)
    if not project_id:
        await message.answer(
            "❌ Сначала выберите или создайте проект!", reply_markup=get_main_menu()
        )
        return

    try:
        project = await api_client.get_project(project_id)
        current_preset = project.get("preset", "tiktok")

        text = "⚙️ Пресет:\n\n"
        text += f"Текущий пресет: {current_preset}\n\n"
        text += "Выберите пресет:"

        await message.answer(text, reply_markup=get_preset_keyboard(current_preset))
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.callback_query(F.data.startswith("preset_select_"))
async def select_preset(callback: CallbackQuery):
    """Select a preset"""
    preset = callback.data.split("_")[-1]
    project_id = get_active_project(callback.from_user.id)

    if not project_id:
        await callback.answer("❌ Сначала выберите проект", show_alert=True)
        return

    try:
        project = await api_client.update_project(project_id, preset=preset)
        preset_names = {"tiktok": "TikTok (9:16)", "youtube": "YouTube (16:9)"}

        await callback.answer(
            f"✅ Пресет установлен: {preset_names.get(preset, preset)}"
        )
        await callback.message.edit_text(
            f"✅ Пресет установлен: {preset_names.get(preset, preset)}\n\n"
            f"Проект: {project['title']}",
            reply_markup=get_preset_keyboard(preset),
        )
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data == "preset_cancel")
async def cancel_preset(callback: CallbackQuery):
    """Cancel preset selection"""
    await callback.message.delete()
    await callback.answer()
