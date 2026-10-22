import ffmpeg
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from config.settings import settings

logger = logging.getLogger(__name__)


class FFmpegRenderer:
    """FFmpeg-based video renderer"""

    def render(
        self,
        execution_plan: Dict[str, Any],
        output_path: Path,
        subtitle_file: Optional[Path] = None,
    ):
        """Render video from execution plan"""
        logger.info(f"Starting render to {output_path}")

        preset = execution_plan.get("preset", "tiktok")

        # Step 1: Extract segments
        logger.info("Step 1: Extracting segments")
        segment_files = []
        for i, segment in enumerate(execution_plan["timeline"]):
            asset_path = Path(execution_plan["assets"][segment["asset"]]["path"])
            segment_file = settings.storage_output_path / f"segment_{i}.mp4"
            mute_audio = segment.get("mute_audio", False)
            logger.info(
                f"Extracting segment {i+1}/{len(execution_plan['timeline'])} (mute_audio={mute_audio})"
            )
            self._extract_segment(
                asset_path, segment["in"], segment["out"], segment_file, mute_audio
            )
            segment_files.append(segment_file)
        logger.info(f"Step 1 completed: {len(segment_files)} segments extracted")

        # Step 2: Convert segments to preset format
        logger.info(f"Step 2: Converting segments to {preset} format")
        converted_files = []
        for i, segment_file in enumerate(segment_files):
            logger.info(f"Converting segment {i+1}/{len(segment_files)}")
            converted_file = settings.storage_output_path / f"converted_{i}.mp4"
            self._convert_to_preset(segment_file, converted_file, preset)
            converted_files.append(converted_file)
        logger.info(f"Step 2 completed: {len(converted_files)} segments converted")

        # Step 3: Concatenate segments
        logger.info("Step 3: Concatenating segments")
        concatenated_file = settings.storage_output_path / "concatenated.mp4"
        self._concatenate_segments(converted_files, concatenated_file)
        logger.info("Step 3 completed: segments concatenated")

        # Step 4: Mix audio
        logger.info("Step 4: Mixing audio")
        audio_mixed_file = settings.storage_output_path / "audio_mixed.mp4"
        self._mix_audio(concatenated_file, execution_plan["audio"], audio_mixed_file)
        logger.info("Step 4 completed: audio mixed")

        # Step 5: Add overlays
        logger.info("Step 5: Adding overlays")
        overlays_file = audio_mixed_file
        overlays = execution_plan.get("overlays", [])
        if overlays:
            logger.info(f"Adding {len(overlays)} overlays")
            overlays_file = settings.storage_output_path / "with_overlays.mp4"
            self._add_overlays(audio_mixed_file, overlays, overlays_file, preset)
            logger.info("Overlays added")
        else:
            logger.info("No overlays to add")

        # Step 6: Add subtitles and final render
        logger.info("Step 6: Adding subtitles and final render")
        if subtitle_file:
            logger.info(f"Subtitle file provided: {subtitle_file}")
            logger.info(f"Subtitle file exists: {subtitle_file.exists()}")
            self._add_subtitles(overlays_file, subtitle_file, output_path)
            logger.info("Subtitles added")
        else:
            # Just copy if no subtitles
            import shutil

            logger.info("No subtitles, copying file")
            shutil.copy(overlays_file, output_path)
        logger.info("Step 6 completed")

        logger.info(f"Render completed: {output_path}")

    def _extract_segment(
        self,
        input_path: Path,
        in_sec: float,
        out_sec: float,
        output_path: Path,
        mute_audio: bool = False,
    ):
        """Extract segment from video"""
        logger.info(
            f"Extracting segment: {in_sec} - {out_sec} from {input_path} (mute_audio={mute_audio})"
        )

        # Check if input has audio
        probe = ffmpeg.probe(str(input_path))
        has_audio = any(s["codec_type"] == "audio" for s in probe["streams"])

        input_stream = ffmpeg.input(str(input_path), ss=in_sec, to=out_sec)

        if mute_audio or not has_audio:
            # No audio or muted - video only
            logger.info("Extracting segment without audio")
            (
                input_stream.output(
                    str(output_path),
                    vcodec="libx264",
                    **{"b:v": "5M"},
                    r=30,
                    avoid_negative_ts="make_zero",
                    an=None,  # No audio
                )
                .overwrite_output()
                .run(quiet=True)
            )
        else:
            # Re-encode to ensure audio is preserved
            logger.info("Re-encoding segment with audio")
            (
                input_stream.output(
                    str(output_path),
                    vcodec="libx264",
                    acodec="aac",
                    **{"b:v": "5M", "b:a": "192k"},
                    r=30,
                    avoid_negative_ts="make_zero",
                )
                .overwrite_output()
                .run(quiet=True)
            )

    def _convert_to_preset(
        self, input_path: Path, output_path: Path, preset: str = "tiktok"
    ):
        """Convert video to preset aspect ratio"""
        logger.info(f"Converting to {preset} format: {input_path}")

        # Get input video info
        probe = ffmpeg.probe(str(input_path))
        video_info = next(s for s in probe["streams"] if s["codec_type"] == "video")
        width = int(video_info["width"])
        height = int(video_info["height"])
        has_audio = any(s["codec_type"] == "audio" for s in probe["streams"])

        # Target resolution based on preset
        if preset == "youtube":
            target_width = 1920
            target_height = 1080
            target_aspect = 16 / 9
        else:  # tiktok
            target_width = 1080
            target_height = 1920
            target_aspect = 9 / 16

        # Calculate crop/scale
        input_aspect = width / height

        video_input = ffmpeg.input(str(input_path))

        if input_aspect > target_aspect:
            # Input is wider, crop width (center crop)
            new_width = int(height * target_aspect)
            x_offset = (width - new_width) // 2
            video_stream = video_input.filter(
                "crop", new_width, height, x_offset, 0
            ).filter("scale", target_width, target_height)
        else:
            # Input is taller, crop height (center crop)
            new_height = int(width / target_aspect)
            y_offset = (height - new_height) // 2
            video_stream = video_input.filter(
                "crop", width, new_height, 0, y_offset
            ).filter("scale", target_width, target_height)

        # Preserve audio if exists
        if has_audio:
            logger.info("Preserving audio during conversion")
            (
                ffmpeg.output(
                    video_stream,
                    video_input["a"],
                    str(output_path),
                    vcodec="libx264",
                    acodec="aac",
                    **{"b:v": "5M", "b:a": "192k"},
                    r=30,
                )
                .overwrite_output()
                .run(quiet=True)
            )
        else:
            logger.info("No audio, video only")
            (
                ffmpeg.output(video_stream, str(output_path), vcodec="libx264", r=30)
                .overwrite_output()
                .run(quiet=True)
            )

    def _concatenate_segments(self, segment_files: list, output_path: Path):
        """Concatenate video segments"""
        logger.info(f"Concatenating {len(segment_files)} segments")

        # Create concat file
        concat_file = settings.storage_output_path / "concat.txt"
        with open(concat_file, "w") as f:
            for segment_file in segment_files:
                f.write(f"file '{segment_file.absolute()}'\n")

        # Use re-encoding instead of copy to ensure audio is preserved
        # Check if segments have audio
        has_audio = False
        for segment_file in segment_files:
            probe = ffmpeg.probe(str(segment_file))
            if any(s["codec_type"] == "audio" for s in probe["streams"]):
                has_audio = True
                break

        if has_audio:
            # Re-encode to ensure audio is preserved
            logger.info("Re-encoding with audio preservation")
            (
                ffmpeg.input(str(concat_file), format="concat", safe=0)
                .output(
                    str(output_path),
                    vcodec="libx264",
                    acodec="aac",
                    **{"b:v": "5M", "b:a": "192k"},
                    r=30,
                )
                .overwrite_output()
                .run(quiet=True)
            )
        else:
            # No audio, just copy
            logger.info("No audio in segments, copying")
            (
                ffmpeg.input(str(concat_file), format="concat", safe=0)
                .output(str(output_path), c="copy")
                .overwrite_output()
                .run(quiet=True)
            )

    def _mix_audio(
        self, video_path: Path, audio_config: Dict[str, Any], output_path: Path
    ):
        """Mix audio: original + BGM + SFX"""
        logger.info("Mixing audio")

        # Get video info
        probe = ffmpeg.probe(str(video_path))
        has_audio = any(s["codec_type"] == "audio" for s in probe["streams"])
        video_duration = float(probe["format"]["duration"])

        # Check if we have BGM or SFX
        has_bgm = audio_config.get("bgm") and Path(audio_config["bgm"]["file"]).exists()
        has_sfx = any(Path(sfx["file"]).exists() for sfx in audio_config.get("sfx", []))

        # Simple case: no BGM, no SFX - just copy video as-is
        if not has_bgm and not has_sfx:
            logger.info("No BGM or SFX, copying video as-is")
            import shutil

            shutil.copy(video_path, output_path)
            return

        # Complex case: need to mix audio
        logger.info("Mixing audio with BGM/SFX")
        video_input = ffmpeg.input(str(video_path))
        audio_streams = []

        # Original audio (if exists)
        if has_audio:
            try:
                original_audio = video_input["a"]
                audio_streams.append(original_audio)
                logger.info("Added original audio")
            except Exception as e:
                logger.warning(f"Could not get original audio: {e}")

        # BGM
        if has_bgm:
            bgm_path = Path(audio_config["bgm"]["file"])
            bgm_volume = audio_config["bgm"]["volume"]
            bgm_start_sec = audio_config["bgm"].get("start_sec")
            bgm_duration = audio_config["bgm"].get("duration")
            logger.info(
                f"Adding BGM: {bgm_path} at volume {bgm_volume}, start_sec={bgm_start_sec}, duration={bgm_duration}"
            )
            bgm_input = ffmpeg.input(str(bgm_path))
            bgm_audio = bgm_input["a"]

            # Apply start delay if specified
            if bgm_start_sec and bgm_start_sec > 0:
                delay_ms = int(bgm_start_sec * 1000)
                bgm_audio = ffmpeg.filter(bgm_audio, "adelay", f"{delay_ms}|{delay_ms}")
                # Pad before delay
                bgm_audio = ffmpeg.filter(bgm_audio, "apad", whole_dur=video_duration)

            # Loop to match video duration
            bgm_audio = ffmpeg.filter(bgm_audio, "aloop", loop=-1, size=2e09)

            # Trim to video duration or specified duration
            trim_duration = bgm_duration if bgm_duration else video_duration
            if bgm_start_sec:
                # Adjust trim duration if start delay is applied
                trim_duration = min(
                    trim_duration, video_duration - (bgm_start_sec or 0)
                )
            bgm_audio = ffmpeg.filter(bgm_audio, "atrim", duration=trim_duration)

            # Apply volume
            bgm_audio = ffmpeg.filter(bgm_audio, "volume", bgm_volume)

            # Pad to match video duration
            bgm_audio = ffmpeg.filter(bgm_audio, "apad", whole_dur=video_duration)
            audio_streams.append(bgm_audio)

        # SFX - add at the specified time with optional duration trim
        for sfx in audio_config.get("sfx", []):
            sfx_path = Path(sfx["file"])
            if sfx_path.exists():
                sfx_duration = sfx.get("duration")
                logger.info(
                    f"Adding SFX: {sfx_path} at {sfx['at']}s, duration={sfx_duration}"
                )
                sfx_input = ffmpeg.input(str(sfx_path))
                sfx_audio = sfx_input["a"]

                # Trim duration if specified
                if sfx_duration:
                    sfx_audio = ffmpeg.filter(sfx_audio, "atrim", duration=sfx_duration)

                # Apply volume
                sfx_audio = ffmpeg.filter(sfx_audio, "volume", sfx["volume"])

                # Apply delay
                delay_ms = int(sfx["at"] * 1000)
                sfx_audio = ffmpeg.filter(sfx_audio, "adelay", f"{delay_ms}|{delay_ms}")

                # Pad to match video duration
                sfx_audio = ffmpeg.filter(sfx_audio, "apad", whole_dur=video_duration)
                audio_streams.append(sfx_audio)

        # Mix audio streams
        if len(audio_streams) > 1:
            logger.info(f"Mixing {len(audio_streams)} audio streams")
            mixed_audio = ffmpeg.filter(
                audio_streams, "amix", inputs=len(audio_streams), duration="longest"
            )
        elif len(audio_streams) == 1:
            logger.info("Using single audio stream")
            mixed_audio = audio_streams[0]
        else:
            logger.info("No audio, creating silent track")
            mixed_audio = ffmpeg.input(
                "anullsrc=channel_layout=stereo:sample_rate=44100",
                f="lavfi",
            )["a"]

        logger.info("Running FFmpeg audio mix command")
        try:
            (
                ffmpeg.output(
                    video_input["v"],
                    mixed_audio,
                    str(output_path),
                    vcodec="copy",
                    acodec="aac",
                    **{"b:a": "192k"},  # Audio bitrate
                )
                .overwrite_output()
                .run(quiet=True, overwrite_output=True)
            )
            logger.info(f"Audio mix completed: {output_path}")
        except Exception as e:
            logger.error(f"Audio mix failed: {str(e)}")
            raise

    def _add_overlays(
        self,
        video_path: Path,
        overlays: List[Dict],
        output_path: Path,
        preset: str = "tiktok",
    ):
        """Add overlays (images/text) to video"""
        logger.info(f"Adding {len(overlays)} overlays to video")

        # Get video resolution
        probe = ffmpeg.probe(str(video_path))
        video_info = next(s for s in probe["streams"] if s["codec_type"] == "video")
        video_width = int(video_info["width"])
        video_height = int(video_info["height"])

        video_input = ffmpeg.input(str(video_path))
        current_stream = video_input["v"]

        # Process each overlay
        for i, overlay in enumerate(overlays):
            overlay_type = overlay["type"]
            start_sec = overlay["start_sec"]
            end_sec = overlay["end_sec"]
            position = overlay["position"]
            x_offset = overlay.get("x_offset", 0.0)
            y_offset = overlay.get("y_offset", 0.0)
            opacity = overlay.get("opacity", 1.0)
            width = overlay.get("width")
            height = overlay.get("height")

            logger.info(
                f"Processing overlay {i+1}: {overlay_type} at {start_sec}-{end_sec}s"
            )

            if overlay_type in ["image", "video"]:
                overlay_path = Path(overlay["path"])
                if not overlay_path.exists():
                    logger.warning(f"Overlay file not found: {overlay_path}, skipping")
                    continue

                # Calculate position
                # Add padding from edges (5% of video height/width)
                padding_y = int(video_height * 0.05)
                padding_x = int(video_width * 0.05)
                overlay_height = height or 100
                overlay_width = width or 100
                if position == "top":
                    y_pos = padding_y + y_offset
                else:  # bottom
                    y_pos = video_height - padding_y - overlay_height - y_offset
                x_pos = (video_width // 2) + x_offset - (overlay_width // 2)

                # Load overlay (image or video)
                overlay_duration = end_sec - start_sec

                # For video overlays, handle looping if needed
                if overlay_type == "video":
                    try:
                        overlay_probe = ffmpeg.probe(str(overlay_path))
                        overlay_video_duration = float(
                            overlay_probe["format"]["duration"]
                        )
                        if overlay_video_duration < overlay_duration:
                            # Loop the video to match duration using stream_loop
                            loop_count = (
                                int(overlay_duration / overlay_video_duration) + 1
                            )
                            overlay_input = ffmpeg.input(
                                str(overlay_path), stream_loop=loop_count
                            )
                            overlay_video = overlay_input["v"]
                            # Trim to exact duration
                            overlay_video = overlay_video.filter(
                                "trim", duration=overlay_duration
                            )
                            overlay_video = overlay_video.filter(
                                "setpts", "PTS-STARTPTS"
                            )
                        else:
                            # Video is longer, trim to duration
                            overlay_input = ffmpeg.input(str(overlay_path))
                            overlay_video = overlay_input["v"]
                            overlay_video = overlay_video.filter(
                                "trim", duration=overlay_duration
                            )
                            overlay_video = overlay_video.filter(
                                "setpts", "PTS-STARTPTS"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Could not probe overlay video duration: {e}, using as-is"
                        )
                        overlay_input = ffmpeg.input(str(overlay_path))
                        overlay_video = overlay_input["v"]
                else:
                    # Image overlay
                    overlay_input = ffmpeg.input(str(overlay_path))
                    overlay_video = overlay_input["v"]

                # Apply chroma key if needed
                if overlay.get("use_chromakey"):
                    chromakey_color = overlay.get("chromakey_color", "#00FF00")
                    similarity = overlay.get("chromakey_similarity", 0.3)
                    blend = overlay.get("chromakey_blend", 0.1)
                    # Convert hex color to RGB for FFmpeg
                    color_hex = chromakey_color.lstrip("#")
                    color_ffmpeg = f"0x{color_hex}"
                    overlay_video = overlay_video.filter(
                        "chromakey",
                        color=color_ffmpeg,
                        similarity=similarity,
                        blend=blend,
                    )

                # Scale overlay if needed
                if width or height:
                    overlay_video = overlay_video.filter(
                        "scale", width or -1, height or -1
                    )

                # Apply opacity
                if opacity < 1.0:
                    overlay_video = overlay_video.filter("format", "rgba")
                    # Create alpha channel adjustment
                    overlay_video = overlay_video.filter(
                        "colorchannelmixer", aa=opacity
                    )

                # Overlay on video at specific time
                current_stream = current_stream.overlay(
                    overlay_video,
                    x=x_pos,
                    y=y_pos,
                    enable=f"between(t,{start_sec},{end_sec})",
                )

            elif overlay_type == "text":
                text = overlay.get("text", "")
                font_size = overlay.get("font_size", 48)
                font_color = overlay.get("font_color", "white")
                bg_color = overlay.get("background_color", "yellow")
                border_radius = overlay.get("border_radius", 20)
                font_family = overlay.get("font_family")
                outline_width = overlay.get("outline_width", 0)
                outline_color = overlay.get("outline_color", "black")
                shadow_x = overlay.get("shadow_x", 0)
                shadow_y = overlay.get("shadow_y", 0)
                shadow_color = overlay.get("shadow_color", "black")
                background_opacity = overlay.get("background_opacity", 0.9)

                # Calculate position
                # Add padding from edges (10% of video height)
                padding = int(video_height * 0.1)
                if position == "top":
                    y_pos = padding + y_offset + (font_size // 2)
                else:  # bottom
                    # Position from bottom with padding, accounting for text height
                    # font_size gives approximate text height, add some margin
                    text_height_approx = (
                        font_size + (outline_width * 2) + 20
                    )  # Add outline and padding
                    y_pos = video_height - padding - y_offset - text_height_approx
                x_pos = (video_width // 2) + x_offset

                # Build drawtext filter parameters
                drawtext_params = {
                    "text": text,
                    "fontsize": font_size,
                    "fontcolor": font_color,
                    "x": f"(w-text_w)/2+{x_offset}",
                    "y": f"{y_pos}",
                    "enable": f"between(t,{start_sec},{end_sec})",
                }

                # Add font family if specified
                if font_family:
                    drawtext_params["fontfile"] = (
                        font_family  # Note: requires font file path
                    )

                # Add outline (border)
                if outline_width > 0:
                    drawtext_params["borderw"] = outline_width
                    drawtext_params["bordercolor"] = outline_color

                # Add shadow
                if shadow_x != 0 or shadow_y != 0:
                    drawtext_params["shadowx"] = shadow_x
                    drawtext_params["shadowy"] = shadow_y
                    drawtext_params["shadowcolor"] = shadow_color

                # Add background box if background color is specified
                if bg_color:
                    # Apply background opacity
                    if background_opacity < 1.0:
                        # Convert hex color to rgba with opacity
                        if bg_color.startswith("#"):
                            bg_hex = bg_color[1:]
                            r = int(bg_hex[0:2], 16)
                            g = int(bg_hex[2:4], 16)
                            b = int(bg_hex[4:6], 16)
                            bg_color_rgba = f"0x{r:02X}{g:02X}{b:02X}{int(background_opacity * 255):02X}"
                        else:
                            bg_color_rgba = f"{bg_color}@{background_opacity}"
                    else:
                        bg_color_rgba = bg_color

                    drawtext_params["box"] = 1
                    drawtext_params["boxcolor"] = bg_color_rgba
                    # Note: FFmpeg drawtext doesn't support border-radius directly
                    # boxborderw is padding around text, not border-radius
                    # We use it as padding to create space around text
                    if border_radius > 0:
                        # Use border_radius as padding value
                        drawtext_params["boxborderw"] = border_radius

                # Apply text overlay at specific time
                current_stream = current_stream.filter("drawtext", **drawtext_params)

        # Output video with overlays
        has_audio = any(s["codec_type"] == "audio" for s in probe["streams"])
        output_args = {"vcodec": "libx264", **{"b:v": "5M"}}
        if has_audio:
            output_args["acodec"] = "aac"
            output_args["b:a"] = "192k"

        try:
            if has_audio:
                (
                    ffmpeg.output(
                        current_stream,
                        video_input["a"],
                        str(output_path),
                        **output_args,
                    )
                    .overwrite_output()
                    .run(quiet=True)
                )
            else:
                (
                    ffmpeg.output(current_stream, str(output_path), **output_args)
                    .overwrite_output()
                    .run(quiet=True)
                )
            logger.info(f"Overlays added successfully to {output_path}")
        except Exception as e:
            logger.error(f"Failed to add overlays: {str(e)}")
            raise

    def _add_subtitles(self, video_path: Path, subtitle_file: Path, output_path: Path):
        """Add subtitles to video"""
        logger.info(f"Adding subtitles from {subtitle_file}")

        # Verify subtitle file exists
        if not subtitle_file.exists():
            logger.error(f"Subtitle file not found: {subtitle_file}")
            raise FileNotFoundError(f"Subtitle file not found: {subtitle_file}")

        logger.info(f"Subtitle file exists, size: {subtitle_file.stat().st_size} bytes")

        # Read subtitle file to verify content
        try:
            with open(subtitle_file, "r", encoding="utf-8") as f:
                content = f.read()
                logger.info(
                    f"Subtitle file content preview (first 200 chars): {content[:200]}"
                )
        except Exception as e:
            logger.warning(f"Could not read subtitle file: {e}")

        # Use absolute path and escape properly for FFmpeg
        subtitle_path = str(subtitle_file.absolute())
        # Escape single quotes and backslashes for shell
        subtitle_path_escaped = subtitle_path.replace("'", "'\\''")

        try:
            # Method 1: Use ass filter (preferred for ASS files)
            logger.info("Trying ass filter")
            video_input = ffmpeg.input(str(video_path))
            video_stream = video_input.video.filter("ass", subtitle_path)
            output = ffmpeg.output(
                video_stream,
                video_input["a"],
                str(output_path),
                vcodec="libx264",
                acodec="aac",
                **{"b:v": "5M", "b:a": "192k"},
            )
            output.overwrite_output().run(quiet=True)
            logger.info(
                f"Subtitles added successfully with ass filter to {output_path}"
            )
        except Exception as e:
            logger.warning(f"ass filter failed: {str(e)}, trying subtitles filter")
            try:
                # Method 2: Use subtitles filter (fallback)
                logger.info("Trying subtitles filter")
                video_input = ffmpeg.input(str(video_path))
                video_stream = video_input.video.filter("subtitles", subtitle_path)
                output = ffmpeg.output(
                    video_stream,
                    video_input["a"],
                    str(output_path),
                    vcodec="libx264",
                    acodec="aac",
                    **{"b:v": "5M", "b:a": "192k"},
                )
                output.overwrite_output().run(quiet=True)
                logger.info(
                    f"Subtitles added successfully with subtitles filter to {output_path}"
                )
            except Exception as e2:
                logger.error(f"subtitles filter also failed: {str(e2)}")
                # Method 3: Use vf parameter as last resort
                try:
                    logger.info("Trying vf parameter method")
                    (
                        ffmpeg.input(str(video_path))
                        .output(
                            str(output_path),
                            vf=f"ass={subtitle_path_escaped}",
                            vcodec="libx264",
                            acodec="aac",
                            **{"b:v": "5M", "b:a": "192k"},
                        )
                        .overwrite_output()
                        .run(quiet=True)
                    )
                    logger.info(
                        f"Subtitles added successfully with vf parameter to {output_path}"
                    )
                except Exception as e3:
                    logger.error(f"All methods failed. Last error: {str(e3)}")
                    raise
