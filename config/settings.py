from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Telegram Bot
    telegram_bot_token: str

    # Database
    database_url: str
    database_url_sync: str

    # RabbitMQ
    rabbitmq_url: str
    rabbitmq_queue: str = "render_tasks"

    # Storage
    storage_path: Path = Path("./storage")
    storage_assets_path: Path = Path("./storage/assets")
    storage_audio_path: Path = Path("./storage/audio")
    storage_output_path: Path = Path("./storage/output")

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Worker
    worker_concurrency: int = 2

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create storage directories
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.storage_assets_path.mkdir(parents=True, exist_ok=True)
        self.storage_audio_path.mkdir(parents=True, exist_ok=True)
        self.storage_output_path.mkdir(parents=True, exist_ok=True)


settings = Settings()
