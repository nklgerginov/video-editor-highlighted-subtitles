"""Data models for the video editor with highlighted subtitles."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Word:
    text: str
    start_time: float
    end_time: float
    is_highlighted: bool = False


@dataclass
class SubtitleLine:
    words: List[Word] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0

    def add_word(self, word: Word):
        self.words.append(word)

    @property
    def text(self) -> str:
        return " ".join(word.text for word in self.words)


@dataclass
class SubtitleStyle:
    font_family: str = "Arial"
    font_size: int = 40
    highlight_scale: float = 1.5
    text_color: str = "#FFFFFF"
    highlight_color: str = "#FFFF00"


@dataclass
class SubtitlePosition:
    x: int = 50
    y: int = 50
    width: int = 800
    height: int = 200


@dataclass
class VideoProject:
    video_path: str = ""
    vosk_model_path: str = ""
    subtitles: List[SubtitleLine] = field(default_factory=list)
    style: SubtitleStyle = field(default_factory=SubtitleStyle)
    position: SubtitlePosition = field(default_factory=SubtitlePosition)
