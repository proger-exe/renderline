from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from pathlib import Path
import aiofiles
from bot.utils.api_client import api_client
from bot.utils.storage import get_active_project
from bot.utils.overlay_presets import get_preset, get_preset_names
from bot.keyboards.main import get_main_menu
from config.settings import settings

router = Router()


class OverlayStates(StatesGroup):
    waiting_for_type = State()
    waiting_for_file = State()  # For image/video
    waiting_for_text = State()
    waiting_for_preset = State()  # For text preset selection
    waiting_for_position = State()
    waiting_for_start_sec = State()
    waiting_for_end_sec = State()
    waiting_for_chromakey = State()  # For chromakey color
    # Custom text styling states
    waiting_for_font_size = State()
    waiting_for_font_color = State()
    waiting_for_background_color = State()
    waiting_for_border_radius = State()
    waiting_for_outline_width = State()
    waiting_for_outline_color = State()
    waiting_for_shadow_x = State()
    waiting_for_shadow_y = State()
    waiting_for_shadow_color = State()
    waiting_for_background_opacity = State()


@router.message(F.text == "🖼️ Оверлеи")
async def overlay_menu(message: Message):
    """Show overlay menu"""
    project_id = get_active_project(message.from_user.id)
    if not project_id:
        await message.answer(
            "❌ Сначала выберите или создайте проект!", reply_markup=get_main_menu()
        )
        return

    try:
        overlays = await api_client.list_overlays(project_id)
        text = "🖼️ Оверлеи:\n\n"
        keyboard_buttons = []

        if overlays:
            for i, overlay in enumerate(overlays, 1):
                overlay_type = overlay.get("type", "unknown")
                overlay_icon = (
                    "🖼️"
                    if overlay_type == "image"
                    else "🎬" if overlay_type == "video" else "📝"
                )
                chromakey_icon = "🎨" if overlay.get("use_chromakey") else ""
                overlay_id = overlay.get("id")
                text += f"{i}. {overlay_icon} {overlay_type}{chromakey_icon} ({overlay.get('start_sec', 0):.1f}-{overlay.get('end_sec', 0):.1f}s)\n"
                # Add button for each overlay
                keyboard_buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{i}. {overlay_icon} {overlay_type}{chromakey_icon}",
                            callback_data=f"overlay_actions_{overlay_id}",
                        )
                    ]
                )
        else:
            text += "Оверлеи отсутствуют.\n"

        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text="➕ Добавить оверлей", callback_data="overlay_add"
                )
            ]
        )
        keyboard_buttons.append(
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="overlay_cancel")]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await message.answer(text, reply_markup=keyboard)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.callback_query(F.data == "overlay_add")
async def overlay_add_start(callback: CallbackQuery, state: FSMContext):
    """Start adding overlay"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🖼️ Изображение", callback_data="overlay_type_image"
                )
            ],
            [InlineKeyboardButton(text="🎬 Видео", callback_data="overlay_type_video")],
            [InlineKeyboardButton(text="📝 Текст", callback_data="overlay_type_text")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="overlay_cancel")],
        ]
    )
    await callback.message.edit_text("Выберите тип оверлея:", reply_markup=keyboard)
    await state.set_state(OverlayStates.waiting_for_type)
    await callback.answer()


@router.callback_query(F.data == "overlay_cancel")
async def overlay_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel overlay action"""
    await state.clear()
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data.startswith("overlay_type_"))
async def overlay_type_selected(callback: CallbackQuery, state: FSMContext):
    """Handle overlay type selection"""
    overlay_type = callback.data.split("_")[-1]
    await state.update_data(type=overlay_type)

    if overlay_type in ["image", "video"]:
        await callback.message.edit_text(
            f"Отправьте {'изображение' if overlay_type == 'image' else 'видео'} для оверлея:"
        )
        await state.set_state(OverlayStates.waiting_for_file)
    else:  # text
        await callback.message.edit_text("Введите текст для оверлея:")
        await state.set_state(OverlayStates.waiting_for_text)

    await callback.answer()


@router.message(OverlayStates.waiting_for_file, F.photo | F.video | F.document)
async def overlay_file_received(message: Message, state: FSMContext):
    """Handle image/video overlay upload"""
    project_id = get_active_project(message.from_user.id)
    if not project_id:
        await message.answer("❌ Проект не найден", reply_markup=get_main_menu())
        await state.clear()
        return

    data = await state.get_data()
    overlay_type = data.get("type")

    try:
        file_id = None
        file_info = None
        file_extension = None

        if message.photo:
            # Get largest photo
            photo = message.photo[-1]
            file_info = await message.bot.get_file(photo.file_id)
            file_extension = ".jpg"
        elif message.video:
            file_info = await message.bot.get_file(message.video.file_id)
            file_extension = Path(file_info.file_path).suffix or ".mp4"
        elif message.document:
            file_info = await message.bot.get_file(message.document.file_id)
            file_extension = Path(file_info.file_path).suffix or ".jpg"

        if not file_info:
            await message.answer("❌ Не удалось получить файл. Попробуйте снова.")
            return

        # Generate filename
        filename = f"{file_info.file_id}{file_extension}"
        file_path = settings.storage_assets_path / filename

        # Download file
        await message.bot.download_file(file_info.file_path, str(file_path))

        # Save path to state
        await state.update_data(path=str(file_path), filename=filename)

        # Ask about chromakey for image/video
        if overlay_type in ["image", "video"]:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Да, использовать хромакей",
                            callback_data="overlay_chromakey_yes",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="❌ Нет", callback_data="overlay_chromakey_no"
                        )
                    ],
                ]
            )
            await message.answer(
                "Использовать хромакей (удаление фона)?\n\n"
                "Хромакей позволяет удалить фон (например, зеленый экран) из изображения/видео.",
                reply_markup=keyboard,
            )
        else:
            await state.set_state(OverlayStates.waiting_for_position)
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⬆️ Сверху", callback_data="overlay_position_top"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬇️ Снизу", callback_data="overlay_position_bottom"
                        )
                    ],
                ]
            )
            await message.answer("Выберите позицию оверлея:", reply_markup=keyboard)
    except Exception as e:
        await message.answer(f"❌ Ошибка при загрузке файла: {str(e)}")
        await state.clear()


@router.callback_query(F.data.startswith("overlay_chromakey_"))
async def overlay_chromakey_selected(callback: CallbackQuery, state: FSMContext):
    """Handle chromakey selection"""
    use_chromakey = callback.data.endswith("_yes")
    await state.update_data(use_chromakey=use_chromakey)

    if use_chromakey:
        await callback.message.edit_text(
            "Введите цвет хромакея в формате HEX (например, #00FF00 для зеленого):\n\n"
            "Популярные цвета:\n"
            "🟢 Зеленый: #00FF00\n"
            "🔵 Синий: #0000FF\n"
            "🔴 Красный: #FF0000"
        )
        await state.set_state(OverlayStates.waiting_for_chromakey)
    else:
        await state.update_data(
            chromakey_color=None, chromakey_similarity=0.3, chromakey_blend=0.1
        )
        await callback.message.edit_text("Выберите позицию оверлея:")
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬆️ Сверху", callback_data="overlay_position_top"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬇️ Снизу", callback_data="overlay_position_bottom"
                    )
                ],
            ]
        )
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await state.set_state(OverlayStates.waiting_for_position)

    await callback.answer()


@router.message(OverlayStates.waiting_for_chromakey)
async def overlay_chromakey_color_received(message: Message, state: FSMContext):
    """Handle chromakey color input"""
    color = message.text.strip()
    if not color.startswith("#"):
        color = "#" + color

    # Validate hex color
    try:
        int(color[1:], 16)
        if len(color) != 7:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Неверный формат цвета. Используйте HEX формат (например, #00FF00)"
        )
        return

    await state.update_data(
        chromakey_color=color, chromakey_similarity=0.3, chromakey_blend=0.1
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬆️ Сверху", callback_data="overlay_position_top"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬇️ Снизу", callback_data="overlay_position_bottom"
                )
            ],
        ]
    )
    await message.answer("Выберите позицию оверлея:", reply_markup=keyboard)
    await state.set_state(OverlayStates.waiting_for_position)


@router.message(OverlayStates.waiting_for_text)
async def overlay_text_received(message: Message, state: FSMContext):
    """Handle text overlay input"""
    text = message.text.strip()
    if not text:
        await message.answer("❌ Текст не может быть пустым. Попробуйте снова:")
        return

    await state.update_data(text=text)

    # Show preset selection
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎨 TikTok", callback_data="overlay_preset_tiktok"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✨ Минималистичный", callback_data="overlay_preset_minimal"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📜 Классический", callback_data="overlay_preset_classic"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Кастомный", callback_data="overlay_preset_custom"
                )
            ],
        ]
    )
    await message.answer(
        "Выберите пресет стиля для текста:\n\n"
        "🎨 TikTok - яркий фон, крупный шрифт\n"
        "✨ Минималистичный - прозрачный фон, тонкая обводка\n"
        "📜 Классический - черный фон, белый текст\n"
        "⚙️ Кастомный - настройка всех параметров",
        reply_markup=keyboard,
    )
    await state.set_state(OverlayStates.waiting_for_preset)


@router.callback_query(F.data.startswith("overlay_preset_"))
async def overlay_preset_selected(callback: CallbackQuery, state: FSMContext):
    """Handle preset selection"""
    preset_name = callback.data.split("_")[-1]
    await state.update_data(preset=preset_name)

    if preset_name == "custom":
        # Start custom configuration flow
        await callback.message.edit_text("Введите размер шрифта (например, 48):")
        await state.set_state(OverlayStates.waiting_for_font_size)
    else:
        # Apply preset configuration
        preset_config = get_preset(preset_name)
        await state.update_data(**preset_config)
        await callback.message.edit_text("Выберите позицию оверлея:")
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬆️ Сверху", callback_data="overlay_position_top"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬇️ Снизу", callback_data="overlay_position_bottom"
                    )
                ],
            ]
        )
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await state.set_state(OverlayStates.waiting_for_position)

    await callback.answer()


@router.message(OverlayStates.waiting_for_font_size)
async def overlay_font_size_received(message: Message, state: FSMContext):
    """Handle font size input for custom preset"""
    try:
        font_size = int(message.text.strip())
        if font_size < 10 or font_size > 200:
            await message.answer(
                "❌ Размер шрифта должен быть от 10 до 200. Попробуйте снова:"
            )
            return
        await state.update_data(font_size=font_size)
        await message.answer(
            "Введите цвет текста в HEX формате (например, #FFFFFF для белого):"
        )
        await state.set_state(OverlayStates.waiting_for_font_color)
    except ValueError:
        await message.answer("❌ Введите число. Попробуйте снова:")


@router.message(OverlayStates.waiting_for_font_color)
async def overlay_font_color_received(message: Message, state: FSMContext):
    """Handle font color input"""
    color = message.text.strip()
    if not color.startswith("#"):
        color = "#" + color
    try:
        int(color[1:], 16)
        if len(color) != 7:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Неверный формат цвета. Используйте HEX формат (например, #FFFFFF)"
        )
        return
    await state.update_data(font_color=color)
    await message.answer(
        "Введите цвет фона в HEX формате (или 'none' для прозрачного):"
    )
    await state.set_state(OverlayStates.waiting_for_background_color)


@router.message(OverlayStates.waiting_for_background_color)
async def overlay_background_color_received(message: Message, state: FSMContext):
    """Handle background color input"""
    bg_color = message.text.strip().lower()
    if bg_color == "none" or bg_color == "прозрачный":
        await state.update_data(background_color=None, background_opacity=0.0)
    else:
        if not bg_color.startswith("#"):
            bg_color = "#" + bg_color
        try:
            int(bg_color[1:], 16)
            if len(bg_color) != 7:
                raise ValueError
        except ValueError:
            await message.answer(
                "❌ Неверный формат цвета. Используйте HEX формат или 'none'"
            )
            return
        await state.update_data(background_color=bg_color, background_opacity=0.9)
    await message.answer(
        "Введите padding вокруг текста в пикселях (например, 20, или 0 для без отступа):\n\n"
        "Примечание: FFmpeg не поддерживает скругление углов напрямую, "
        "но этот параметр создает отступ вокруг текста."
    )
    await state.set_state(OverlayStates.waiting_for_border_radius)


@router.message(OverlayStates.waiting_for_border_radius)
async def overlay_border_radius_received(message: Message, state: FSMContext):
    """Handle border radius input"""
    try:
        border_radius = int(message.text.strip())
        if border_radius < 0:
            border_radius = 0
        await state.update_data(border_radius=border_radius)
        await message.answer(
            "Введите толщину обводки в пикселях (например, 2, или 0 для без обводки):"
        )
        await state.set_state(OverlayStates.waiting_for_outline_width)
    except ValueError:
        await message.answer("❌ Введите число. Попробуйте снова:")


@router.message(OverlayStates.waiting_for_outline_width)
async def overlay_outline_width_received(message: Message, state: FSMContext):
    """Handle outline width input"""
    try:
        outline_width = int(message.text.strip())
        if outline_width < 0:
            outline_width = 0
        await state.update_data(outline_width=outline_width)
        if outline_width > 0:
            await message.answer(
                "Введите цвет обводки в HEX формате (например, #000000 для черного):"
            )
            await state.set_state(OverlayStates.waiting_for_outline_color)
        else:
            await state.update_data(outline_color="black")
            await message.answer(
                "Введите смещение тени по X в пикселях (например, 2, или 0 для без тени):"
            )
            await state.set_state(OverlayStates.waiting_for_shadow_x)
    except ValueError:
        await message.answer("❌ Введите число. Попробуйте снова:")


@router.message(OverlayStates.waiting_for_outline_color)
async def overlay_outline_color_received(message: Message, state: FSMContext):
    """Handle outline color input"""
    color = message.text.strip()
    if not color.startswith("#"):
        color = "#" + color
    try:
        int(color[1:], 16)
        if len(color) != 7:
            raise ValueError
    except ValueError:
        await message.answer("❌ Неверный формат цвета. Используйте HEX формат")
        return
    await state.update_data(outline_color=color)
    await message.answer(
        "Введите смещение тени по X в пикселях (например, 2, или 0 для без тени):"
    )
    await state.set_state(OverlayStates.waiting_for_shadow_x)


@router.message(OverlayStates.waiting_for_shadow_x)
async def overlay_shadow_x_received(message: Message, state: FSMContext):
    """Handle shadow X offset input"""
    try:
        shadow_x = int(message.text.strip())
        await state.update_data(shadow_x=shadow_x)
        await message.answer("Введите смещение тени по Y в пикселях:")
        await state.set_state(OverlayStates.waiting_for_shadow_y)
    except ValueError:
        await message.answer("❌ Введите число. Попробуйте снова:")


@router.message(OverlayStates.waiting_for_shadow_y)
async def overlay_shadow_y_received(message: Message, state: FSMContext):
    """Handle shadow Y offset input"""
    try:
        shadow_y = int(message.text.strip())
        await state.update_data(shadow_y=shadow_y)
        data = await state.get_data()
        if shadow_y != 0 or data.get("shadow_x", 0) != 0:
            await message.answer("Введите цвет тени в HEX формате (например, #000000):")
            await state.set_state(OverlayStates.waiting_for_shadow_color)
        else:
            await state.update_data(shadow_color="black")
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⬆️ Сверху", callback_data="overlay_position_top"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬇️ Снизу", callback_data="overlay_position_bottom"
                        )
                    ],
                ]
            )
            await message.answer("Выберите позицию оверлея:", reply_markup=keyboard)
            await state.set_state(OverlayStates.waiting_for_position)
    except ValueError:
        await message.answer("❌ Введите число. Попробуйте снова:")


@router.message(OverlayStates.waiting_for_shadow_color)
async def overlay_shadow_color_received(message: Message, state: FSMContext):
    """Handle shadow color input"""
    color = message.text.strip()
    if not color.startswith("#"):
        color = "#" + color
    try:
        int(color[1:], 16)
        if len(color) != 7:
            raise ValueError
    except ValueError:
        await message.answer("❌ Неверный формат цвета. Используйте HEX формат")
        return
    await state.update_data(shadow_color=color)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬆️ Сверху", callback_data="overlay_position_top"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬇️ Снизу", callback_data="overlay_position_bottom"
                )
            ],
        ]
    )
    await message.answer("Выберите позицию оверлея:", reply_markup=keyboard)
    await state.set_state(OverlayStates.waiting_for_position)


@router.callback_query(F.data.startswith("overlay_position_"))
async def overlay_position_selected(callback: CallbackQuery, state: FSMContext):
    """Handle position selection"""
    position = callback.data.split("_")[-1]
    await state.update_data(position=position, x_offset=0.0, y_offset=0.0)

    await callback.message.edit_text("Введите время начала оверлея в секундах:")
    await state.set_state(OverlayStates.waiting_for_start_sec)
    await callback.answer()


@router.message(OverlayStates.waiting_for_start_sec)
async def overlay_start_sec_received(message: Message, state: FSMContext):
    """Handle start time input"""
    try:
        start_sec = float(message.text.strip())
        if start_sec < 0:
            await message.answer(
                "❌ Время не может быть отрицательным. Попробуйте снова:"
            )
            return

        await state.update_data(start_sec=start_sec)
        await message.answer("Введите время окончания оверлея в секундах:")
        await state.set_state(OverlayStates.waiting_for_end_sec)
    except ValueError:
        await message.answer("❌ Введите число. Попробуйте снова:")


@router.message(OverlayStates.waiting_for_end_sec)
async def overlay_end_sec_received(message: Message, state: FSMContext):
    """Handle end time input and create overlay"""
    project_id = get_active_project(message.from_user.id)
    if not project_id:
        await message.answer("❌ Проект не найден", reply_markup=get_main_menu())
        await state.clear()
        return

    try:
        end_sec = float(message.text.strip())
        data = await state.get_data()
        start_sec = data.get("start_sec")

        if end_sec <= start_sec:
            await message.answer(
                "❌ Время окончания должно быть больше времени начала. Попробуйте снова:"
            )
            return

        # Prepare overlay data
        overlay_data = {
            "type": data.get("type"),
            "position": data.get("position"),
            "start_sec": start_sec,
            "end_sec": end_sec,
            "x_offset": data.get("x_offset", 0.0),
            "y_offset": data.get("y_offset", 0.0),
            "opacity": 1.0,
        }

        if data.get("type") in ["image", "video"]:
            overlay_data["path"] = data.get("path")
            if data.get("use_chromakey"):
                overlay_data["use_chromakey"] = True
                overlay_data["chromakey_color"] = data.get("chromakey_color")
                overlay_data["chromakey_similarity"] = data.get(
                    "chromakey_similarity", 0.3
                )
                overlay_data["chromakey_blend"] = data.get("chromakey_blend", 0.1)
            else:
                overlay_data["use_chromakey"] = False
        else:  # text
            overlay_data["text"] = data.get("text")
            # Apply preset styling or defaults
            overlay_data["font_size"] = data.get("font_size", 48)
            overlay_data["font_color"] = data.get("font_color", "white")
            overlay_data["background_color"] = data.get("background_color", "yellow")
            overlay_data["border_radius"] = data.get("border_radius", 20)
            overlay_data["outline_width"] = data.get("outline_width", 2)
            overlay_data["outline_color"] = data.get("outline_color", "black")
            overlay_data["shadow_x"] = data.get("shadow_x", 2)
            overlay_data["shadow_y"] = data.get("shadow_y", 2)
            overlay_data["shadow_color"] = data.get("shadow_color", "black")
            overlay_data["background_opacity"] = data.get("background_opacity", 0.9)

        # Create overlay
        overlay = await api_client.create_overlay(project_id, **overlay_data)

        overlay_type_icon = (
            "🖼️"
            if overlay["type"] == "image"
            else "🎬" if overlay["type"] == "video" else "📝"
        )
        await message.answer(
            f"✅ Оверлей создан!\n\n"
            f"{overlay_type_icon} {overlay['type']}\n"
            f"Позиция: {overlay['position']}\n"
            f"Время: {overlay['start_sec']:.1f}-{overlay['end_sec']:.1f}s",
            reply_markup=get_main_menu(),
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число. Попробуйте снова:")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()


@router.callback_query(F.data.startswith("overlay_actions_"))
async def overlay_actions(callback: CallbackQuery):
    """Show overlay details and actions"""
    overlay_id = int(callback.data.split("_")[-1])
    try:
        overlay = await api_client.get_overlay(overlay_id)
        overlay_type = overlay.get("type", "unknown")
        overlay_icon = (
            "🖼️"
            if overlay_type == "image"
            else "🎬" if overlay_type == "video" else "📝"
        )

        text = f"{overlay_icon} Оверлей:\n\n"
        text += f"Тип: {overlay_type}\n"
        text += f"Позиция: {overlay.get('position', 'unknown')}\n"
        text += f"Время: {overlay.get('start_sec', 0):.1f}-{overlay.get('end_sec', 0):.1f}s\n"

        if overlay_type == "text":
            text += f"Текст: {overlay.get('text', '')}\n"
            text += f"Размер шрифта: {overlay.get('font_size', 48)}\n"
            text += f"Цвет текста: {overlay.get('font_color', 'white')}\n"
            text += f"Цвет фона: {overlay.get('background_color', 'yellow')}\n"
        elif overlay_type in ["image", "video"]:
            if overlay.get("use_chromakey"):
                text += f"Хромакей: {overlay.get('chromakey_color', '#00FF00')}\n"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🗑 Удалить", callback_data=f"overlay_delete_{overlay_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отмена", callback_data="overlay_cancel"
                    )
                ],
            ]
        )
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("overlay_delete_"))
async def delete_overlay(callback: CallbackQuery):
    """Delete an overlay"""
    overlay_id = int(callback.data.split("_")[-1])
    try:
        await api_client.delete_overlay(overlay_id)
        await callback.answer("✅ Оверлей удален")
        # Refresh overlay menu
        project_id = get_active_project(callback.from_user.id)
        if project_id:
            overlays = await api_client.list_overlays(project_id)
            text = "🖼️ Оверлеи:\n\n"
            keyboard_buttons = []

            if overlays:
                for i, overlay in enumerate(overlays, 1):
                    overlay_type = overlay.get("type", "unknown")
                    overlay_icon = (
                        "🖼️"
                        if overlay_type == "image"
                        else "🎬" if overlay_type == "video" else "📝"
                    )
                    chromakey_icon = "🎨" if overlay.get("use_chromakey") else ""
                    overlay_id_item = overlay.get("id")
                    text += f"{i}. {overlay_icon} {overlay_type}{chromakey_icon} ({overlay.get('start_sec', 0):.1f}-{overlay.get('end_sec', 0):.1f}s)\n"
                    keyboard_buttons.append(
                        [
                            InlineKeyboardButton(
                                text=f"{i}. {overlay_icon} {overlay_type}{chromakey_icon}",
                                callback_data=f"overlay_actions_{overlay_id_item}",
                            )
                        ]
                    )
            else:
                text += "Оверлеи отсутствуют.\n"

            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        text="➕ Добавить оверлей", callback_data="overlay_add"
                    )
                ]
            )
            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        text="❌ Закрыть", callback_data="overlay_cancel"
                    )
                ]
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            await callback.message.edit_text(text, reply_markup=keyboard)
        else:
            await callback.message.delete()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
