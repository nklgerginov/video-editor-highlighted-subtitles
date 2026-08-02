import json
import os
import subprocess
import sys
import wave
from datetime import timedelta
from pathlib import Path

import numpy as np
import speech_recognition as sr

# For video processing
from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
)
from moviepy.video.tools.subtitles import SubtitlesClip

# For audio processing
from pydub import AudioSegment
from PyQt6.QtCore import QSize, Qt, QThread, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPalette, QPixmap
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QApplication,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class SubtitleWord:
    """Represents a word with timing information for highlighting."""

    def __init__(self, text, start_time, end_time):
        self.text = text
        self.start_time = start_time  # in seconds
        self.end_time = end_time  # in seconds


class SubtitleLine:
    """Represents a line of subtitles with multiple words."""

    def __init__(self, words, start_time, end_time):
        self.words = words  # List of SubtitleWord
        self.start_time = start_time
        self.end_time = end_time

    def get_text(self):
        return " ".join(w.text for w in self.words)


class VideoProcessor(QThread):
    """Thread for processing video and generating subtitles."""

    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    processing_complete = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, video_path, model_path=None):
        super().__init__()
        self.video_path = video_path
        self.model_path = model_path
        self._is_running = True

    def run(self):
        try:
            self.message.emit("Extracting audio from video...")
            self.progress.emit(10)

            # Step 1: Extract audio
            audio_path = self._extract_audio()
            if not self._is_running:
                return

            self.message.emit("Converting audio format...")
            self.progress.emit(20)

            # Step 2: Convert audio to WAV format for speech recognition
            wav_path = self._convert_to_wav(audio_path)
            if not self._is_running:
                return

            self.message.emit("Generating subtitles...")
            self.progress.emit(30)

            # Step 3: Generate subtitles with word-level timing
            subtitle_lines = self._generate_subtitles(wav_path)
            if not self._is_running:
                return

            self.progress.emit(90)
            self.message.emit("Processing complete!")
            self.progress.emit(100)
            self.processing_complete.emit(subtitle_lines)

        except Exception as e:
            import traceback

            self.error_occurred.emit(f"Error: {str(e)}\n{traceback.format_exc()}")

    def stop(self):
        self._is_running = False

    def _extract_audio(self):
        """Extract audio from video file."""
        try:
            video = VideoFileClip(self.video_path)
            audio_path = os.path.join(
                os.path.dirname(self.video_path),
                f"{os.path.splitext(os.path.basename(self.video_path))[0]}_audio.mp3",
            )
            video.audio.write_audiofile(audio_path, codec="mp3", bitrate="192k")
            video.close()
            return audio_path
        except Exception as e:
            # Try using ffmpeg directly
            output_path = os.path.join(
                os.path.dirname(self.video_path),
                f"{os.path.splitext(os.path.basename(self.video_path))[0]}_audio.mp3",
            )
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                self.video_path,
                "-vn",
                "-acodec",
                "libmp3lame",
                "-q:a",
                "2",
                output_path,
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path

    def _convert_to_wav(self, audio_path):
        """Convert audio to WAV format for speech recognition."""
        try:
            # Try using moviepy first
            audio = AudioFileClip(audio_path)
            wav_path = os.path.join(
                os.path.dirname(audio_path),
                f"{os.path.splitext(os.path.basename(audio_path))[0]}.wav",
            )
            audio.write_audiofile(wav_path, codec="pcm_s16le", fps=16000)
            audio.close()
            return wav_path
        except Exception:
            # Fallback to ffmpeg
            wav_path = os.path.join(
                os.path.dirname(audio_path),
                f"{os.path.splitext(os.path.basename(audio_path))[0]}.wav",
            )
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                audio_path,
                "-acodec",
                "pcm_s16le",
                "-ac",
                "1",
                "-ar",
                "16000",
                wav_path,
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return wav_path

    def _generate_subtitles(self, wav_path):
        """Generate subtitles with word-level timing using Vosk."""
        if not self.model_path:
            raise ValueError("Vosk model path not provided")

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found at: {self.model_path}")

        # Load Vosk model
        import vosk

        model = vosk.Model(self.model_path)

        # Open audio file
        wf = wave.open(wav_path, "rb")

        # Check audio format
        if wf.getnchannels() != 1:
            # Convert to mono if needed
            wf.close()
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                wav_path,
                "-ac",
                "1",
                "-ar",
                str(wf.getframerate()),
                wav_path + ".mono.wav",
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            wav_path = wav_path + ".mono.wav"
            wf = wave.open(wav_path, "rb")

        if wf.getsampwidth() != 2:
            raise ValueError("Audio must be 16-bit PCM")

        # Create recognizer with word-level timing
        rec = vosk.KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)

        subtitle_lines = []
        current_line_words = []
        current_line_start = 0

        # Process audio in chunks
        while self._is_running:
            data = wf.readframes(4000)
            if len(data) == 0:
                break

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())

                if "result" in result:
                    for item in result["result"]:
                        word = item.get("word", "")
                        start = item.get("start", 0)
                        end = item.get("end", 0)

                        if word:
                            subtitle_word = SubtitleWord(word, start, end)
                            current_line_words.append(subtitle_word)

                            # Create a new line every ~5 seconds or ~10 words
                            if (end - current_line_start > 5.0) or (
                                len(current_line_words) >= 10
                            ):
                                if current_line_words:
                                    line = SubtitleLine(
                                        current_line_words,
                                        current_line_start,
                                        current_line_words[-1].end_time,
                                    )
                                    subtitle_lines.append(line)
                                    current_line_words = []
                                    current_line_start = end

            self.progress.emit(30 + int((wf.tell() / wf.getnframes()) * 50))

        # Add remaining words as last line
        if current_line_words:
            line = SubtitleLine(
                current_line_words, current_line_start, current_line_words[-1].end_time
            )
            subtitle_lines.append(line)

        # Final result
        final_result = json.loads(rec.FinalResult())
        if "result" in final_result:
            for item in final_result["result"]:
                word = item.get("word", "")
                start = item.get("start", 0)
                end = item.get("end", 0)

                if word:
                    subtitle_word = SubtitleWord(word, start, end)
                    current_line_words.append(subtitle_word)

            if current_line_words:
                line = SubtitleLine(
                    current_line_words,
                    current_line_start,
                    current_line_words[-1].end_time,
                )
                subtitle_lines.append(line)

        wf.close()
        return subtitle_lines


class VideoExporter(QThread):
    """Thread for exporting video with subtitles."""

    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    export_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, video_path, subtitle_lines, output_path, subtitle_style=None):
        super().__init__()
        self.video_path = video_path
        self.subtitle_lines = subtitle_lines
        self.output_path = output_path
        self.subtitle_style = subtitle_style or {}
        self._is_running = True

    def run(self):
        try:
            self.message.emit("Loading video...")
            self.progress.emit(10)

            # Load video
            video = VideoFileClip(self.video_path)

            self.message.emit("Generating subtitle clips...")
            self.progress.emit(30)

            # Create subtitle clips
            subtitle_clips = self._create_subtitle_clips(video)

            if not self._is_running:
                video.close()
                return

            self.message.emit("Compositing video...")
            self.progress.emit(50)

            # Composite video with subtitles
            final_video = CompositeVideoClip([video] + subtitle_clips)

            self.message.emit("Exporting video...")
            self.progress.emit(70)

            # Export with proper settings
            final_video.write_videofile(
                self.output_path,
                codec="libx264",
                audio_codec="aac",
                fps=video.fps,
                threads=4,
                preset="fast",
                bitrate="5000k",
                audio_bitrate="192k",
            )

            self.progress.emit(100)
            self.message.emit("Export complete!")
            self.export_complete.emit(self.output_path)

            # Cleanup
            video.close()
            final_video.close()

        except Exception as e:
            import traceback

            self.error_occurred.emit(
                f"Export error: {str(e)}\n{traceback.format_exc()}"
            )

    def stop(self):
        self._is_running = False

    def _create_subtitle_clips(self, video):
        """Create text clips for each subtitle line with word-level highlighting."""
        subtitle_clips = []

        # Get style settings
        font_family = self.subtitle_style.get("font", "Arial")
        fontsize = self.subtitle_style.get("fontsize", 40)
        color = self.subtitle_style.get("color", "white")
        highlight_color = self.subtitle_style.get("highlight_color", "yellow")
        stroke_color = self.subtitle_style.get("stroke_color", "black")
        stroke_width = self.subtitle_style.get("stroke_width", 2)
        highlight_scale = self.subtitle_style.get("highlight_scale", 1.2)  # 20% bigger

        for line in self.subtitle_lines:
            position = ("center", 0.85)

            for word in line.words:
                # Normal word clip (non-highlighted)
                word_clip = (
                    TextClip(
                        word.text,
                        fontsize=fontsize,
                        font=font_family,
                        color=color,
                        stroke_color=stroke_color,
                        stroke_width=stroke_width,
                        bg_color="transparent",
                    )
                    .set_position(position)
                    .set_start(word.start_time)
                    .set_duration(word.end_time - word.start_time)
                )

                # Highlighted word clip (bigger)
                highlighted_clip = (
                    TextClip(
                        word.text,
                        fontsize=int(fontsize * highlight_scale),
                        font=font_family,
                        color=highlight_color,
                        stroke_color=stroke_color,
                        stroke_width=stroke_width,
                        bg_color="transparent",
                    )
                    .set_position(position)
                    .set_start(word.start_time)
                    .set_duration(word.end_time - word.start_time)
                )

                # Add both clips - highlighted will overlay normal
                subtitle_clips.append(word_clip)
                subtitle_clips.append(highlighted_clip)

        return subtitle_clips


class SubtitlePreviewWidget(QWidget):
    """Widget for previewing subtitles with highlighting."""

    def __init__(self, subtitle_lines, parent=None):
        super().__init__(parent)
        self.subtitle_lines = subtitle_lines
        self.current_time = 0
        self.playing = False

        # Setup UI
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # Subtitle display
        self.subtitle_label = QLabel("")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: white;
                background-color: rgba(0, 0, 0, 150);
                padding: 20px;
                border-radius: 10px;
            }
        """)
        self.layout.addWidget(self.subtitle_label)

        # Timer for updating subtitles
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_subtitle)

    def start(self, interval=50):
        """Start subtitle preview updates."""
        self.playing = True
        self.timer.start(interval)

    def stop(self):
        """Stop subtitle preview updates."""
        self.playing = False
        self.timer.stop()

    def set_time(self, time):
        """Set current time and update subtitle."""
        self.current_time = time
        self.update_subtitle()

    def update_subtitle(self):
        """Update displayed subtitle based on current time."""
        if not self.subtitle_lines:
            self.subtitle_label.setText("")
            return

        # Find active subtitle line
        active_line = None
        for line in self.subtitle_lines:
            if line.start_time <= self.current_time <= line.end_time:
                active_line = line
                break

        if active_line:
            # Build HTML with highlighted words
            html = "<div style='text-align: center;'>"
            for word in active_line.words:
                if word.start_time <= self.current_time <= word.end_time:
                    # Highlight active word
                    html += f"<span style='background-color: yellow; color: black; padding: 2px 4px; font-size: 1.2em;'>{word.text}</span> "
                else:
                    html += f"<span>{word.text}</span> "
            html += "</div>"
            self.subtitle_label.setText(html)
        else:
            self.subtitle_label.setText("")


class VideoEditorApp(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Editor - Highlighted Subtitles")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)

        # Load available fonts
        self.font_db = QFontDatabase()
        self.available_fonts = [f.family() for f in self.font_db.families() if f != ""]

        # State
        self.video_path = None
        self.subtitle_lines = []
        self.processor = None
        self.exporter = None
        self.model_path = None

        # Setup UI
        self.init_ui()

        # Setup media player
        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.positionChanged.connect(self.on_media_position_changed)

    def _get_stylesheet(self):
        """Get application stylesheet."""
        return """
        QMainWindow {
            background-color: #2b2b2b;
        }
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QGroupBox {
            border: 1px solid #444;
            border-radius: 5px;
            margin-top: 10px;
            padding: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: #aaa;
        }
        QLabel {
            color: #ccc;
        }
        QPushButton {
            background-color: #444;
            color: #fff;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            min-width: 120px;
        }
        QPushButton:hover {
            background-color: #555;
        }
        QPushButton:disabled {
            background-color: #333;
            color: #666;
        }
        QPushButton[primary="true"] {
            background-color: #0078d7;
        }
        QPushButton[primary="true"]:hover {
            background-color: #0095ff;
        }
        QProgressBar {
            border: 1px solid #444;
            border-radius: 4px;
            text-align: center;
            background-color: #333;
        }
        QProgressBar::chunk {
            background-color: #0078d7;
            border-radius: 3px;
        }
        QComboBox {
            background-color: #444;
            color: #fff;
            border: 1px solid #555;
            padding: 5px;
            border-radius: 4px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QScrollArea {
            border: 1px solid #444;
            background-color: #333;
        }
        QSpinBox, QDoubleSpinBox {
            background-color: #444;
            color: #fff;
            border: 1px solid #555;
            padding: 5px;
            border-radius: 4px;
        }
        """

    def init_ui(self):
        """Initialize user interface."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Header
        header = QLabel("Video Editor - Create Viral Clips with Highlighted Subtitles")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #fff;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        # Main content split
        content_split = QHBoxLayout()
        content_split.setSpacing(10)

        # Left panel - Video and controls
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)

        # Video display group
        video_group = QGroupBox("Video Preview")
        video_layout = QVBoxLayout()

        # Video widget
        self.video_widget = QVideoWidget(self)
        self.video_widget.setStyleSheet("background-color: #000;")
        self.video_widget.setMinimumSize(640, 360)
        video_layout.addWidget(self.video_widget)

        # Video controls
        video_controls = QHBoxLayout()
        video_controls.setSpacing(10)

        self.btn_open = QPushButton("📁 Open Video")
        self.btn_open.clicked.connect(self.open_video)
        video_controls.addWidget(self.btn_open)

        self.btn_play = QPushButton("▶ Play")
        self.btn_play.clicked.connect(self.play_video)
        self.btn_play.setEnabled(False)
        video_controls.addWidget(self.btn_play)

        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_pause.clicked.connect(self.pause_video)
        self.btn_pause.setEnabled(False)
        video_controls.addWidget(self.btn_pause)

        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.clicked.connect(self.stop_video)
        self.btn_stop.setEnabled(False)
        video_controls.addWidget(self.btn_stop)

        video_layout.addLayout(video_controls)
        video_group.setLayout(video_layout)
        left_panel.addWidget(video_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 100)
        left_panel.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel(
            "Ready - Create viral clips with highlighted subtitles!"
        )
        self.status_label.setStyleSheet("color: #aaa;")
        left_panel.addWidget(self.status_label)

        content_split.addLayout(left_panel, 60)

        # Right panel - Subtitles and settings
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)

        # Subtitles group
        subtitles_group = QGroupBox("Subtitles")
        subtitles_layout = QVBoxLayout()

        # Subtitle preview
        self.subtitle_preview = SubtitlePreviewWidget([])
        self.subtitle_preview.setMinimumHeight(200)
        subtitles_layout.addWidget(self.subtitle_preview)

        # Subtitle list
        self.subtitle_list = QScrollArea()
        self.subtitle_list_widget = QWidget()
        self.subtitle_list_layout = QVBoxLayout(self.subtitle_list_widget)
        self.subtitle_list_layout.setSpacing(5)
        self.subtitle_list.setWidget(self.subtitle_list_widget)
        self.subtitle_list.setWidgetResizable(True)
        self.subtitle_list.setMinimumHeight(200)
        subtitles_layout.addWidget(self.subtitle_list)

        subtitles_group.setLayout(subtitles_layout)
        right_panel.addWidget(subtitles_group)

        # Settings group
        settings_group = QGroupBox("Subtitle Settings")
        settings_layout = QFormLayout()
        settings_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        settings_layout.setFormAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        settings_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Font selection
        self.font_combo = QComboBox()
        self.font_combo.addItems(self.available_fonts[:50])  # Limit to first 50 fonts
        self.font_combo.setCurrentText("Arial")
        settings_layout.addRow("Font:", self.font_combo)

        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(20, 100)
        self.font_size_spin.setValue(40)
        settings_layout.addRow("Font Size:", self.font_size_spin)

        # Highlight scale (how much bigger the highlighted word should be)
        self.highlight_scale_spin = QDoubleSpinBox()
        self.highlight_scale_spin.setRange(1.0, 2.0)
        self.highlight_scale_spin.setValue(1.2)
        self.highlight_scale_spin.setSingleStep(0.1)
        settings_layout.addRow("Highlight Scale:", self.highlight_scale_spin)

        # Highlight color
        self.highlight_color_btn = QPushButton("Choose Color")
        self.highlight_color_btn.clicked.connect(self.choose_highlight_color)
        self.highlight_color = QColor(255, 255, 0)  # Yellow
        settings_layout.addRow("Highlight Color:", self.highlight_color_btn)

        settings_group.setLayout(settings_layout)
        right_panel.addWidget(settings_group)

        # Model selection
        model_group = QGroupBox("Speech Recognition")
        model_layout = QVBoxLayout()

        model_form = QFormLayout()

        self.model_combo = QComboBox()
        self.model_combo.addItem("Select model...")
        self.model_combo.currentIndexChanged.connect(self.on_model_selected)
        model_form.addRow("Vosk Model:", self.model_combo)

        model_layout.addLayout(model_form)
        model_group.setLayout(model_layout)
        right_panel.addWidget(model_group)

        # Export group
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout()

        self.btn_generate = QPushButton("🎤 Generate Subtitles")
        self.btn_generate.setProperty("primary", "true")
        self.btn_generate.clicked.connect(self.generate_subtitles)
        self.btn_generate.setEnabled(False)
        export_layout.addWidget(self.btn_generate)

        self.btn_preview = QPushButton("👁 Preview with Subtitles")
        self.btn_preview.clicked.connect(self.preview_with_subtitles)
        self.btn_preview.setEnabled(False)
        export_layout.addWidget(self.btn_preview)

        self.btn_export = QPushButton("💾 Export Video")
        self.btn_export.setProperty("primary", "true")
        self.btn_export.clicked.connect(self.export_video)
        self.btn_export.setEnabled(False)
        export_layout.addWidget(self.btn_export)

        export_group.setLayout(export_layout)
        right_panel.addWidget(export_group)

        content_split.addLayout(right_panel, 40)
        main_layout.addLayout(content_split)

        # Set stylesheet
        self.setStyleSheet(self._get_stylesheet())

        # Scan for Vosk models
        self.scan_vosk_models()

    def choose_highlight_color(self):
        """Open color dialog to choose highlight color."""
        color = QColorDialog.getColor(
            self.highlight_color, self, "Choose Highlight Color"
        )
        if color.isValid():
            self.highlight_color = color
            self.status_label.setText(f"Highlight color set to {color.name()}")

    def scan_vosk_models(self):
        """Scan for available Vosk models."""
        model_dirs = [
            "models",
            os.path.join(os.path.expanduser("~"), "vosk-models"),
            os.path.join(os.path.dirname(__file__), "models"),
        ]

        found_models = []
        for model_dir in model_dirs:
            if os.path.exists(model_dir):
                for item in os.listdir(model_dir):
                    item_path = os.path.join(model_dir, item)
                    if os.path.isdir(item_path) and "vosk" in item.lower():
                        found_models.append(item_path)

        self.model_combo.clear()
        if found_models:
            for model in found_models:
                self.model_combo.addItem(model)
            self.model_combo.setCurrentIndex(0)
            self.model_path = found_models[0]
            self.status_label.setText(f"Model: {os.path.basename(self.model_path)}")
        else:
            self.model_combo.addItem("No models found")
            self.status_label.setText(
                "⚠️ Download Vosk model from https://alphacephei.com/vosk/models"
            )

    def on_model_selected(self, index):
        """Handle model selection."""
        if index > 0:
            self.model_path = self.model_combo.currentText()
            self.status_label.setText(f"Model: {os.path.basename(self.model_path)}")

    def open_video(self):
        """Open video file."""
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Video Files (*.mp4 *.avi *.mov *.mkv *.webm)")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)

        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            video_path = file_dialog.selectedFiles()[0]
            self.load_video(video_path)

    def load_video(self, video_path):
        """Load video file."""
        self.video_path = video_path

        # Stop any current playback
        self.stop_video()

        # Update UI
        self.btn_play.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_generate.setEnabled(True)
        self.btn_preview.setEnabled(False)
        self.btn_export.setEnabled(False)

        # Clear previous subtitles
        self.subtitle_lines = []
        self.update_subtitle_list()
        self.subtitle_preview.stop()

        # Load video into player
        self.media_player.setSource(QUrl.fromLocalFile(video_path))

        # Update status
        self.status_label.setText(f"Loaded: {os.path.basename(video_path)}")

    def play_video(self):
        """Play video."""
        if self.video_path:
            self.media_player.play()
            self.btn_play.setEnabled(False)
            self.btn_pause.setEnabled(True)
            self.btn_stop.setEnabled(True)

            # Start subtitle preview if subtitles exist
            if self.subtitle_lines:
                self.subtitle_preview.start()

    def pause_video(self):
        """Pause video."""
        self.media_player.pause()
        self.btn_play.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.subtitle_preview.stop()

    def stop_video(self):
        """Stop video."""
        self.media_player.stop()
        self.btn_play.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.subtitle_preview.stop()
        self.subtitle_preview.set_time(0)

    def on_media_position_changed(self, position):
        """Handle media player position changes."""
        if self.video_path:
            # Update progress bar
            duration = self.media_player.duration()
            if duration > 0:
                progress = int((position / duration) * 100)
                self.progress_bar.setValue(progress)

            # Update subtitle preview
            if self.subtitle_lines:
                self.subtitle_preview.set_time(position / 1000)  # Convert ms to seconds

    def generate_subtitles(self):
        """Generate subtitles from video."""
        if not self.video_path:
            self.status_label.setText("❌ Error: No video loaded")
            return

        if not self.model_path or not os.path.exists(self.model_path):
            self.status_label.setText("❌ Error: No valid Vosk model selected")
            return

        # Disable buttons during processing
        self.btn_generate.setEnabled(False)
        self.btn_open.setEnabled(False)
        self.btn_play.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)

        # Create and start processor
        self.processor = VideoProcessor(self.video_path, self.model_path)
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.message.connect(self.status_label.setText)
        self.processor.processing_complete.connect(self.on_subtitles_generated)
        self.processor.error_occurred.connect(self.on_processing_error)
        self.processor.start()

    def on_subtitles_generated(self, subtitle_lines):
        """Handle subtitles generation complete."""
        self.subtitle_lines = subtitle_lines
        self.update_subtitle_list()

        # Enable buttons
        self.btn_generate.setEnabled(True)
        self.btn_open.setEnabled(True)
        self.btn_play.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.btn_export.setEnabled(True)

        self.status_label.setText(
            f"✅ Subtitles generated: {len(subtitle_lines)} lines"
        )

    def on_processing_error(self, error):
        """Handle processing error."""
        self.status_label.setText(f"❌ {error}")

        # Re-enable buttons
        self.btn_generate.setEnabled(True)
        self.btn_open.setEnabled(True)
        self.btn_play.setEnabled(True if self.video_path else False)
        self.btn_stop.setEnabled(True if self.video_path else False)

    def update_subtitle_list(self):
        """Update the subtitle list display."""
        # Clear existing items
        for i in reversed(range(self.subtitle_list_layout.count())):
            widget = self.subtitle_list_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Add subtitle lines
        for i, line in enumerate(self.subtitle_lines):
            label = QLabel(
                f"{i+1}. [{self._format_time(line.start_time)} - {self._format_time(line.end_time)}] {line.get_text()}"
            )
            label.setStyleSheet("padding: 5px; border-bottom: 1px solid #444;")
            label.setWordWrap(True)
            self.subtitle_list_layout.addWidget(label)

    def _format_time(self, seconds):
        """Format time in seconds to HH:MM:SS."""
        return str(timedelta(seconds=int(seconds)))

    def preview_with_subtitles(self):
        """Preview video with subtitles."""
        if not self.video_path or not self.subtitle_lines:
            return

        # Stop current playback
        self.stop_video()

        # Create a temporary preview video
        import tempfile

        temp_dir = tempfile.mkdtemp()
        preview_path = os.path.join(temp_dir, "preview.mp4")

        # Get subtitle style from UI
        subtitle_style = {
            "font": self.font_combo.currentText(),
            "fontsize": self.font_size_spin.value(),
            "color": "white",
            "highlight_color": self.highlight_color.name(),
            "stroke_color": "black",
            "stroke_width": 2,
            "highlight_scale": self.highlight_scale_spin.value(),
        }

        # Export with subtitles
        self.exporter = VideoExporter(
            self.video_path,
            self.subtitle_lines,
            preview_path,
            subtitle_style=subtitle_style,
        )

        # Connect signals
        self.exporter.progress.connect(self.progress_bar.setValue)
        self.exporter.message.connect(self.status_label.setText)
        self.exporter.export_complete.connect(
            lambda path: self._on_preview_ready(path, temp_dir)
        )
        self.exporter.error_occurred.connect(self.on_processing_error)

        # Disable buttons during export
        self.btn_generate.setEnabled(False)
        self.btn_open.setEnabled(False)
        self.btn_play.setEnabled(False)
        self.btn_preview.setEnabled(False)
        self.btn_export.setEnabled(False)

        self.exporter.start()

    def _on_preview_ready(self, video_path, temp_dir):
        """Handle preview video ready."""
        # Load the preview video
        self.load_video(video_path)
        self.media_player.play()

        # Cleanup old exporter
        if self.exporter:
            self.exporter.deleteLater()
            self.exporter = None

        # Store temp dir for cleanup
        self._temp_dir = temp_dir

        # Re-enable buttons
        self.btn_generate.setEnabled(True)
        self.btn_open.setEnabled(True)
        self.btn_play.setEnabled(False)  # Video is playing
        self.btn_pause.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.btn_export.setEnabled(True)

        self.status_label.setText("🎬 Preview ready")

    def export_video(self):
        """Export video with subtitles."""
        if not self.video_path or not self.subtitle_lines:
            return

        # Get output path
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("MP4 Video (*.mp4)")
        file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setDefaultSuffix("mp4")

        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            output_path = file_dialog.selectedFiles()[0]

            # Get subtitle style from UI
            subtitle_style = {
                "font": self.font_combo.currentText(),
                "fontsize": self.font_size_spin.value(),
                "color": "white",
                "highlight_color": self.highlight_color.name(),
                "stroke_color": "black",
                "stroke_width": 2,
                "highlight_scale": self.highlight_scale_spin.value(),
            }

            # Create exporter
            self.exporter = VideoExporter(
                self.video_path,
                self.subtitle_lines,
                output_path,
                subtitle_style=subtitle_style,
            )

            # Connect signals
            self.exporter.progress.connect(self.progress_bar.setValue)
            self.exporter.message.connect(self.status_label.setText)
            self.exporter.export_complete.connect(self.on_export_complete)
            self.exporter.error_occurred.connect(self.on_processing_error)

            # Disable buttons during export
            self.btn_generate.setEnabled(False)
            self.btn_open.setEnabled(False)
            self.btn_play.setEnabled(False)
            self.btn_preview.setEnabled(False)
            self.btn_export.setEnabled(False)

            self.exporter.start()

    def on_export_complete(self, output_path):
        """Handle export complete."""
        # Cleanup old exporter
        if self.exporter:
            self.exporter.deleteLater()
            self.exporter = None

        # Re-enable buttons
        self.btn_generate.setEnabled(True)
        self.btn_open.setEnabled(True)
        self.btn_play.setEnabled(True if self.video_path else False)
        self.btn_preview.setEnabled(True)
        self.btn_export.setEnabled(True)

        self.status_label.setText(
            f"✅ Export complete: {os.path.basename(output_path)}"
        )

    def closeEvent(self, event):
        """Handle window close."""
        # Stop any running threads
        if self.processor and self.processor.isRunning():
            self.processor.stop()
            self.processor.wait()

        if self.exporter and self.exporter.isRunning():
            self.exporter.stop()
            self.exporter.wait()

        # Cleanup temp files
        if hasattr(self, "_temp_dir") and os.path.exists(self._temp_dir):
            import shutil

            shutil.rmtree(self._temp_dir, ignore_errors=True)

        event.accept()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    # Create and show main window
    window = VideoEditorApp()
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "____main__":
    main()
