from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from bot.states.project import ProjectStates
from bot.keyboards.main import get_main_menu
from bot.keyboards.project import get_projects_keyboard, get_project_actions_keyboard
from bot.utils.api_client import api_client
from bot.utils.storage import (
    set_active_project,
    get_active_project,
    clear_active_project,
)

router = Router()


@router.message(F.text == "➕ Новый проект")
async def new_project_start(message: Message, state: FSMContext):
    """Start creating a new project"""
    await state.set_state(ProjectStates.waiting_for_title)
    await message.answer("Введите название проекта:")


@router.message(F.text == "📋 Мои проекты")
async def list_projects(message: Message):
    """List all user projects"""
    try:
        projects = await api_client.list_projects(owner_id=message.from_user.id)
        if not projects:
            await message.answer("У вас пока нет проектов. Создайте новый проект!")
            return

        active_project_id = get_active_project(message.from_user.id)
        text = "📋 Ваши проекты:\n\n"
        for project in projects:
            marker = "👉 " if project["id"] == active_project_id else "  "
            text += f"{marker}{project['title']} (ID: {project['id']}, статус: {project['status']})\n"

        await message.answer(text, reply_markup=get_projects_keyboard(projects))
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении проектов: {str(e)}")


@router.callback_query(F.data.startswith("project_select_"))
async def select_project(callback: CallbackQuery):
    """Select a project as active"""
    project_id = int(callback.data.split("_")[-1])
    try:
        project = await api_client.get_project(project_id)
        if project["owner_id"] != callback.from_user.id:
            await callback.answer(
                "❌ У вас нет доступа к этому проекту", show_alert=True
            )
            return

        set_active_project(callback.from_user.id, project_id)
        await callback.answer(f"✅ Проект '{project['title']}' выбран")
        await callback.message.edit_text(
            f"✅ Активный проект: {project['title']}\n"
            f"ID: {project['id']}\n"
            f"Статус: {project['status']}"
        )
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("project_delete_"))
async def delete_project(callback: CallbackQuery):
    """Delete a project"""
    project_id = int(callback.data.split("_")[-1])
    try:
        project = await api_client.get_project(project_id)
        if project["owner_id"] != callback.from_user.id:
            await callback.answer(
                "❌ У вас нет доступа к этому проекту", show_alert=True
            )
            return

        # Clear active project if it's the one being deleted
        active_project_id = get_active_project(callback.from_user.id)
        if active_project_id == project_id:
            clear_active_project(callback.from_user.id)

        await api_client.delete_project(project_id)
        await callback.answer("✅ Проект удален")

        # Refresh projects list
        projects = await api_client.list_projects(owner_id=callback.from_user.id)
        if not projects:
            await callback.message.edit_text(
                "✅ Проект удален.\n\n"
                "У вас больше нет проектов. Создайте новый проект!"
            )
        else:
            active_project_id = get_active_project(callback.from_user.id)
            text = "📋 Ваши проекты:\n\n"
            for p in projects:
                marker = "👉 " if p["id"] == active_project_id else "  "
                text += f"{marker}{p['title']} (ID: {p['id']}, статус: {p['status']})\n"

            await callback.message.edit_text(
                text, reply_markup=get_projects_keyboard(projects)
            )
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("project_edit_"))
async def edit_project_start(callback: CallbackQuery, state: FSMContext):
    """Start editing project title"""
    project_id = int(callback.data.split("_")[-1])
    try:
        project = await api_client.get_project(project_id)
        if project["owner_id"] != callback.from_user.id:
            await callback.answer(
                "❌ У вас нет доступа к этому проекту", show_alert=True
            )
            return

        await state.update_data(project_id=project_id)
        await state.set_state(ProjectStates.waiting_for_title)
        await callback.message.answer(
            f"Текущее название: {project['title']}\n\n"
            f"Введите новое название проекта:"
        )
        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.message(StateFilter(ProjectStates.waiting_for_title))
async def edit_project_save(message: Message, state: FSMContext):
    """Save edited project title"""
    data = await state.get_data()
    if "project_id" in data:
        # Editing existing project
        title = message.text.strip()
        if not title:
            await message.answer("Название не может быть пустым. Попробуйте снова:")
            return

        try:
            project = await api_client.update_project(data["project_id"], title=title)
            await message.answer(
                f"✅ Проект обновлен!\n" f"Название: {project['title']}",
                reply_markup=get_main_menu(),
            )
            await state.clear()
        except Exception as e:
            await message.answer(f"❌ Ошибка при обновлении проекта: {str(e)}")
            await state.clear()
    else:
        # Creating new project (existing handler)
        title = message.text.strip()
        if not title:
            await message.answer("Название не может быть пустым. Попробуйте снова:")
            return

        try:
            project = await api_client.create_project(
                owner_id=message.from_user.id, title=title, preset="tiktok"
            )
            set_active_project(message.from_user.id, project["id"])
            await message.answer(
                f"✅ Проект '{title}' создан!\n"
                f"ID: {project['id']}\n"
                f"Статус: {project['status']}",
                reply_markup=get_main_menu(),
            )
            await state.clear()
        except Exception as e:
            await message.answer(f"❌ Ошибка при создании проекта: {str(e)}")
            await state.clear()


@router.callback_query(F.data.startswith("project_clone_"))
async def clone_project_handler(callback: CallbackQuery):
    """Clone a project"""
    project_id = int(callback.data.split("_")[-1])
    try:
        project = await api_client.get_project(project_id)
        if project["owner_id"] != callback.from_user.id:
            await callback.answer(
                "❌ У вас нет доступа к этому проекту", show_alert=True
            )
            return

        new_project = await api_client.clone_project(project_id)
        set_active_project(callback.from_user.id, new_project["id"])
        await callback.answer("✅ Проект клонирован!")
        await callback.message.edit_text(
            f"✅ Проект '{project['title']}' клонирован!\n\n"
            f"Новый проект: {new_project['title']}\n"
            f"ID: {new_project['id']}\n\n"
            f"⚠️ Не забудьте загрузить новые файлы для ассетов!",
            reply_markup=get_project_actions_keyboard(new_project["id"]),
        )
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data == "project_cancel")
async def cancel_project_action(callback: CallbackQuery):
    """Cancel project action"""
    await callback.answer("Отменено")
    await callback.message.delete()
