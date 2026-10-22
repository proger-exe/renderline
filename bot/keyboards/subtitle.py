from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict


def get_subtitles_keyboard(
    subtitles: List[Dict], project_id: int
) -> InlineKeyboardMarkup:
    """Keyboard for managing subtitles"""
    buttons = []
    for subtitle in subtitles:
        text_preview = (
            subtitle["text"][:30] + "..."
            if len(subtitle["text"]) > 30
            else subtitle["text"]
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{subtitle['start_sec']:.1f}-{subtitle['end_sec']:.1f}: {text_preview}",
                    callback_data=f"subtitle_edit_{subtitle['id']}",
                )
            ]
        )
    buttons.append(
        [InlineKeyboardButton(text="➕ Добавить субтитр", callback_data="subtitle_add")]
    )
    buttons.append(
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="subtitle_close")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_time_adjust_keyboard(current_time: float, action: str) -> InlineKeyboardMarkup:
    """Keyboard for adjusting time with increments"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="−5", callback_data=f"{action}_time_-5"),
                InlineKeyboardButton(text="−1", callback_data=f"{action}_time_-1"),
                InlineKeyboardButton(
                    text=f"{current_time:.1f}", callback_data="time_display"
                ),
                InlineKeyboardButton(text="+1", callback_data=f"{action}_time_+1"),
                InlineKeyboardButton(text="+5", callback_data=f"{action}_time_+5"),
            ],
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить", callback_data=f"{action}_time_confirm"
                )
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="subtitle_cancel")],
        ]
    )
    return keyboard


def get_subtitles_empty_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for empty subtitles"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить субтитр", callback_data="subtitle_add"
                )
            ],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="subtitle_close")],
        ]
    )
    return keyboard


def get_subtitle_actions_keyboard(subtitle_id: int) -> InlineKeyboardMarkup:
    """Keyboard for subtitle actions"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать", callback_data=f"subtitle_edit_{subtitle_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить", callback_data=f"subtitle_delete_{subtitle_id}"
                )
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="subtitle_cancel")],
        ]
    )
    return keyboard
