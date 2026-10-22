from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict


def get_assets_keyboard(assets: List[Dict], project_id: int) -> InlineKeyboardMarkup:
    """Keyboard for managing assets"""
    buttons = []
    for asset in assets:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🗑 {asset['alias']}: {asset['filename']}",
                    callback_data=f"asset_delete_{asset['id']}",
                )
            ]
        )
    buttons.append(
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="asset_close")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)
