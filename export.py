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
            "txt": text,
            "size": None,
            "color": color,
            "bg_color": bg_color,
            "fontsize": font_size,
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
        except TypeError as e:
            if "multiple values for argument 'font'" in str(e):
                clip_kwargs.pop("font", None)
                clip_kwargs["font"] = font_family
                return TextClip(**clip_kwargs)
            raise

    def _create_highlighted_subtitle_clips(self, video: VideoFileClip) -> List:
        subtitle_clips = []
        style = self.project.style
        position = self.project.position

        bg_clip = ColorClip(
            size=(position.width, position.height),
            color=(0, 0, 0, 128),
            duration=self.project.subtitles[-1].end_time if self.project.subtitles else video.duration
        )
        bg_clip = bg_clip.set_position((position.x, position.y), relative=False).set_start(0)
        subtitle_clips.append(bg_clip)

        x_pos = position.x + 20
        y_pos = position.y + 20 + style.font_size

        for line in self.project.subtitles:
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
                    int(style.font_size * style.highlight_scale),
                    style.highlight_color,
                    "transparent"
                )

                normal_clip = normal_clip.set_position((x_pos, y_pos), relative=False)
                highlight_clip = highlight_clip.set_position((x_pos, y_pos), relative=False)

                normal_clip = normal_clip.set_start(word.start_time).set_duration(
                    word.end_time - word.start_time
                )
                highlight_clip = highlight_clip.set_start(word.start_time).set_duration(
                    word.end_time - word.start_time
                )

                subtitle_clips.append(normal_clip)
                subtitle_clips.append(highlight_clip)

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