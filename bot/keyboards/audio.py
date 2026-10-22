from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Optional


def get_audio_menu_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for audio menu"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎵 BGM", callback_data="audio_bgm_menu")],
            [InlineKeyboardButton(text="🔊 SFX", callback_data="audio_sfx_menu")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="audio_close")],
        ]
    )
    return keyboard


def get_bgm_keyboard(bgm: Optional[Dict]) -> InlineKeyboardMarkup:
    """Keyboard for BGM management"""
    buttons = []
    if bgm:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🎵 {bgm['filename']} (громкость: {bgm['volume']:.2f})",
                    callback_data="bgm_info",
                )
            ]
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text="🔊 Изменить громкость", callback_data="bgm_volume"
                )
            ]
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text="🗑 Удалить BGM", callback_data=f"bgm_delete_{bgm['id']}"
                )
            ]
        )
    else:
        buttons.append(
            [InlineKeyboardButton(text="➕ Добавить BGM", callback_data="bgm_add")]
        )
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="audio_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_sfx_keyboard(sfx_list: List[Dict], project_id: int) -> InlineKeyboardMarkup:
    """Keyboard for SFX management"""
    buttons = []
    for sfx in sfx_list:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🔊 {sfx['at_sec']:.1f}с: {sfx['filename']}",
                    callback_data=f"sfx_edit_{sfx['id']}",
                )
            ]
        )
    buttons.append(
        [InlineKeyboardButton(text="➕ Добавить SFX", callback_data="sfx_add")]
    )
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="audio_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_sfx_actions_keyboard(sfx_id: int) -> InlineKeyboardMarkup:
    """Keyboard for SFX actions"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать", callback_data=f"sfx_edit_{sfx_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить", callback_data=f"sfx_delete_{sfx_id}"
                )
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="sfx_cancel")],
        ]
    )
    return keyboard
