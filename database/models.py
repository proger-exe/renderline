from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Boolean,
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database.base import Base


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class Preset(str, enum.Enum):
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, nullable=False, index=True)  # telegram_id
    title = Column(String, nullable=False)
    preset = Column(String, default=Preset.TIKTOK.value)
    status = Column(String, default=ProjectStatus.DRAFT.value)
    output_path = Column(String, nullable=True)  # Path to rendered video
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    assets = relationship(
        "Asset", back_populates="project", cascade="all, delete-orphan"
    )
    segments = relationship(
        "Segment",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Segment.order",
    )
    subtitles = relationship(
        "Subtitle", back_populates="project", cascade="all, delete-orphan"
    )
    audio_bgm = relationship(
        "AudioBGM",
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
    )
    audio_sfx = relationship(
        "AudioSFX", back_populates="project", cascade="all, delete-orphan"
    )
    overlays = relationship(
        "Overlay", back_populates="project", cascade="all, delete-orphan"
    )


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    alias = Column(String, nullable=False)  # A, B, C...
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    duration = Column(Float, nullable=False)  # in seconds
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="assets")


class Segment(Base):
    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    asset_alias = Column(String, nullable=False)  # Reference to Asset.alias
    in_sec = Column(Float, nullable=False)
    out_sec = Column(Float, nullable=False)
    order = Column(Integer, nullable=False)  # Order in timeline
    mute_audio = Column(Boolean, default=False)  # Mute original audio for this segment

    # Relationships
    project = relationship("Project", back_populates="segments")


class Subtitle(Base):
    __tablename__ = "subtitles"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    start_sec = Column(Float, nullable=False)
    end_sec = Column(Float, nullable=False)
    text = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)  # Active subtitle with yellow background

    # Relationships
    project = relationship("Project", back_populates="subtitles")


class AudioBGM(Base):
    __tablename__ = "audio_bgm"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, unique=True)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    volume = Column(Float, default=0.25)  # 0.0-1.0
    start_sec = Column(Float, nullable=True)  # Delay start of BGM
    duration = Column(Float, nullable=True)  # Maximum duration (trim BGM)

    # Relationships
    project = relationship("Project", back_populates="audio_bgm")


class AudioSFX(Base):
    __tablename__ = "audio_sfx"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    at_sec = Column(Float, nullable=False)  # When to play in final video
    volume = Column(Float, default=0.6)  # 0.0-1.0
    duration = Column(Float, nullable=True)  # Duration to trim SFX

    # Relationships
    project = relationship("Project", back_populates="audio_sfx")


class Overlay(Base):
    __tablename__ = "overlays"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    type = Column(String, nullable=False)  # "image", "text", or "video"
    path = Column(
        String, nullable=True
    )  # Path to image/video file (for image/video type)
    text = Column(String, nullable=True)  # Text content (for text type)
    position = Column(String, nullable=False)  # "top" or "bottom"
    x_offset = Column(Float, default=0.0)  # Horizontal offset
    y_offset = Column(Float, default=0.0)  # Vertical offset
    width = Column(Float, nullable=True)  # Width (null = auto)
    height = Column(Float, nullable=True)  # Height (null = auto)
    opacity = Column(Float, default=1.0)  # 0.0-1.0
    start_sec = Column(Float, nullable=False)  # When to show overlay
    end_sec = Column(Float, nullable=False)  # When to hide overlay
    # Text-specific fields
    font_size = Column(Integer, nullable=True)  # Font size for text
    font_color = Column(String, nullable=True)  # Hex color for text
    background_color = Column(String, nullable=True)  # Hex color for background
    border_radius = Column(Integer, nullable=True)  # Border radius in pixels
    font_family = Column(String, nullable=True)  # Font name/family
    outline_width = Column(Integer, nullable=True)  # Text outline thickness
    outline_color = Column(String, nullable=True)  # Outline color hex
    shadow_x = Column(Integer, nullable=True)  # Shadow X offset
    shadow_y = Column(Integer, nullable=True)  # Shadow Y offset
    shadow_color = Column(String, nullable=True)  # Shadow color hex
    background_opacity = Column(Float, nullable=True)  # Background opacity (0.0-1.0)
    # Chroma key fields
    use_chromakey = Column(Boolean, default=False)
    chromakey_color = Column(String, nullable=True)  # Hex color like "#00FF00"
    chromakey_similarity = Column(Float, nullable=True)  # 0.0-1.0, tolerance
    chromakey_blend = Column(Float, nullable=True)  # 0.0-1.0, smoothness

    # Relationships
    project = relationship("Project", back_populates="overlays")
