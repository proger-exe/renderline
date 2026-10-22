# Renderline

Describe a vertical video in Telegram, get it rendered. Users upload clips, build a timeline of segments (`asset + in + out` in seconds), add subtitle lines, background music, sound effects and text overlays; a worker assembles the result with FFmpeg and sends it back. No video editor involved.

## How it works

```
Telegram bot ──► FastAPI (projects, assets, timeline, subtitles, audio, overlays, render)
                      │ PostgreSQL (SQLAlchemy 2 + Alembic)
                      ▼
                 RabbitMQ queue ──► render worker (ffmpeg, libass subtitles) ──► storage/output
```

- **bot/**: aiogram 3 FSM flow: project → assets → segments → subtitles → audio → render.
- **api/**: REST layer the bot talks to; also usable directly (`/docs`).
- **worker/**: consumes `render_tasks`, builds the FFmpeg filter graph (trim, concat, 9:16 scaling, ASS subtitles, BGM mix, SFX at timestamps, text overlays), writes MP4, updates project status.
- **database/**: models and migrations.

## Run

```bash
cp .env.example .env     # set TELEGRAM_BOT_TOKEN
docker compose up -d --build
# API docs: http://127.0.0.1:8000/docs
```

Five containers: postgres, rabbitmq, api (runs migrations on start), bot, worker. Uploaded assets and renders live in `./storage`.

Local without Docker: run Postgres + RabbitMQ, point `.env` at them, then `alembic upgrade head`, `uvicorn api.main:app`, `python bot/main.py`, `python worker/main.py`.

## Tests

```bash
pytest -q
```

Spec with the full feature list: `docs/spec.md` (RU).

## License

MIT
