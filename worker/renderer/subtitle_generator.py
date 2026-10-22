from pathlib import Path
from typing import List, Dict


class SubtitleGenerator:
    """Generate ASS subtitle files in TikTok/YouTube style"""

    def generate_ass(
        self, subtitles: List[Dict], output_path: Path, preset: str = "tiktok"
    ) -> Path:
        """Generate ASS file from subtitles"""
        ass_content = self._build_ass_content(subtitles, preset)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

        return output_path

    def _build_ass_content(self, subtitles: List[Dict], preset: str = "tiktok") -> str:
        """Build ASS file content"""
        # Determine resolution based on preset
        if preset == "youtube":
            play_res_x = 1920
            play_res_y = 1080
            subtitle_y = 950  # Bottom center for 16:9
        else:  # tiktok
            play_res_x = 1080
            play_res_y = 1920
            subtitle_y = 1750  # Bottom center for 9:16

        # ASS header
        header = f"""[Script Info]
Title: Video Script Engine Subtitles
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TikTokStylePassive, Arial Bold, 64, &H00FFFFFF, &H000000FF, &H00000000, &H80000000, 1, 0, 0, 0, 100, 100, 0, 0, 1, 4, 2, 2, 10, 10, 50, 1
Style: TikTokStyleActive, Arial Bold, 64, &H00FFFFFF, &H000000FF, &H00000000, &H00FFFF00, 1, 0, 0, 0, 100, 100, 0, 0, 1, 4, 2, 2, 10, 10, 50, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        # Subtitle events
        events = []
        center_x = play_res_x // 2
        for subtitle in subtitles:
            start_time = self._seconds_to_ass_time(subtitle["start"])
            end_time = self._seconds_to_ass_time(subtitle["end"])
            text = subtitle["text"].replace("\\", "\\\\").replace(",", "\\,")
            is_active = subtitle.get("is_active", False)

            # Choose style based on active/passive
            style = "TikTokStyleActive" if is_active else "TikTokStylePassive"

            # Build dialogue line
            if is_active:
                # Active: yellow background with border-radius 20px
                # Use clip for rounded corners: \clip(center_x-100, subtitle_y-40, center_x+100, subtitle_y+40)
                # For simplicity, we'll use a box with rounded corners
                clip_x1 = center_x - 200
                clip_y1 = subtitle_y - 40
                clip_x2 = center_x + 200
                clip_y2 = subtitle_y + 40
                # Border radius effect using clip and border
                dialogue = f"Dialogue: 0,{start_time},{end_time},{style},,0,0,0,,{{\\an2\\pos({center_x},{subtitle_y})\\b1\\3c&H000000&\\4c&H000000&\\shad4\\fs64\\clip({clip_x1},{clip_y1},{clip_x2},{clip_y2})}}{text}"
            else:
                # Passive: standard style
                dialogue = f"Dialogue: 0,{start_time},{end_time},{style},,0,0,0,,{{\\an2\\pos({center_x},{subtitle_y})\\b1\\3c&H000000&\\4c&H000000&\\shad4\\fs64}}{text}"

            events.append(dialogue)

        return header + "\n".join(events)

    def _seconds_to_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format (H:MM:SS.cc)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
