"""Fails if settings stop parsing or any router stops registering."""
import os

os.environ.update(
    TELEGRAM_BOT_TOKEN="1:test",
    DATABASE_URL="postgresql+asyncpg://u:p@localhost/db",
    DATABASE_URL_SYNC="postgresql://u:p@localhost/db",
    RABBITMQ_URL="amqp://u:p@localhost/",
    STORAGE_PATH="/tmp/renderline-test",
    STORAGE_ASSETS_PATH="/tmp/renderline-test/assets",
    STORAGE_AUDIO_PATH="/tmp/renderline-test/audio",
    STORAGE_OUTPUT_PATH="/tmp/renderline-test/output",
)


def test_api_routes_registered():
    from api.main import app

    paths = {r.path for r in app.routes}
    assert any(p.startswith("/projects") for p in paths)
    assert any("timeline" in p for p in paths)


def test_worker_imports():
    import worker.processors.render_processor  # noqa: F401
