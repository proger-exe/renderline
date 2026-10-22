"""Add new features: overlays, audio improvements, YouTube preset, active subtitles

Revision ID: 003
Revises: 002
Create Date: 2024-01-03 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add YouTube preset support (enum update handled at application level)

    # Add mute_audio to segments
    op.add_column(
        "segments",
        sa.Column("mute_audio", sa.Boolean(), nullable=True, server_default="false"),
    )

    # Add is_active to subtitles
    op.add_column(
        "subtitles",
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default="false"),
    )

    # Add start_sec and duration to audio_bgm
    op.add_column("audio_bgm", sa.Column("start_sec", sa.Float(), nullable=True))
    op.add_column("audio_bgm", sa.Column("duration", sa.Float(), nullable=True))

    # Add duration to audio_sfx
    op.add_column("audio_sfx", sa.Column("duration", sa.Float(), nullable=True))

    # Create overlays table
    op.create_table(
        "overlays",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("path", sa.String(), nullable=True),
        sa.Column("text", sa.String(), nullable=True),
        sa.Column("position", sa.String(), nullable=False),
        sa.Column("x_offset", sa.Float(), nullable=True, server_default="0.0"),
        sa.Column("y_offset", sa.Float(), nullable=True, server_default="0.0"),
        sa.Column("width", sa.Float(), nullable=True),
        sa.Column("height", sa.Float(), nullable=True),
        sa.Column("opacity", sa.Float(), nullable=True, server_default="1.0"),
        sa.Column("start_sec", sa.Float(), nullable=False),
        sa.Column("end_sec", sa.Float(), nullable=False),
        sa.Column("font_size", sa.Integer(), nullable=True),
        sa.Column("font_color", sa.String(), nullable=True),
        sa.Column("background_color", sa.String(), nullable=True),
        sa.Column("border_radius", sa.Integer(), nullable=True),
        sa.Column("use_chromakey", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("chromakey_color", sa.String(), nullable=True),
        sa.Column("chromakey_similarity", sa.Float(), nullable=True),
        sa.Column("chromakey_blend", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_overlays_id"), "overlays", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_overlays_id"), table_name="overlays")
    op.drop_table("overlays")
    op.drop_column("audio_sfx", "duration")
    op.drop_column("audio_bgm", "duration")
    op.drop_column("audio_bgm", "start_sec")
    op.drop_column("subtitles", "is_active")
    op.drop_column("segments", "mute_audio")
