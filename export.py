"""Video export module for creating videos with highlighted subtitles."""
import os
from typing import List, Optional
from moviepy import VideoFileClip, CompositeVideoClip, TextClip, ColorClip
from models import VideoProject, SubtitleStyle, SubtitlePosition


class VideoExporter:
    def __init__(self, project: VideoProject):
        self.project = project

    def _get_font_path(self, font_family: str) -> Optional[str]:
        font_paths = [
            f"{font_family}.ttf",
            f"/usr/share/fonts/{font_family}.ttf",
            f"/usr/share/fonts/truetype/{font_family}.ttf",
            f"C:/Windows/Fonts/{font_family}.ttf",
            f"C:/Windows/Fonts/{font_family}.TTF"
        ]
        for path in font_paths:
            if os.path.exists(path):
                return path
        return None

    def _create_text_clip(
        self,
        text: str,
        font_family: str,
        font_size: int,
        color: str,
        bg_color: str = "transparent",
        font_path: Optional[str] = None
    ) -> Optional[TextClip]:
        # Skip empty text to avoid zero-sized clips
        if not text or not text.strip():
            return None
            
        clip_kwargs = {
            "text": text,
            "size": None,
            "color": color,
            "bg_color": bg_color if bg_color != "transparent" else None,
            "font_size": font_size,
            "stroke_color": None,
            "stroke_width": 0
        }

        if font_path is None:
            font_path = self._get_font_path(font_family)

        if font_path and os.path.exists(font_path):
            clip_kwargs["font"] = font_path
        else:
            clip_kwargs["font"] = font_family

        try:
            text_clip = TextClip(**clip_kwargs)
            # Ensure the clip has valid dimensions
            if hasattr(text_clip, 'w') and hasattr(text_clip, 'h'):
                if text_clip.w <= 0 or text_clip.h <= 0:
                    # Fallback: create a minimal clip if sizing failed
                    text_clip = TextClip(text, fontsize=font_size, color=color, size=(100, font_size + 10))
            return text_clip
        except (TypeError, ValueError, OSError) as e:
            error_msg = str(e)
            if "multiple values for argument 'font'" in error_msg:
                clip_kwargs.pop("font", None)
                clip_kwargs["font"] = font_family
                try:
                    text_clip = TextClip(**clip_kwargs)
                    if hasattr(text_clip, 'w') and hasattr(text_clip, 'h'):
                        if text_clip.w <= 0 or text_clip.h <= 0:
                            text_clip = TextClip(text, fontsize=font_size, color=color, size=(100, font_size + 10))
                    return text_clip
                except (ValueError, OSError):
                    pass
            
            if "Invalid font" in error_msg or "cannot open resource" in error_msg:
                pass
            
            clip_kwargs.pop("font", None)
            clip_kwargs.pop("size", None)
            try:
                text_clip = TextClip(**clip_kwargs)
                if hasattr(text_clip, 'w') and hasattr(text_clip, 'h'):
                    if text_clip.w <= 0 or text_clip.h <= 0:
                        text_clip = TextClip(text, fontsize=font_size, color=color, size=(100, font_size + 10))
                return text_clip
            except:
                # Last resort: create a minimal clip
                return TextClip(text or " ", fontsize=font_size, color=color, size=(100, font_size + 10))

    def _create_highlighted_subtitle_clips(self, video: VideoFileClip) -> List:
        subtitle_clips = []
        style = self.project.style
        
        position = self.project.position

        # Ensure position has valid dimensions
        if position.width <= 0:
            position.width = 800
        if position.height <= 0:
            position.height = 200
            
        bg_duration = video.duration
        if self.project.subtitles:
            try:
                bg_duration = max(line.end_time for line in self.project.subtitles)
            except ValueError:
                # No subtitles, use video duration
                bg_duration = video.duration
        
        # Create background clip only if we have subtitles
        if self.project.subtitles:
            bg_clip = ColorClip(
                size=(position.width, position.height),
                color=(0, 0, 0, style.background_opacity if hasattr(style, 'background_opacity') else 128),
                duration=bg_duration
            ).with_position((position.x, position.y)).with_start(0)
            subtitle_clips.append(bg_clip)

        # Get highlight font size from style
        highlight_font_size = getattr(style, 'highlight_font_size', int(style.font_size * 1.5))
        
        x_pos = position.x + 20
        y_pos = position.y + 20 + style.font_size

        for line in self.project.subtitles:
            line_x_pos = x_pos
            for word in line.words:
                # Skip empty words
                if not word.text or not word.text.strip():
                    continue
                    
                normal_clip = self._create_text_clip(
                    word.text,
                    style.font_family,
                    style.font_size,
                    style.text_color,
                    "transparent"
                )

                highlight_clip = self._create_text_clip(
                    word.text,
                    style.font_family,
                    highlight_font_size,
                    style.highlight_color,
                    "transparent"
                )

                # Skip if clips couldn't be created
                if normal_clip is None or highlight_clip is None:
                    continue

                normal_clip = normal_clip.with_position((line_x_pos, y_pos)).with_start(word.start_time).with_duration(
                    word.end_time - word.start_time
                )
                highlight_clip = highlight_clip.with_position((line_x_pos, y_pos)).with_start(word.start_time).with_duration(
                    word.end_time - word.start_time
                )

                subtitle_clips.append(normal_clip)
                subtitle_clips.append(highlight_clip)
                
                # Calculate word width based on actual clip width if available
                word_width = max(10, normal_clip.w if hasattr(normal_clip, 'w') else len(word.text) * style.font_size * 0.6)
                line_x_pos += word_width + 10
            
            y_pos += style.font_size * 1.5

        return subtitle_clips

    def export(self, output_path: str, quality: str = "high", fps: int = 30) -> str:
        video = VideoFileClip(self.project.video_path)
        quality_params = {
            "low": {"bitrate": "500k"},
            "medium": {"bitrate": "2000k"},
            "high": {"bitrate": "5000k"},
            "ultra": {"bitrate": "10000k"}
        }
        params = quality_params.get(quality, quality_params["high"])

        try:
            subtitle_clips = self._create_highlighted_subtitle_clips(video)
            
            # Only create composite if we have subtitle clips
            if subtitle_clips:
                final_video = CompositeVideoClip(
                    [video] + subtitle_clips
                )
            else:
                # No subtitles to add, just re-encode the video
                final_video = video
                
            final_video.write_videofile(
                output_path,
                fps=fps,
                codec="libx264",
                audio_codec="aac",
                bitrate=params["bitrate"],
                threads=4,
                ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p"]
            )
            return output_path
        except Exception as e:
            video.close()
            raise RuntimeError(f"Export failed: {str(e)}")
        finally:
            video.close()
