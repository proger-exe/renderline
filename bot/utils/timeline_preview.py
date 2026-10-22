from typing import List, Dict


def calculate_total_duration(segments: List[Dict]) -> float:
    """Calculate total duration of timeline"""
    if not segments:
        return 0.0
    return sum(seg["out_sec"] - seg["in_sec"] for seg in segments)


def generate_timeline_preview(segments: List[Dict], scale: float = 1.0) -> str:
    """
    Generate ASCII timeline preview

    Args:
        segments: List of segment dicts with asset_alias, in_sec, out_sec
        scale: Scale factor (1.0 = 1 char per second, 0.5 = 1 char per 2 seconds)

    Returns:
        ASCII representation of timeline
    """
    if not segments:
        return "Таймлайн пуст"

    # Calculate timeline positions
    total_duration = calculate_total_duration(segments)
    if total_duration == 0:
        return "Таймлайн пуст"

    # Calculate positions in timeline
    current_time = 0.0
    timeline_segments = []
    for seg in segments:
        duration = seg["out_sec"] - seg["in_sec"]
        timeline_segments.append(
            {
                "asset_alias": seg["asset_alias"],
                "start": current_time,
                "end": current_time + duration,
                "duration": duration,
            }
        )
        current_time += duration

    # Generate preview
    chars_per_sec = 1.0 / scale
    width = int(total_duration * chars_per_sec)
    width = max(width, 20)  # Minimum width

    # Create timeline grid
    lines = []

    # Time markers
    marker_interval = max(1, int(5 / scale))  # Every 5 seconds
    time_line = "0"
    for i in range(1, int(total_duration) + 1, marker_interval):
        pos = int(i * chars_per_sec)
        if pos < width:
            time_line += "." * (pos - len(time_line)) + str(i)
    lines.append(time_line[:width])

    # Separator
    lines.append("|" + "-" * (width - 1))

    # Segments
    for seg in timeline_segments:
        start_pos = int(seg["start"] * chars_per_sec)
        end_pos = int(seg["end"] * chars_per_sec)
        duration_chars = end_pos - start_pos

        if duration_chars > 0:
            bar = "#" * duration_chars
            line = " " * start_pos + bar
            line = line[:width]
            lines.append(f"{seg['asset_alias']}: [{line}]")
        else:
            lines.append(f"{seg['asset_alias']}: [точка]")

    return "\n".join(lines)
