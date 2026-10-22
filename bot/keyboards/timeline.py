from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict


def get_timeline_keyboard(
    segments: List[Dict], project_id: int
) -> InlineKeyboardMarkup:
    """Keyboard for managing timeline segments"""
    buttons = []
    for i, segment in enumerate(segments, 1):
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{i}. {segment['asset_alias']} {segment['in_sec']:.1f}→{segment['out_sec']:.1f}",
                    callback_data=f"segment_edit_{segment['id']}",
                )
            ]
        )
    buttons.append(
        [InlineKeyboardButton(text="➕ Добавить сегмент", callback_data="segment_add")]
    )
    buttons.append(
        [InlineKeyboardButton(text="📊 Просмотр", callback_data="timeline_preview")]
    )
    buttons.append(
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="timeline_close")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_timeline_empty_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for empty timeline"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить сегмент", callback_data="segment_add"
                )
            ],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="timeline_close")],
        ]
    )
    return keyboard


def get_segment_actions_keyboard(
    segment_id: int, mute_audio: bool = False
) -> InlineKeyboardMarkup:
    """Keyboard for segment actions"""
    mute_text = "🔇 Включить звук" if mute_audio else "🔊 Выключить звук"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать", callback_data=f"segment_edit_{segment_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text=mute_text, callback_data=f"segment_mute_toggle_{segment_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬆️ Вверх", callback_data=f"segment_move_up_{segment_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬇️ Вниз", callback_data=f"segment_move_down_{segment_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить", callback_data=f"segment_delete_{segment_id}"
                )
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="segment_cancel")],
        ]
    )
    return keyboard
