from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from pathlib import Path
from bot.states.audio import AudioStates
from bot.keyboards.audio import (
    get_audio_menu_keyboard,
    get_bgm_keyboard,
    get_sfx_keyboard,
    get_sfx_actions_keyboard,
)
from bot.utils.api_client import api_client
from bot.utils.storage import get_active_project
from bot.keyboards.main import get_main_menu
from config.settings import settings

router = Router()


@router.message(F.text == "🔊 Аудио (BGM / SFX)")
async def audio_menu(message: Message):
    """Show audio menu"""
    project_id = get_active_project(message.from_user.id)
    if not project_id:
        await message.answer(
            "❌ Сначала выберите или создайте проект!", reply_markup=get_main_menu()
        )
        return

    await message.answer(
        "🔊 Управление аудио:\n\n" "Выберите тип аудио:",
        reply_markup=get_audio_menu_keyboard(),
    )


@router.callback_query(F.data == "audio_menu")
async def show_audio_menu(callback: CallbackQuery):
    """Show audio menu"""
    await callback.message.edit_text(
        "🔊 Управление аудио:\n\n" "Выберите тип аудио:",
        reply_markup=get_audio_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "audio_bgm_menu")
async def bgm_menu(callback: CallbackQuery):
    """Show BGM menu"""
    project_id = get_active_project(callback.from_user.id)
    if not project_id:
        await callback.answer("❌ Сначала выберите проект", show_alert=True)
        return

    try:
        bgm = await api_client.get_bgm(project_id)
        text = "🎵 Фоновая музыка (BGM):\n\n"
        if bgm:
            text += f"Файл: {bgm['filename']}\n"
            text += f"Громкость: {bgm['volume']:.2f}\n"
        else:
            text += "BGM не установлен.\n"
            text += "Отправьте аудиофайл для добавления."

        await callback.message.edit_text(text, reply_markup=get_bgm_keyboard(bgm))
        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data == "bgm_add")
async def bgm_add_start(callback: CallbackQuery):
    """Start adding BGM"""
    await callback.message.answer("Отправьте аудиофайл (MP3, WAV, etc.) для BGM:")
    await callback.answer()


@router.message(F.audio | F.document)
async def handle_audio_upload(message: Message):
    """Handle audio file upload (BGM or SFX)"""
    project_id = get_active_project(message.from_user.id)
    if not project_id:
        return

    # Check if it's an audio file
    is_audio = False
    file_id = None
    filename = None

    if message.audio:
        is_audio = True
        file_id = message.audio.file_id
        filename = message.audio.file_name or f"{file_id}.mp3"
    elif message.document:
        if message.document.mime_type and message.document.mime_type.startswith(
            "audio/"
        ):
            is_audio = True
            file_id = message.document.file_id
            filename = message.document.file_name or f"{file_id}.mp3"

    if not is_audio:
        return

    try:
        # Get file
        file_info = await message.bot.get_file(file_id)

        # Determine if it's BGM or SFX based on context
        # For now, assume BGM if no active state
        # In a more sophisticated implementation, we'd track the state

        # Save file
        file_path = settings.storage_audio_path / filename
        await message.bot.download_file(file_info.file_path, str(file_path))

        # Check if BGM exists
        try:
            existing_bgm = await api_client.get_bgm(project_id)
            if existing_bgm:
                # Update existing BGM
                await api_client.update_bgm(existing_bgm["id"], volume=0.25)
                await message.answer(f"✅ BGM обновлен: {filename}")
            else:
                # Create new BGM
                bgm = await api_client.create_bgm(
                    project_id=project_id,
                    filename=filename,
                    path=str(file_path),
                    volume=0.25,
                )
                await message.answer(f"✅ BGM добавлен: {filename}\nГромкость: 0.25")
        except:
            # Assume it's BGM if no existing BGM
            bgm = await api_client.create_bgm(
                project_id=project_id,
                filename=filename,
                path=str(file_path),
                volume=0.25,
            )
            await message.answer(f"✅ BGM добавлен: {filename}\nГромкость: 0.25")
    except Exception as e:
        await message.answer(f"❌ Ошибка при загрузке аудио: {str(e)}")


@router.callback_query(F.data == "bgm_volume")
async def bgm_volume_start(callback: CallbackQuery, state: FSMContext):
    """Start setting BGM volume"""
    project_id = get_active_project(callback.from_user.id)
    bgm = await api_client.get_bgm(project_id)
    if not bgm:
        await callback.answer("❌ BGM не найден", show_alert=True)
        return

    await state.update_data(bgm_id=bgm["id"], current_volume=bgm["volume"])
    await callback.message.answer(
        f"Текущая громкость: {bgm['volume']:.2f}\n\n"
        f"Введите новую громкость (0.0 - 1.0):"
    )
    await state.set_state(AudioStates.waiting_for_volume)
    await callback.answer()


@router.message(StateFilter(AudioStates.waiting_for_volume))
async def process_volume(message: Message, state: FSMContext):
    """Process volume input"""
    try:
        volume = float(message.text.strip())
        if not 0.0 <= volume <= 1.0:
            await message.answer(
                "❌ Громкость должна быть от 0.0 до 1.0. Попробуйте снова:"
            )
            return

        data = await state.get_data()
        if "bgm_id" in data:
            bgm = await api_client.update_bgm(data["bgm_id"], volume=volume)
            await message.answer(f"✅ Громкость BGM установлена: {volume:.2f}")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число от 0.0 до 1.0. Попробуйте снова:")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()


@router.callback_query(F.data.startswith("bgm_delete_"))
async def delete_bgm(callback: CallbackQuery):
    """Delete BGM"""
    bgm_id = int(callback.data.split("_")[-1])
    try:
        await api_client.delete_bgm(bgm_id)
        await callback.answer("✅ BGM удален")
        await callback.message.delete()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data == "audio_sfx_menu")
async def sfx_menu(callback: CallbackQuery):
    """Show SFX menu"""
    project_id = get_active_project(callback.from_user.id)
    if not project_id:
        await callback.answer("❌ Сначала выберите проект", show_alert=True)
        return

    try:
        sfx_list = await api_client.list_sfx(project_id)
        text = "🔊 Звуковые эффекты (SFX):\n\n"
        if not sfx_list:
            text += "SFX отсутствуют.\n"
            text += "Отправьте аудиофайл для добавления."
        else:
            for sfx in sfx_list:
                text += f"{sfx['at_sec']:.1f}с: {sfx['filename']} (громкость: {sfx['volume']:.2f})\n"

        await callback.message.edit_text(
            text, reply_markup=get_sfx_keyboard(sfx_list, project_id)
        )
        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data == "sfx_add")
async def sfx_add_start(callback: CallbackQuery, state: FSMContext):
    """Start adding SFX"""
    project_id = get_active_project(callback.from_user.id)
    await state.update_data(project_id=project_id)
    await state.set_state(AudioStates.waiting_for_sfx_time)
    await callback.message.answer(
        "Отправьте аудиофайл для SFX, затем введите время (в секундах) когда его воспроизвести:"
    )
    await callback.answer()


@router.message(StateFilter(AudioStates.waiting_for_sfx_time))
async def process_sfx_time(message: Message, state: FSMContext):
    """Process SFX time - this will be handled after file upload"""
    # This is a placeholder - actual implementation would track file upload state
    pass


@router.callback_query(F.data.startswith("sfx_delete_"))
async def delete_sfx(callback: CallbackQuery):
    """Delete SFX"""
    sfx_id = int(callback.data.split("_")[-1])
    try:
        await api_client.delete_sfx(sfx_id)
        await callback.answer("✅ SFX удален")
        await callback.message.delete()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data == "audio_close")
async def close_audio(callback: CallbackQuery):
    """Close audio menu"""
    await callback.message.delete()
    await callback.answer()
