from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict


def get_projects_keyboard(projects: List[Dict]) -> InlineKeyboardMarkup:
    """Keyboard for selecting a project"""
    buttons = []
    for project in projects:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"✅ {project['title']} ({project['status']})",
                    callback_data=f"project_select_{project['id']}",
                )
            ]
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"✏️ Редактировать {project['title']}",
                    callback_data=f"project_edit_{project['id']}",
                ),
                InlineKeyboardButton(
                    text=f"🗑 Удалить",
                    callback_data=f"project_delete_{project['id']}",
                ),
            ]
        )
    buttons.append(
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="project_cancel")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_project_actions_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Keyboard for project actions"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать", callback_data=f"project_edit_{project_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить", callback_data=f"project_delete_{project_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Выбрать", callback_data=f"project_select_{project_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Клонировать", callback_data=f"project_clone_{project_id}"
                )
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="project_cancel")],
        ]
    )
    return keyboard
