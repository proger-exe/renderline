from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from bot.states.subtitle import SubtitleStates
from bot.keyboards.subtitle import (
    get_subtitles_keyboard,
    get_time_adjust_keyboard,
    get_subtitle_actions_keyboard,
    get_subtitles_empty_keyboard,
)
from bot.utils.api_client import api_client
from bot.utils.storage import get_active_project
from bot.keyboards.main import get_main_menu
from bot.utils.timeline_preview import calculate_total_duration

router = Router()


@router.message(F.text == "📝 Субтитры")
async def subtitles_menu(message: Message):
    """Show subtitles menu"""
    project_id = get_active_project(message.from_user.id)
    if not project_id:
        await message.answer(
            "❌ Сначала выберите или создайте проект!", reply_markup=get_main_menu()
        )
        return

    try:
        subtitles = await api_client.list_subtitles(project_id)
        if not subtitles:
            await message.answer(
                "📝 Субтитры отсутствуют.\n\n"
                "Нажмите '➕ Добавить субтитр' для начала.",
                reply_markup=get_subtitles_empty_keyboard(),
            )
            return

        text = "📝 Субтитры:\n\n"
        for subtitle in subtitles:
            text += f"{subtitle['start_sec']:.1f}–{subtitle['end_sec']:.1f}: «{subtitle['text']}»\n"

        await message.answer(
            text, reply_markup=get_subtitles_keyboard(subtitles, project_id)
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.callback_query(F.data == "subtitle_add")
async def add_subtitle_start(callback: CallbackQuery, state: FSMContext):
    """Start adding a new subtitle"""
    project_id = get_active_project(callback.from_user.id)
    if not project_id:
        await callback.answer("❌ Сначала выберите проект", show_alert=True)
        return

    # Get timeline duration for validation
    try:
        segments = await api_client.list_segments(project_id)
        total_duration = calculate_total_duration(segments)

        await state.update_data(
            project_id=project_id, total_duration=total_duration, start_sec=0.0
        )
        await state.set_state(SubtitleStates.waiting_for_start_sec)

        await callback.message.answer(
            f"Введите время начала (START) в секундах:\n"
            f"(Максимальная длительность ролика: {total_duration:.1f} сек)",
            reply_markup=get_time_adjust_keyboard(0.0, "start"),
        )
        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("start_time_"))
async def adjust_start_time(callback: CallbackQuery, state: FSMContext):
    """Adjust start time with increments"""
    data = await state.get_data()
    current_time = data.get("start_sec", 0.0)

    action = callback.data.split("_")[-1]
    if action == "confirm":
        await state.set_state(SubtitleStates.waiting_for_end_sec)
        await callback.message.edit_text(
            f"Время начала: {current_time:.1f} сек\n\n"
            f"Введите время окончания (END) в секундах:",
            reply_markup=get_time_adjust_keyboard(current_time + 2.0, "end"),
        )
        await callback.answer()
    elif action == "display":
        await callback.answer(f"Текущее время: {current_time:.1f} сек")
    else:
        increment = float(action)
        new_time = max(0.0, current_time + increment)
        await state.update_data(start_sec=new_time)
        await callback.message.edit_reply_markup(
            reply_markup=get_time_adjust_keyboard(new_time, "start")
        )
        await callback.answer()


@router.callback_query(F.data.startswith("end_time_"))
async def adjust_end_time(callback: CallbackQuery, state: FSMContext):
    """Adjust end time with increments"""
    data = await state.get_data()
    start_sec = data.get("start_sec", 0.0)
    total_duration = data.get("total_duration", 0.0)
    current_time = data.get("end_sec", start_sec + 2.0)

    action = callback.data.split("_")[-1]
    if action == "confirm":
        if current_time <= start_sec:
            await callback.answer("❌ END должно быть больше START", show_alert=True)
            return
        if current_time > total_duration:
            await callback.answer(
                f"❌ END не может превышать длительность ролика ({total_duration:.1f} сек)",
                show_alert=True,
            )
            return

        await state.set_state(SubtitleStates.waiting_for_text)
        await callback.message.edit_text(
            f"Время начала: {data['start_sec']:.1f} сек\n"
            f"Время окончания: {current_time:.1f} сек\n\n"
            f"Введите текст субтитра:"
        )
        await callback.answer()
    elif action == "display":
        await callback.answer(f"Текущее время: {current_time:.1f} сек")
    else:
        increment = float(action)
        new_time = max(start_sec + 0.1, min(total_duration, current_time + increment))
        await state.update_data(end_sec=new_time)
        await callback.message.edit_reply_markup(
            reply_markup=get_time_adjust_keyboard(new_time, "end")
        )
        await callback.answer()


@router.callback_query(F.data == "time_display")
async def display_time(callback: CallbackQuery, state: FSMContext):
    """Display current time from button"""
    data = await state.get_data()
    current_state = await state.get_state()

    if current_state == SubtitleStates.waiting_for_start_sec:
        current_time = data.get("start_sec", 0.0)
        await callback.answer(f"Текущее время начала: {current_time:.1f} сек")
    elif current_state == SubtitleStates.waiting_for_end_sec:
        start_sec = data.get("start_sec", 0.0)
        current_time = data.get("end_sec", start_sec + 2.0)
        await callback.answer(f"Текущее время окончания: {current_time:.1f} сек")
    else:
        await callback.answer()


@router.message(StateFilter(SubtitleStates.waiting_for_start_sec))
async def process_start_time(message: Message, state: FSMContext):
    """Process start time from text input"""
    try:
        start_sec = float(message.text.strip())
        if start_sec < 0:
            await message.answer(
                "❌ Время не может быть отрицательным. Попробуйте снова:"
            )
            return

        data = await state.get_data()
        total_duration = data.get("total_duration", 0.0)
        if start_sec > total_duration:
            await message.answer(
                f"❌ Время не может превышать длительность ролика ({total_duration:.1f} сек). Попробуйте снова:"
            )
            return

        await state.update_data(start_sec=start_sec)
        await state.set_state(SubtitleStates.waiting_for_end_sec)
        await message.answer(
            f"Время начала: {start_sec:.1f} сек\n\n"
            f"Введите время окончания (END) в секундах:",
            reply_markup=get_time_adjust_keyboard(start_sec + 2.0, "end"),
        )
    except ValueError:
        await message.answer("❌ Введите число. Попробуйте снова:")


@router.message(StateFilter(SubtitleStates.waiting_for_end_sec))
async def process_end_time(message: Message, state: FSMContext):
    """Process end time from text input"""
    try:
        end_sec = float(message.text.strip())
        data = await state.get_data()
        start_sec = data.get("start_sec", 0.0)
        total_duration = data.get("total_duration", 0.0)

        if end_sec <= start_sec:
            await message.answer("❌ END должно быть больше START. Попробуйте снова:")
            return

        if end_sec > total_duration:
            await message.answer(
                f"❌ END не может превышать длительность ролика ({total_duration:.1f} сек). Попробуйте снова:"
            )
            return

        await state.update_data(end_sec=end_sec)
        await state.set_state(SubtitleStates.waiting_for_text)
        await message.answer("Введите текст субтитра:")
    except ValueError:
        await message.answer("❌ Введите число. Попробуйте снова:")


@router.message(StateFilter(SubtitleStates.waiting_for_text))
async def process_subtitle_text(message: Message, state: FSMContext):
    """Process subtitle text and create subtitle"""
    text = message.text.strip()
    if not text:
        await message.answer("❌ Текст не может быть пустым. Попробуйте снова:")
        return

    try:
        data = await state.get_data()
        subtitle = await api_client.create_subtitle(
            project_id=data["project_id"],
            start_sec=data["start_sec"],
            end_sec=data["end_sec"],
            text=text,
        )

        await message.answer(
            f"✅ Субтитр добавлен!\n\n"
            f"{subtitle['start_sec']:.1f}–{subtitle['end_sec']:.1f}: «{subtitle['text']}»",
            reply_markup=get_main_menu(),
        )
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()


@router.callback_query(F.data.startswith("subtitle_edit_"))
async def edit_subtitle(callback: CallbackQuery):
    """Show subtitle edit options"""
    try:
        subtitle_id = int(callback.data.split("_")[-1])
        subtitle = await api_client.get_subtitle(subtitle_id)
        await callback.message.answer(
            f"Субтитр:\n"
            f"START: {subtitle['start_sec']:.1f} сек\n"
            f"END: {subtitle['end_sec']:.1f} сек\n"
            f"Текст: «{subtitle['text']}»",
            reply_markup=get_subtitle_actions_keyboard(subtitle_id),
        )
        await callback.answer()
    except ValueError as e:
        logger.error(f"Invalid subtitle ID in callback: {callback.data}, error: {e}")
        await callback.answer("❌ Неверный ID субтитра", show_alert=True)
    except Exception as e:
        logger.error(f"Error editing subtitle: {e}", exc_info=True)
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("subtitle_delete_"))
async def delete_subtitle(callback: CallbackQuery):
    """Delete a subtitle"""
    subtitle_id = int(callback.data.split("_")[-1])
    try:
        await api_client.delete_subtitle(subtitle_id)
        await callback.answer("✅ Субтитр удален")
        await callback.message.delete()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data == "subtitle_cancel")
async def cancel_subtitle_action(callback: CallbackQuery, state: FSMContext):
    """Cancel subtitle action"""
    await state.clear()
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "subtitle_close")
async def close_subtitles(callback: CallbackQuery):
    """Close subtitles menu"""
    await callback.message.delete()
    await callback.answer()
