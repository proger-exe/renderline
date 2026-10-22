from typing import Dict, Any, List
from sqlalchemy.orm import Session
from database.models import (
    Project,
    Asset,
    Segment,
    Subtitle,
    AudioBGM,
    AudioSFX,
    Overlay,
)


def generate_execution_plan(project_id: int, db: Session) -> Dict[str, Any]:
    """Generate execution plan JSON from project data"""
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")

    # Get assets
    assets = db.query(Asset).filter(Asset.project_id == project_id).all()
    assets_dict = {}
    for asset in assets:
        assets_dict[asset.alias] = {"path": asset.path}

    # Get segments
    segments = (
        db.query(Segment)
        .filter(Segment.project_id == project_id)
        .order_by(Segment.order)
        .all()
    )
    timeline = []
    for segment in segments:
        timeline.append(
            {
                "asset": segment.asset_alias,
                "in": segment.in_sec,
                "out": segment.out_sec,
                "mute_audio": segment.mute_audio or False,
            }
        )

    # Get subtitles
    subtitles = (
        db.query(Subtitle)
        .filter(Subtitle.project_id == project_id)
        .order_by(Subtitle.start_sec)
        .all()
    )
    subtitles_list = []
    for subtitle in subtitles:
        subtitles_list.append(
            {
                "start": subtitle.start_sec,
                "end": subtitle.end_sec,
                "text": subtitle.text,
                "is_active": subtitle.is_active or False,
            }
        )

    # Get BGM
    bgm = db.query(AudioBGM).filter(AudioBGM.project_id == project_id).first()
    bgm_dict = None
    if bgm:
        bgm_dict = {
            "file": bgm.path,
            "volume": bgm.volume,
            "start_sec": bgm.start_sec,
            "duration": bgm.duration,
        }

    # Get SFX
    sfx_list = (
        db.query(AudioSFX)
        .filter(AudioSFX.project_id == project_id)
        .order_by(AudioSFX.at_sec)
        .all()
    )
    sfx_dict = []
    for sfx in sfx_list:
        sfx_dict.append(
            {
                "at": sfx.at_sec,
                "file": sfx.path,
                "volume": sfx.volume,
                "duration": sfx.duration,
            }
        )

    # Get overlays
    overlays = (
        db.query(Overlay)
        .filter(Overlay.project_id == project_id)
        .order_by(Overlay.start_sec)
        .all()
    )
    overlays_list = []
    for overlay in overlays:
        overlay_dict = {
            "type": overlay.type,
            "position": overlay.position,
            "x_offset": overlay.x_offset or 0.0,
            "y_offset": overlay.y_offset or 0.0,
            "width": overlay.width,
            "height": overlay.height,
            "opacity": overlay.opacity or 1.0,
            "start_sec": overlay.start_sec,
            "end_sec": overlay.end_sec,
        }
        if overlay.type in ["image", "video"]:
            overlay_dict["path"] = overlay.path
            overlay_dict["use_chromakey"] = overlay.use_chromakey or False
            if overlay.use_chromakey:
                overlay_dict["chromakey_color"] = overlay.chromakey_color
                overlay_dict["chromakey_similarity"] = (
                    overlay.chromakey_similarity or 0.3
                )
                overlay_dict["chromakey_blend"] = overlay.chromakey_blend or 0.1
        elif overlay.type == "text":
            overlay_dict["text"] = overlay.text
            overlay_dict["font_size"] = overlay.font_size
            overlay_dict["font_color"] = overlay.font_color
            overlay_dict["background_color"] = overlay.background_color
            overlay_dict["border_radius"] = overlay.border_radius
            overlay_dict["font_family"] = overlay.font_family
            overlay_dict["outline_width"] = overlay.outline_width
            overlay_dict["outline_color"] = overlay.outline_color
            overlay_dict["shadow_x"] = overlay.shadow_x
            overlay_dict["shadow_y"] = overlay.shadow_y
            overlay_dict["shadow_color"] = overlay.shadow_color
            overlay_dict["background_opacity"] = overlay.background_opacity
        overlays_list.append(overlay_dict)

    # Build execution plan
    execution_plan = {
        "preset": project.preset or "tiktok",
        "assets": assets_dict,
        "timeline": timeline,
        "subtitles": subtitles_list,
        "subtitle_style": "tiktok_bold_v1",
        "audio": {"bgm": bgm_dict, "sfx": sfx_dict if sfx_dict else []},
        "overlays": overlays_list,
    }

    return execution_plan


def validate_execution_plan(execution_plan: Dict[str, Any]) -> List[str]:
    """Validate execution plan and return list of errors"""
    errors = []

    # Check assets
    if not execution_plan.get("assets"):
        errors.append("No assets defined")

    # Check timeline
    if not execution_plan.get("timeline"):
        errors.append("Timeline is empty")

    # Validate segments
    assets = execution_plan.get("assets", {})
    for i, segment in enumerate(execution_plan.get("timeline", [])):
        asset_alias = segment.get("asset")
        if asset_alias not in assets:
            errors.append(f"Segment {i+1}: Asset '{asset_alias}' not found")

        in_sec = segment.get("in")
        out_sec = segment.get("out")
        if in_sec is None or out_sec is None:
            errors.append(f"Segment {i+1}: Missing in/out times")
        elif out_sec <= in_sec:
            errors.append(f"Segment {i+1}: Invalid timings (out <= in)")

    # Validate subtitles
    for i, subtitle in enumerate(execution_plan.get("subtitles", [])):
        start = subtitle.get("start")
        end = subtitle.get("end")
        if start is None or end is None:
            errors.append(f"Subtitle {i+1}: Missing start/end times")
        elif end <= start:
            errors.append(f"Subtitle {i+1}: Invalid timings (end <= start)")

    return errors
