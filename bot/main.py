import asyncio
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings
from bot.handlers import (
    start,
    main_menu,
    project,
    asset,
    timeline,
    subtitle,
    audio,
    preset,
    render,
    overlay,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to run the bot"""
    # Initialize bot and dispatcher
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Register routers
    dp.include_router(start.router)
    dp.include_router(main_menu.router)
    dp.include_router(project.router)
    dp.include_router(asset.router)
    dp.include_router(timeline.router)
    dp.include_router(subtitle.router)
    dp.include_router(audio.router)
    dp.include_router(overlay.router)
    dp.include_router(preset.router)
    dp.include_router(render.router)

    # Start polling
    logger.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
