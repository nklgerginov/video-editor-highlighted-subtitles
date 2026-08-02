import sys
import os
import json
import re
import wave
import shutil
import subprocess
import tempfile
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
    QFileDialog,
    QColorDialog,
    QFontComboBox,
    QSpinBox,
    QFrame,
    QMessageBox,
    QProgressBar,
    QGroupBox,
    QComboBox,
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

from vosk import Model, KaldiRecognizer


def configure_ffmpeg_for_dependencies():
    ffmpeg_path = shutil.which("ffmpeg") or shutil.which("avconv")
    ffprobe_path = shutil.which("ffprobe") or shutil.which("avprobe")

    if not ffmpeg_path:
        try:
            from imageio_ffmpeg import get_ffmpeg_exe

            ffmpeg_path = get_ffmpeg_exe()
        except Exception:
            ffmpeg_path = None

    if not ffprobe_path and ffmpeg_path:
        candidate = Path(ffmpeg_path).with_name("ffprobe.exe")
        if candidate.exists():
            ffprobe_path = str(candidate)

    if not ffmpeg_path:
        print(
            "Warning: ffmpeg/avconv not found. Install ffmpeg or add it to PATH "
            "for better audio/video processing support."
        )
        return None, None

    ffmpeg_dir = str(Path(ffmpeg_path).parent)
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    os.environ["FFMPEG_BINARY"] = ffmpeg_path
    if ffprobe_path:
        os.environ["FFPROBE_BINARY"] = ffprobe_path
    return ffmpeg_path, ffprobe_path


FFMPEG_BINARY, FFPROBE_BINARY = configure_ffmpeg_for_dependencies()

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
    QFileDialog,
    QColorDialog,
    QFontComboBox,
    QSpinBox,
    QFrame,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

from vosk import Model, KaldiRecognizer


def run_ffmpeg_command(args, check=True, cwd=None):
    if not FFMPEG_BINARY:
        raise RuntimeError("ffmpeg is not available")

    result = subprocess.run(
        [FFMPEG_BINARY, *args], capture_output=True, text=True, cwd=cwd
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or result.stdout.strip() or "ffmpeg failed"
        )
    return result


def get_video_duration(video_path):
    if FFPROBE_BINARY:
        try:
            result = subprocess.run(
                [
                    FFPROBE_BINARY,
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(video_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            value = result.stdout.strip()
            if value:
                return float(value)
        except Exception:
            pass

    result = run_ffmpeg_command(["-i", str(video_path)], check=False)
    match = re.search(
        r"Duration:\s+(\d{2}):(\d{2}):(\d{2})\.(\d+)", result.stderr or ""
    )
    if match:
        hours, minutes, seconds, millis = match.groups()
        return (
            int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000.0
        )
    return 0.0


def transcribe_with_vosk(audio_path, model_path):
    if not model_path.exists():
        raise FileNotFoundError(f"Vosk model not found at {model_path}")

    model = Model(str(model_path))
    recognizer = KaldiRecognizer(model, 16000)

    words = []
    with wave.open(str(audio_path), "rb") as audio_file:
        while True:
            chunk = audio_file.readframes(4000)
            if not chunk:
                break
            if recognizer.AcceptWaveform(chunk):
                result = json.loads(recognizer.Result())
                words.extend(result.get("result", []))

    final_result = json.loads(recognizer.FinalResult())
    words.extend(final_result.get("result", []))
    return words


class SubtitleWord:
    def __init__(self, text, start_time, end_time):
        self.text = text
        self.start_time = start_time
        self.end_time = end_time


class SubtitleLine:
    def __init__(self, words, start_time, end_time):
        self.words = words
        self.start_time = start_time
        self.end_time = end_time

    def get_text(self):
        return " ".join(w.text for w in self.words)


class VideoUploaderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Uploader")
        self.resize(900, 620)
        self.selected_video_path = None
        self.subtitle_items = []
        self.word_level_subtitles = []
        self.generated_subtitles_path = None
        self.vosk_model_path = (
            Path(__file__).resolve().parent / "models" / "vosk-model-en-us-0.22-lgraph"
        )
        self.export_dir = Path(__file__).resolve().parent / "exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.font_family = "Arial"
        self.font_size = 28
        self.normal_text_color = QColor("white")
        self.highlight_text_color = QColor("yellow")
        self.current_step = "Ready"

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title_label = QLabel("Upload a video to begin")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        button_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        upload_button = QPushButton("Choose Video")
        upload_button.clicked.connect(self.choose_video)
        button_row.addWidget(upload_button)

        self.preview_button = QPushButton("Preview Video")
        self.preview_button.setEnabled(False)
        self.preview_button.clicked.connect(self.preview_selected_video)
        button_row.addWidget(self.preview_button)

        self.process_button = QPushButton("Process Video")
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self.process_video)
        button_row.addWidget(self.process_button)

        self.generate_button = QPushButton("Generate Subtitles")
        self.generate_button.setEnabled(False)
        self.generate_button.clicked.connect(self.generate_subtitles)
        button_row.addWidget(self.generate_button)

        self.export_button = QPushButton("Export Video")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_video)
        button_row.addWidget(self.export_button)

        layout.addLayout(button_row)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        self.step_label = QLabel("Step: ready")
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.step_label)

        controls_group = QGroupBox("Subtitle styling & export")
        controls_layout = QHBoxLayout(controls_group)
        controls_layout.setSpacing(8)

        style_label = QLabel("Style")
        controls_layout.addWidget(style_label)

        self.style_preset_combo = QComboBox(self)
        self.style_preset_combo.addItems(
            ["Default", "Streamer Glow", "Editorial Clean", "Creator Bold"]
        )
        self.style_preset_combo.currentTextChanged.connect(self.apply_style_preset)
        controls_layout.addWidget(self.style_preset_combo)

        self.font_combo = QFontComboBox(self)
        self.font_combo.setCurrentFont(QFont(self.font_family))
        self.font_combo.currentFontChanged.connect(self._update_font_family)
        controls_layout.addWidget(self.font_combo)

        self.font_size_spin = QSpinBox(self)
        self.font_size_spin.setRange(16, 72)
        self.font_size_spin.setValue(self.font_size)
        self.font_size_spin.valueChanged.connect(self._update_font_size)
        controls_layout.addWidget(self.font_size_spin)

        self.normal_color_button = QPushButton("Normal")
        self.normal_color_button.clicked.connect(self.choose_normal_color)
        controls_layout.addWidget(self.normal_color_button)

        self.highlight_color_button = QPushButton("Highlight")
        self.highlight_color_button.clicked.connect(self.choose_highlight_color)
        controls_layout.addWidget(self.highlight_color_button)

        self.reset_style_button = QPushButton("Reset")
        self.reset_style_button.clicked.connect(self.reset_style_to_defaults)
        controls_layout.addWidget(self.reset_style_button)

        self.open_exports_button = QPushButton("Open exports")
        self.open_exports_button.clicked.connect(self.open_export_folder)
        controls_layout.addWidget(self.open_exports_button)

        layout.addWidget(controls_group)
        self._refresh_style_button_labels()

        self.path_label = QLabel("No video selected")
        self.path_label.setWordWrap(True)
        self.path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.path_label.setFrameShape(QFrame.Shape.Box)
        self.path_label.setFrameShadow(QFrame.Shadow.Sunken)
        self.path_label.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.path_label)

        self.video_widget = QVideoWidget(self)
        self.video_widget.setMinimumHeight(280)
        self.video_widget.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_widget)

        self.hint_label = QLabel(
            "Tip: pick a preset, generate subtitles, then export a polished MP4 for your audience."
        )
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet("color: #555; font-size: 10pt;")
        layout.addWidget(self.hint_label)

        self.status_label = QLabel("Select a video file to continue.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        self.setStyleSheet(
            "QMainWindow { background: #f5f5f5; }"
            "QLabel { color: #222; }"
            "QPushButton { padding: 8px 16px; }"
            "QPushButton#primary { background: #1f8ceb; color: white; }"
            "QGroupBox { font-weight: bold; border: 1px solid #ccc; margin-top: 8px; }"
        )

    def choose_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video",
            str(self.export_dir),
            "Video Files (*.mp4 *.avi *.mov *.mkv *.webm);;All Files (*)",
        )

        if file_path:
            self.selected_video_path = file_path
            self.path_label.setText(file_path)
            self.preview_button.setEnabled(True)
            self.process_button.setEnabled(True)
            self.generate_button.setEnabled(True)
            self.export_button.setEnabled(False)
            self.subtitle_items = []
            self.word_level_subtitles = []
            self.generated_subtitles_path = None
            self.status_label.setText(f"Selected: {Path(file_path).name}")
        else:
            self.preview_button.setEnabled(False)
            self.process_button.setEnabled(False)
            self.generate_button.setEnabled(False)
            self.export_button.setEnabled(False)
            self.status_label.setText("No video selected.")

    def preview_selected_video(self):
        if not self.selected_video_path:
            self._set_status("No video selected.")
            return

        try:
            self.media_player.stop()
            self.media_player.setSource(QUrl.fromLocalFile(self.selected_video_path))
            self.media_player.play()
            self.status_label.setText(
                f"Previewing: {Path(self.selected_video_path).name}"
            )
        except Exception as exc:
            self.status_label.setText(f"Could not preview video: {exc}")

    def process_video(self):
        if not self.selected_video_path:
            self._set_status("No video selected.")
            return

        try:
            duration = get_video_duration(self.selected_video_path)
            if duration <= 0:
                raise RuntimeError("The selected video could not be read")
            self._set_status(
                f"Video loaded: {Path(self.selected_video_path).name} ({duration:.2f}s)",
                progress=10,
                step="Video loaded",
            )
        except Exception as exc:
            self._set_status(
                f"Could not process video: {exc}", progress=0, step="Error"
            )

    def generate_subtitles(self):
        if not self.selected_video_path:
            self._set_status("No video selected.")
            return

        try:
            duration = get_video_duration(self.selected_video_path)
            self._set_status("Extracting audio...", progress=10, step="Audio extract")

            audio_path = (
                Path(tempfile.gettempdir())
                / f"{Path(self.selected_video_path).stem}_audio.wav"
            )
            run_ffmpeg_command(
                [
                    "-y",
                    "-i",
                    str(self.selected_video_path),
                    "-vn",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-acodec",
                    "pcm_s16le",
                    str(audio_path),
                ]
            )
            self._set_status("Audio extracted.", progress=20, step="Audio ready")

            if not self.vosk_model_path.exists():
                raise FileNotFoundError(
                    "Vosk model not found. Download it and place it in the models folder."
                )

            self._set_status("Transcribing speech...", progress=30, step="Transcribing")
            words = transcribe_with_vosk(audio_path, self.vosk_model_path)
            self._set_progress(60, "Transcription complete")

            self.subtitle_items = self._build_subtitles_from_words(words, duration)
            self.word_level_subtitles = self._build_word_level_subtitles(
                words, duration
            )

            if not self.subtitle_items:
                self.subtitle_items = []
            if not self.word_level_subtitles:
                self.word_level_subtitles = []

            if self.subtitle_items:
                self.generated_subtitles_path = self._write_srt(self.subtitle_items)
                self.export_button.setEnabled(True)
                self._set_status(
                    f"Generated {len(self.subtitle_items)} subtitle blocks.",
                    progress=100,
                    step="Ready to export",
                )
            else:
                self.generated_subtitles_path = None
                self.export_button.setEnabled(False)
                self._set_status(
                    "No speech detected in the selected clip.",
                    progress=100,
                    step="No speech",
                )
        except Exception as exc:
            self.subtitle_items = []
            self.generated_subtitles_path = None
            self.export_button.setEnabled(False)
            self._set_status(
                f"Subtitle generation failed: {exc}",
                progress=0,
                step="Error",
            )

    def _build_subtitles_from_words(self, words, duration):
        if not words:
            return []

        subtitle_items = []
        current_words = []
        current_start = None
        current_end = None

        for item in words:
            word_text = (item.get("word") or "").strip()
            if not word_text:
                continue

            start_time = float(item.get("start", 0.0))
            end_time = float(item.get("end", start_time + 0.5))

            if not current_words:
                current_start = start_time
                current_end = end_time
                current_words = [word_text]
            else:
                if len(current_words) >= 5 or (start_time - current_end) > 0.8:
                    subtitle_items.append(
                        (current_start, current_end, " ".join(current_words))
                    )
                    current_start = start_time
                    current_end = end_time
                    current_words = [word_text]
                else:
                    current_end = end_time
                    current_words.append(word_text)

        if current_words:
            subtitle_items.append(
                (current_start or 0.0, current_end or duration, " ".join(current_words))
            )

        return subtitle_items

    def _build_word_level_subtitles(self, words, duration):
        if not words:
            return []

        subtitle_items = []
        for item in words:
            word_text = (item.get("word") or "").strip()
            if not word_text:
                continue

            start_time = float(item.get("start", 0.0))
            end_time = float(item.get("end", start_time + 0.35))
            if end_time <= start_time:
                end_time = start_time + 0.35
            subtitle_items.append((start_time, end_time, word_text))

        return subtitle_items

    def _write_srt(self, subtitles):
        output_path = self.export_dir / f"{Path(self.selected_video_path).stem}.srt"
        self.export_dir.mkdir(parents=True, exist_ok=True)
        lines = []
        for index, (start_time, end_time, text) in enumerate(subtitles, 1):
            lines.append(str(index))
            lines.append(
                f"{self._format_timestamp(start_time)} --> {self._format_timestamp(end_time)}"
            )
            lines.append(text)
            lines.append("")

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return str(output_path)

    def _format_timestamp(self, seconds):
        total_seconds = max(0, int(seconds))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _as_ass_color(self, color):
        return f"&H00{color.blue():02X}{color.green():02X}{color.red():02X}"

    def _refresh_style_button_labels(self):
        self.normal_color_button.setText(
            f"Normal color ({self.normal_text_color.name().upper()})"
        )
        self.highlight_color_button.setText(
            f"Highlight color ({self.highlight_text_color.name().upper()})"
        )

    def _sync_style_controls(self):
        resolved_font = self.font_family
        if resolved_font not in {"Arial", "Montserrat", "Segoe UI", "Impact"}:
            available_fonts = [
                self.font_combo.itemText(i) for i in range(self.font_combo.count())
            ]
            if resolved_font in available_fonts:
                resolved_font = resolved_font
            elif "Arial" in available_fonts:
                resolved_font = "Arial"
            elif available_fonts:
                resolved_font = available_fonts[0]
            else:
                resolved_font = "Sans Serif"
        self.font_combo.setCurrentFont(QFont(resolved_font))
        self.font_size_spin.setValue(self.font_size)
        self._refresh_style_button_labels()

    def _update_font_family(self, font):
        self.font_family = font.family()

    def _update_font_size(self, value):
        self.font_size = value

    def apply_style_preset(self, preset_name):
        presets = {
            "Default": {
                "font_family": "Arial",
                "font_size": 28,
                "normal_color": QColor("white"),
                "highlight_color": QColor("yellow"),
            },
            "Streamer Glow": {
                "font_family": "Montserrat",
                "font_size": 34,
                "normal_color": QColor("white"),
                "highlight_color": QColor("#ffcc00"),
            },
            "Editorial Clean": {
                "font_family": "Segoe UI",
                "font_size": 26,
                "normal_color": QColor("#f5f5f5"),
                "highlight_color": QColor("#67e8f9"),
            },
            "Creator Bold": {
                "font_family": "Impact",
                "font_size": 38,
                "normal_color": QColor("white"),
                "highlight_color": QColor("#ff4d6d"),
            },
        }
        settings = presets.get(preset_name, presets["Default"])
        self.font_family = settings["font_family"]
        self.font_size = settings["font_size"]
        self.normal_text_color = settings["normal_color"]
        self.highlight_text_color = settings["highlight_color"]
        self._sync_style_controls()
        self._set_status(f"Style preset applied: {preset_name}")

    def reset_style_to_defaults(self):
        self.font_family = "Arial"
        self.font_size = 28
        self.normal_text_color = QColor("white")
        self.highlight_text_color = QColor("yellow")
        self._sync_style_controls()
        self.style_preset_combo.setCurrentText("Default")
        self._set_status("Style reset to defaults")

    def choose_normal_color(self):
        color = QColorDialog.getColor(self.normal_text_color, self, "Choose color")
        if color.isValid():
            self.normal_text_color = color
            self._refresh_style_button_labels()

    def choose_highlight_color(self):
        color = QColorDialog.getColor(self.highlight_text_color, self, "Choose color")
        if color.isValid():
            self.highlight_text_color = color
            self._refresh_style_button_labels()

    def _get_subtitle_style_settings(self):
        return {
            "font_family": self.font_family or "Arial",
            "font_size": max(16, int(self.font_size or 28)),
            "normal_color": self.normal_text_color or QColor("white"),
            "highlight_color": self.highlight_text_color or QColor("yellow"),
        }

    def _write_ass_subtitles(self, subtitles, output_path):
        settings = self._get_subtitle_style_settings()
        normal_color = self._as_ass_color(settings["normal_color"])
        highlight_color = self._as_ass_color(settings["highlight_color"])
        font_family = settings["font_family"]
        font_size = settings["font_size"]

        lines = ["[Script Info]", "Title: Generated Subtitles", "ScriptType: v4.00+"]
        lines.append("PlayResX: 640")
        lines.append("PlayResY: 480")
        lines.append("\n[V4+ Styles]")
        lines.append(
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"
        )
        lines.append(
            f"Style: Default,{font_family},{font_size},{normal_color},&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1"
        )
        lines.append(
            f"Style: Highlight,{font_family},{font_size + 2},{highlight_color},&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1"
        )
        lines.append("\n[Events]")
        lines.append(
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        )

        for start_time, end_time, text in subtitles:
            style_name = "Highlight" if len(text.split()) == 1 else "Default"
            lines.append(
                f"Dialogue: 0,{self._format_ass_timestamp(start_time)},{self._format_ass_timestamp(end_time)},{style_name},,0,0,0,,{text}"
            )

        Path(output_path).write_text("\n".join(lines), encoding="utf-8")
        return output_path

    def _format_ass_timestamp(self, seconds):
        total_seconds = int(seconds)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

    def _build_subtitles_filter(self, ass_path):
        ass_path = Path(ass_path)
        if not ass_path.is_absolute():
            normalized_path = ass_path.as_posix()
        else:
            normalized_path = ass_path.name
        return f"subtitles=filename='{normalized_path}'"

    def _set_progress(self, percent, step=None):
        self.progress_bar.setValue(max(0, min(100, percent)))
        if step:
            self.step_label.setText(f"Step: {step}")

    def _set_status(self, message, progress=None, step=None):
        self.status_label.setText(message)
        if progress is not None:
            self._set_progress(progress, step)
        elif step:
            self._set_progress(self.progress_bar.value(), step)

    def open_export_folder(self):
        try:
            if not self.export_dir.exists():
                self.export_dir.mkdir(parents=True, exist_ok=True)
            os.startfile(str(self.export_dir))
        except Exception:
            subprocess.run(["explorer", str(self.export_dir)])

    def export_video(self):
        if not self.selected_video_path:
            self.status_label.setText("No video selected.")
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Video",
            str(
                self.export_dir
                / f"{Path(self.selected_video_path).stem}_with_subtitles.mp4"
            ),
            "MP4 Video (*.mp4)",
        )
        if not output_path:
            return

        output_path = str(Path(output_path).expanduser())

        try:
            subtitle_entries = self.word_level_subtitles or self.subtitle_items
            if not subtitle_entries:
                raise RuntimeError("No subtitles available to export.")

            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            ass_path = output_dir / f"{Path(output_path).stem}_subtitles.ass"
            self._write_ass_subtitles(subtitle_entries, ass_path)

            self._set_status(
                "Exporting video with subtitles...", progress=40, step="Exporting"
            )
            filter_string = self._build_subtitles_filter(ass_path)
            run_ffmpeg_command(
                [
                    "-y",
                    "-i",
                    str(self.selected_video_path),
                    "-vf",
                    filter_string,
                    "-c:v",
                    "libx264",
                    "-c:a",
                    "aac",
                    output_path,
                ],
                cwd=str(output_dir),
            )

            self._set_status(
                f"Export complete: {Path(output_path).name}",
                progress=100,
                step="Done",
            )
            QMessageBox.information(
                self, "Export complete", f"Video exported to {output_path}"
            )
        except Exception as exc:
            self._set_status(f"Export failed: {exc}", progress=0, step="Error")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoUploaderWindow()
    window.show()
    sys.exit(app.exec())
