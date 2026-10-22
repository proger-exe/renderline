"""Text overlay presets configuration"""

from typing import Dict, Any

# Preset definitions for text overlays
TEXT_OVERLAY_PRESETS: Dict[str, Dict[str, Any]] = {
    "tiktok": {
        "font_size": 64,
        "font_color": "white",
        "background_color": "yellow",
        "border_radius": 20,
        "outline_width": 4,
        "outline_color": "black",
        "shadow_x": 2,
        "shadow_y": 2,
        "shadow_color": "black",
        "background_opacity": 0.9,
    },
    "minimal": {
        "font_size": 48,
        "font_color": "white",
        "background_color": None,  # Transparent
        "border_radius": 0,
        "outline_width": 2,
        "outline_color": "black",
        "shadow_x": 1,
        "shadow_y": 1,
        "shadow_color": "black",
        "background_opacity": 0.0,
    },
    "classic": {
        "font_size": 56,
        "font_color": "white",
        "background_color": "black",
        "border_radius": 10,
        "outline_width": 3,
        "outline_color": "black",
        "shadow_x": 2,
        "shadow_y": 2,
        "shadow_color": "black",
        "background_opacity": 0.8,
    },
    "custom": {
        # Custom preset - user will configure all parameters
        "font_size": 48,
        "font_color": "white",
        "background_color": "yellow",
        "border_radius": 20,
        "outline_width": 2,
        "outline_color": "black",
        "shadow_x": 2,
        "shadow_y": 2,
        "shadow_color": "black",
        "background_opacity": 0.9,
    },
}


def get_preset(name: str) -> Dict[str, Any]:
    """Get preset configuration by name"""
    return TEXT_OVERLAY_PRESETS.get(name.lower(), TEXT_OVERLAY_PRESETS["custom"])


def get_preset_names() -> list[str]:
    """Get list of available preset names"""
    return list(TEXT_OVERLAY_PRESETS.keys())
