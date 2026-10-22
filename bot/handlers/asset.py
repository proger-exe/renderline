from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from pathlib import Path
import aiofiles
from bot.utils.api_client import api_client
from bot.utils.storage import get_active_project
from bot.utils.ffprobe import get_video_duration
from bot.utils.asset_utils import get_next_alias
from bot.keyboards.asset import get_assets_keyboard
from bot.keyboards.main import get_main_menu
from config.settings import settings

router = Router()


@router.message(F.text == "📁 Ассеты")
async def assets_menu(message: Message):
    """Show assets menu"""
    project_id = get_active_project(message.from_user.id)
    if not project_id:
        await message.answer(
            "❌ Сначала выберите или создайте проект!", reply_markup=get_main_menu()
        )
        return

    try:
        assets = await api_client.list_assets(project_id)
        if not assets:
            await message.answer(
                "📁 В проекте пока нет ассетов.\n\n" "Отправьте видеофайл для загрузки."
            )
        else:
            text = "📁 Ассеты проекта:\n\n"
            for asset in assets:
                text += f"{asset['alias']}: {asset['filename']}\n"
                text += f"   Длительность: {asset['duration']:.2f} сек\n\n"

            await message.answer(
                text, reply_markup=get_assets_keyboard(assets, project_id)
            )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(F.video)
async def handle_video(message: Message):
    """Handle video file upload"""
    project_id = get_active_project(message.from_user.id)
    if not project_id:
        await message.answer(
            "❌ Сначала выберите или создайте проект!", reply_markup=get_main_menu()
        )
        return

    try:
        # Get video file
        video = message.video
        file_info = await message.bot.get_file(video.file_id)

        # Generate filename
        file_extension = Path(file_info.file_path).suffix or ".mp4"
        filename = f"{video.file_id}{file_extension}"
        file_path = settings.storage_assets_path / filename

        # Download file
        await message.bot.download_file(file_info.file_path, str(file_path))

        # Get duration
        duration = get_video_duration(file_path)

        # Get existing aliases
        existing_assets = await api_client.list_assets(project_id)
        existing_aliases = [asset["alias"] for asset in existing_assets]

        # Get next alias
        alias = get_next_alias(existing_aliases)

        # Create asset in database
        asset = await api_client.create_asset(
            project_id=project_id,
            alias=alias,
            filename=video.file_name or filename,
            path=str(file_path),
            duration=duration,
        )

        await message.answer(
            f"✅ Ассет загружен!\n\n"
            f"Алиас: {alias}\n"
            f"Файл: {asset['filename']}\n"
            f"Длительность: {duration:.2f} сек"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при загрузке ассета: {str(e)}")


@router.message(F.document)
async def handle_document(message: Message):
    """Handle document (video file) upload"""
    project_id = get_active_project(message.from_user.id)
    if not project_id:
        await message.answer(
            "❌ Сначала выберите или создайте проект!", reply_markup=get_main_menu()
        )
        return

    # Check if it's a video file
    doc = message.document
    if not doc.mime_type or not doc.mime_type.startswith("video/"):
        await message.answer("❌ Пожалуйста, отправьте видеофайл")
        return

    try:
        # Get file
        file_info = await message.bot.get_file(doc.file_id)

        # Generate filename
        filename = doc.file_name or f"{doc.file_id}.mp4"
        file_path = settings.storage_assets_path / filename

        # Download file
        await message.bot.download_file(file_info.file_path, str(file_path))

        # Get duration
        duration = get_video_duration(file_path)

        # Get existing aliases
        existing_assets = await api_client.list_assets(project_id)
        existing_aliases = [asset["alias"] for asset in existing_assets]

        # Get next alias
        alias = get_next_alias(existing_aliases)

        # Create asset in database
        asset = await api_client.create_asset(
            project_id=project_id,
            alias=alias,
            filename=filename,
            path=str(file_path),
            duration=duration,
        )

        await message.answer(
            f"✅ Ассет загружен!\n\n"
            f"Алиас: {alias}\n"
            f"Файл: {asset['filename']}\n"
            f"Длительность: {duration:.2f} сек"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при загрузке ассета: {str(e)}")


@router.callback_query(F.data.startswith("asset_delete_"))
async def delete_asset(callback: CallbackQuery):
    """Delete an asset"""
    asset_id = int(callback.data.split("_")[-1])
    project_id = get_active_project(callback.from_user.id)
    try:
        await api_client.delete_asset(asset_id)
        await callback.answer("✅ Ассет удален")

        # Refresh assets list
        if project_id:
            assets = await api_client.list_assets(project_id)
            if not assets:
                await callback.message.edit_text(
                    "📁 В проекте пока нет ассетов.\n\n"
                    "Отправьте видеофайл для загрузки."
                )
            else:
                text = "📁 Ассеты проекта:\n\n"
                for asset in assets:
                    text += f"{asset['alias']}: {asset['filename']}\n"
                    text += f"   Длительность: {asset['duration']:.2f} сек\n\n"

                await callback.message.edit_text(
                    text, reply_markup=get_assets_keyboard(assets, project_id)
                )
        else:
            await callback.message.delete()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data == "asset_close")
async def close_assets(callback: CallbackQuery):
    """Close assets menu"""
    await callback.message.delete()
    await callback.answer()
