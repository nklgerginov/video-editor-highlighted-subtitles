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
    ) -> TextClip:
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
            return TextClip(**clip_kwargs)
        except (TypeError, ValueError, OSError) as e:
            error_msg = str(e)
            if "multiple values for argument 'font'" in error_msg:
                clip_kwargs.pop("font", None)
                clip_kwargs["font"] = font_family
                try:
                    return TextClip(**clip_kwargs)
                except (ValueError, OSError):
                    pass
            
            if "Invalid font" in error_msg or "cannot open resource" in error_msg:
                pass
            
            clip_kwargs.pop("font", None)
            clip_kwargs.pop("size", None)
            return TextClip(**clip_kwargs)

    def _create_highlighted_subtitle_clips(self, video: VideoFileClip) -> List:
        subtitle_clips = []
        style = self.project.style
  
        position = self.project.position

        bg_duration = video.duration
        if self.project.subtitles:
            bg_duration = max(line.end_time for line in self.project.subtitles)
        
        bg_clip = ColorClip(
            size=(position.width, position.height),
            color=(0, 0, 0, 128),
            duration=bg_duration
        ).with_position((position.x, position.y)).with_start(0)
        subtitle_clips.append(bg_clip)

        x_pos = position.x + 20
        y_pos = position.y + 20 + style.font_size

        for line in self.project.subtitles:
            line_x_pos = x_pos
            for word in line.words:
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
                    style.highlight_font_size,
                    style.highlight_color,
                    "transparent"
                )

                normal_clip = normal_clip.with_position((line_x_pos, y_pos)).with_start(word.start_time).with_duration(
                    word.end_time - word.start_time
                )
                highlight_clip = highlight_clip.with_position((line_x_pos, y_pos)).with_start(word.start_time).with_duration(
                    word.end_time - word.start_time
                )

                subtitle_clips.append(normal_clip)
                subtitle_clips.append(highlight_clip)
                
                word_width = len(word.text) * style.font_size * 0.6
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
            final_video = CompositeVideoClip(
                [video] + self._create_highlighted_subtitle_clips(video)
            )
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