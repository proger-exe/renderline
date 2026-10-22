from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from bot.utils.api_client import api_client
from bot.utils.storage import get_active_project
from bot.keyboards.main import get_main_menu
from pathlib import Path
import asyncio
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "🚀 Рендер")
async def render_start(message: Message):
    """Start render process"""
    project_id = get_active_project(message.from_user.id)
    if not project_id:
        await message.answer(
            "❌ Сначала выберите или создайте проект!", reply_markup=get_main_menu()
        )
        return

    try:
        # Update project status to rendering
        await api_client.update_project(project_id, status="rendering")

        # Submit render task
        response = await api_client.start_render(project_id)
        task_id = response.get("task_id")

        status_msg = await message.answer(
            f"🚀 Рендер запущен!\n\n"
            f"Task ID: {task_id}\n"
            f"Статус: rendering\n\n"
            f"⏳ Ожидайте завершения рендера..."
        )

        # Poll for completion
        await check_render_status(
            message.bot, message.from_user.id, project_id, status_msg
        )

    except Exception as e:
        await message.answer(f"❌ Ошибка при запуске рендера: {str(e)}")
        # Reset status on error
        try:
            await api_client.update_project(project_id, status="draft")
        except:
            pass


async def check_render_status(
    bot: Bot,
    user_id: int,
    project_id: int,
    status_msg: Message,
    max_attempts: int = 120,
):
    """Poll render status and send video when ready"""
    for attempt in range(max_attempts):
        await asyncio.sleep(5)  # Check every 5 seconds

        try:
            status = await api_client.get_render_status(project_id)

            if status["status"] == "completed":
                output_path = status.get("output_path")
                if output_path and Path(output_path).exists():
                    try:
                        await status_msg.edit_text(
                            "✅ Рендер завершен! Отправляю видео..."
                        )
                        video_file = FSInputFile(output_path)
                        await bot.send_video(
                            chat_id=user_id,
                            video=video_file,
                            caption="✅ Ваше видео готово!",
                        )
                        await status_msg.delete()
                        return
                    except Exception as e:
                        logger.error(f"Error sending video: {str(e)}")
                        await status_msg.edit_text(
                            f"❌ Ошибка при отправке видео: {str(e)}"
                        )
                        return
                else:
                    await status_msg.edit_text("❌ Видео готово, но файл не найден")
                    return

            elif status["status"] == "failed":
                await status_msg.edit_text("❌ Рендер завершился с ошибкой")
                return

            elif status["status"] == "rendering":
                # Update status message only if content changed
                if attempt % 6 == 0:  # Update every 30 seconds
                    new_text = (
                        f"⏳ Рендер в процессе...\nПопытка {attempt + 1}/{max_attempts}"
                    )
                    try:
                        await status_msg.edit_text(new_text)
                    except Exception as e:
                        # Ignore "message is not modified" error
                        if "message is not modified" not in str(e).lower():
                            logger.warning(f"Error updating status message: {e}")

        except Exception as e:
            logger.error(f"Error checking render status: {str(e)}")
            if attempt == max_attempts - 1:
                await status_msg.edit_text(f"❌ Ошибка при проверке статуса: {str(e)}")

    # Timeout
    await status_msg.edit_text(
        "⏱ Рендер занимает больше времени, чем ожидалось. Проверьте позже."
    )
