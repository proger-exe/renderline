from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from bot.states.timeline import TimelineStates
from bot.keyboards.timeline import (
    get_timeline_keyboard,
    get_segment_actions_keyboard,
    get_timeline_empty_keyboard,
)
from bot.utils.api_client import api_client
from bot.utils.storage import get_active_project
from bot.keyboards.main import get_main_menu
from bot.utils.timeline_preview import generate_timeline_preview

router = Router()


@router.message(F.text.in_(["🎬 Таймлайн", "📊 Таймлайн (просмотр)"]))
async def timeline_menu(message: Message):
    """Show timeline menu"""
    project_id = get_active_project(message.from_user.id)
    if not project_id:
        await message.answer(
            "❌ Сначала выберите или создайте проект!", reply_markup=get_main_menu()
        )
        return

    try:
        segments = await api_client.list_segments(project_id)
        if not segments:
            await message.answer(
                "🎬 Таймлайн пуст.\n\n" "Нажмите '➕ Добавить сегмент' для начала.",
                reply_markup=get_timeline_empty_keyboard(),
            )
            return

        # Check if it's preview request
        if message.text == "📊 Таймлайн (просмотр)":
            preview = generate_timeline_preview(segments, scale=1.0)
            total_duration = sum(seg["out_sec"] - seg["in_sec"] for seg in segments)

            text = f"📊 Таймлайн (просмотр):\n\n"
            text += f"Общая длительность: {total_duration:.1f} сек\n\n"
            text += "<code>\n"
            text += preview
            text += "\n</code>"

            await message.answer(text)
        else:
            text = "🎬 Таймлайн:\n\n"
            for i, segment in enumerate(segments, 1):
                mute_icon = "🔇" if segment.get("mute_audio", False) else "🔊"
                text += f"{i}) {mute_icon} {segment['asset_alias']} {segment['in_sec']:.1f}→{segment['out_sec']:.1f}\n"

            await message.answer(
                text, reply_markup=get_timeline_keyboard(segments, project_id)
            )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.callback_query(F.data == "segment_add")
async def add_segment_start(callback: CallbackQuery, state: FSMContext):
    """Start adding a new segment"""
    project_id = get_active_project(callback.from_user.id)
    if not project_id:
        await callback.answer("❌ Сначала выберите проект", show_alert=True)
        return

    # Get available assets
    try:
        assets = await api_client.list_assets(project_id)
        if not assets:
            await callback.answer("❌ Нет доступных ассетов", show_alert=True)
            return

        await state.update_data(project_id=project_id)
        await state.set_state(TimelineStates.waiting_for_asset_alias)

        assets_list = "\n".join([f"- {a['alias']}: {a['filename']}" for a in assets])
        await callback.message.answer(
            f"Выберите ассет (введите алиас):\n\n{assets_list}"
        )
        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.message(StateFilter(TimelineStates.waiting_for_asset_alias))
async def add_segment_asset(message: Message, state: FSMContext):
    """Process asset alias for new segment"""
    data = await state.get_data()
    project_id = data["project_id"]
    asset_alias = message.text.strip().upper()

    # Verify asset exists
    try:
        assets = await api_client.list_assets(project_id)
        asset_aliases = [a["alias"] for a in assets]
        if asset_alias not in asset_aliases:
            await message.answer(
                f"❌ Ассет '{asset_alias}' не найден. Попробуйте снова:"
            )
            return

        await state.update_data(asset_alias=asset_alias)
        await state.set_state(TimelineStates.waiting_for_in_sec)
        await message.answer("Введите время начала (IN) в секундах:")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()


@router.message(StateFilter(TimelineStates.waiting_for_in_sec))
async def add_segment_in(message: Message, state: FSMContext):
    """Process IN time for new segment"""
    try:
        in_sec = float(message.text.strip())
        if in_sec < 0:
            await message.answer(
                "❌ Время не может быть отрицательным. Попробуйте снова:"
            )
            return

        await state.update_data(in_sec=in_sec)
        await state.set_state(TimelineStates.waiting_for_out_sec)
        await message.answer("Введите время окончания (OUT) в секундах:")
    except ValueError:
        await message.answer("❌ Введите число. Попробуйте снова:")


@router.message(StateFilter(TimelineStates.waiting_for_out_sec))
async def add_segment_out(message: Message, state: FSMContext):
    """Process OUT time and create segment"""
    try:
        out_sec = float(message.text.strip())
        data = await state.get_data()

        if out_sec <= data["in_sec"]:
            await message.answer("❌ OUT должно быть больше IN. Попробуйте снова:")
            return

        # Get segments to determine order
        segments = await api_client.list_segments(data["project_id"])
        next_order = len(segments) + 1

        # Create segment
        segment = await api_client.create_segment(
            project_id=data["project_id"],
            asset_alias=data["asset_alias"],
            in_sec=data["in_sec"],
            out_sec=out_sec,
            order=next_order,
        )

        await message.answer(
            f"✅ Сегмент добавлен!\n\n"
            f"{segment['asset_alias']} {segment['in_sec']:.1f}→{segment['out_sec']:.1f}",
            reply_markup=get_main_menu(),
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число. Попробуйте снова:")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()


@router.callback_query(F.data.startswith("segment_edit_"))
async def edit_segment(callback: CallbackQuery):
    """Show segment edit options"""
    segment_id = int(callback.data.split("_")[-1])
    try:
        segment = await api_client.get_segment(segment_id)
        mute_status = (
            "🔇 Выключен" if segment.get("mute_audio", False) else "🔊 Включен"
        )
        await callback.message.answer(
            f"Сегмент:\n"
            f"Ассет: {segment['asset_alias']}\n"
            f"IN: {segment['in_sec']:.1f} сек\n"
            f"OUT: {segment['out_sec']:.1f} сек\n"
            f"Порядок: {segment['order']}\n"
            f"Звук: {mute_status}",
            reply_markup=get_segment_actions_keyboard(
                segment_id, segment.get("mute_audio", False)
            ),
        )
        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("segment_delete_"))
async def delete_segment(callback: CallbackQuery):
    """Delete a segment"""
    segment_id = int(callback.data.split("_")[-1])
    try:
        await api_client.delete_segment(segment_id)
        await callback.answer("✅ Сегмент удален")
        await callback.message.delete()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("segment_move_up_"))
async def move_segment_up(callback: CallbackQuery):
    """Move segment up"""
    segment_id = int(callback.data.split("_")[-1])
    try:
        segment = await api_client.get_segment(segment_id)
        if segment["order"] > 1:
            await api_client.move_segment(segment_id, segment["order"] - 1)
            await callback.answer("✅ Сегмент перемещен вверх")
        else:
            await callback.answer("❌ Сегмент уже первый", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("segment_move_down_"))
async def move_segment_down(callback: CallbackQuery):
    """Move segment down"""
    segment_id = int(callback.data.split("_")[-1])
    try:
        segment = await api_client.get_segment(segment_id)
        segments = await api_client.list_segments(segment["project_id"])
        if segment["order"] < len(segments):
            await api_client.move_segment(segment_id, segment["order"] + 1)
            await callback.answer("✅ Сегмент перемещен вниз")
        else:
            await callback.answer("❌ Сегмент уже последний", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("segment_mute_toggle_"))
async def toggle_segment_mute(callback: CallbackQuery):
    """Toggle mute audio for segment"""
    segment_id = int(callback.data.split("_")[-1])
    try:
        segment = await api_client.get_segment(segment_id)
        current_mute = segment.get("mute_audio", False)
        new_mute = not current_mute

        # Update segment via API
        await api_client.update_segment(segment_id, mute_audio=new_mute)

        mute_status = "🔇 Выключен" if new_mute else "🔊 Включен"
        await callback.answer(f"✅ Звук: {mute_status}")

        # Update message
        await callback.message.edit_text(
            f"Сегмент:\n"
            f"Ассет: {segment['asset_alias']}\n"
            f"IN: {segment['in_sec']:.1f} сек\n"
            f"OUT: {segment['out_sec']:.1f} сек\n"
            f"Порядок: {segment['order']}\n"
            f"Звук: {mute_status}",
            reply_markup=get_segment_actions_keyboard(segment_id, new_mute),
        )
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data == "segment_cancel")
async def cancel_segment_action(callback: CallbackQuery):
    """Cancel segment action"""
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "timeline_close")
async def close_timeline(callback: CallbackQuery):
    """Close timeline menu"""
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "timeline_preview")
async def show_timeline_preview(callback: CallbackQuery):
    """Show timeline preview"""
    project_id = get_active_project(callback.from_user.id)
    if not project_id:
        await callback.answer("❌ Сначала выберите проект", show_alert=True)
        return

    try:
        segments = await api_client.list_segments(project_id)
        if not segments:
            await callback.answer("❌ Таймлайн пуст", show_alert=True)
            return

        preview = generate_timeline_preview(segments, scale=1.0)
        total_duration = sum(seg["out_sec"] - seg["in_sec"] for seg in segments)

        text = f"📊 Таймлайн (просмотр):\n\n"
        text += f"Общая длительность: {total_duration:.1f} сек\n\n"
        text += "<code>\n"
        text += preview
        text += "\n</code>"

        await callback.message.answer(text)
        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
