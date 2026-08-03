"""Data models for the video editor with highlighted subtitles."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict


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
    highlight_font_size: int = 60
    text_color: str = "#FFFFFF"
    highlight_color: str = "#FFFF00"
    bold: bool = True
    italic: bool = False
    stroke_color: str = "#000000"
    stroke_width: int = 2
    background_opacity: int = 128
    animation: str = "none"


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
    
    def get_all_words(self) -> List[Word]:
        words = []
        for line in self.subtitles:
            words.extend(line.words)
        return words
    
    def get_active_word_at_time(self, time: float) -> Optional[Word]:
        for word in self.get_all_words():
            if word.start_time <= time < word.end_time:
                return word
        return None

STYLE_PRESETS: Dict[str, SubtitleStyle] = {
    "TikTok Bold": SubtitleStyle(
        font_family="Arial",
        font_size=48,
        highlight_font_size=72,
        text_color="#FFFFFF",
        highlight_color="#FF0000",
        bold=True,
        italic=False,
        stroke_color="#000000",
        stroke_width=3,
        background_opacity=200,
        animation="none"
    ),
    "Instagram Elegant": SubtitleStyle(
        font_family="Helvetica",
        font_size=40,
        highlight_font_size=60,
        text_color="#000000",
        highlight_color="#FF69B4",
        bold=False,
        italic=True,
        stroke_color="#FFFFFF",
        stroke_width=1,
        background_opacity=0,
        animation="fade"
    ),
    "YouTube Clean": SubtitleStyle(
        font_family="Roboto",
        font_size=36,
        highlight_font_size=54,
        text_color="#FFFFFF",
        highlight_color="#FFFF00",
        bold=True,
        italic=False,
        stroke_color="#000000",
        stroke_width=2,
        background_opacity=128,
        animation="none"
    ),
    "Viral Pop": SubtitleStyle(
        font_family="Impact",
        font_size=50,
        highlight_font_size=80,
        text_color="#FFD700",
        highlight_color="#FF00FF",
        bold=True,
        italic=False,
        stroke_color="#000000",
        stroke_width=4,
        background_opacity=200,
        animation="pulse"
    ),
    "Minimalist": SubtitleStyle(
        font_family="Arial",
        font_size=32,
        highlight_font_size=48,
        text_color="#CCCCCC",
        highlight_color="#FFFFFF",
        bold=False,
        italic=False,
        stroke_color="#000000",
        stroke_width=0,
        background_opacity=0,
        animation="none"
    )
}
