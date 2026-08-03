import os
import sys
from typing import Optional
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout, QMessageBox, QFileDialog, QColorDialog, QApplication)
from PyQt6.QtGui import QPixmap, QImage, QFontDatabase, QFont, QColor
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal, QThread
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from models import VideoProject, SubtitleStyle, SubtitlePosition
from processing import SubtitleGenerator
from export import VideoExporter
from .preview import VideoPreviewWidget


class ProcessingThread(QThread):
    processing_complete = pyqtSignal(VideoProject)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, video_path: str, vosk_model_path: str):
        super().__init__()
        self.video_path = video_path
        self.vosk_model_path = vosk_model_path
    
    def run(self):
        try:
            generator = SubtitleGenerator(self.vosk_model_path)
            project = generator.process_video(self.video_path, self.vosk_model_path)
            self.processing_complete.emit(project)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ExportThread(QThread):
    export_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, project: VideoProject, output_path: str):
        super().__init__()
        self.project = project
        self.output_path = output_path
    
    def run(self):
        try:
            exporter = VideoExporter(self.project)
            exporter.export(self.output_path)
            self.export_complete.emit(self.output_path)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Editor - Highlighted Subtitles")
        self.setMinimumSize(1200, 800)
        self.project = VideoProject()
        self.current_video_path = ""
        self.current_time = 0.0
        self._setup_ui()
        self._setup_connections()
        self._load_fonts()
        self._setup_media_player()
        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self._update_playback)

    def _setup_ui(self):
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        self.preview_widget = VideoPreviewWidget()
        self.preview_widget.setMinimumSize(800, 450)
        left_panel.addWidget(self.preview_widget, stretch=1)
        controls_group = QGroupBox("Video Controls")
        controls_layout = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addStretch()
        self.time_label = QLabel("00:00:00")
        controls_layout.addWidget(self.time_label)
        controls_group.setLayout(controls_layout)
        left_panel.addWidget(controls_group)
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)
        vosk_group = QGroupBox("Vosk Model")
        vosk_layout = QVBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.addItem("vosk-model-en-us-0.22-lgraph")
        self.model_combo.addItem("vosk-model-small-en-us-0.15")
        self.model_combo.setEditable(True)
        vosk_layout.addWidget(QLabel("Select Vosk Model:"))
        vosk_layout.addWidget(self.model_combo)
        vosk_group.setLayout(vosk_layout)
        right_panel.addWidget(vosk_group)
        self.process_button = QPushButton("Generate Subtitles")
        self.process_button.setEnabled(False)
        right_panel.addWidget(self.process_button)
        self.processing_label = QLabel("Processing...")
        self.processing_label.setVisible(False)
        right_panel.addWidget(self.processing_label)
        style_group = QGroupBox("Subtitle Style")
        style_layout = QFormLayout()
        self.font_combo = QComboBox()
        self._populate_font_combo()
        style_layout.addRow("Font:", self.font_combo)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 200)
        self.font_size_spin.setValue(40)
        style_layout.addRow("Font Size:", self.font_size_spin)
        self.highlight_scale_spin = QDoubleSpinBox()
        self.highlight_scale_spin.setRange(1.0, 3.0)
        self.highlight_scale_spin.setValue(1.5)
        self.highlight_scale_spin.setSingleStep(0.1)
        style_layout.addRow("Highlight Scale:", self.highlight_scale_spin)
        self.text_color_button = QPushButton("Choose Text Color")
        self.text_color = QColor(255, 255, 255)
        self._update_color_button(self.text_color_button, self.text_color)
        style_layout.addRow("Text Color:", self.text_color_button)
        self.highlight_color_button = QPushButton("Choose Highlight Color")
        self.highlight_color = QColor(255, 255, 0)
        self._update_color_button(self.highlight_color_button, self.highlight_color)
        style_layout.addRow("Highlight Color:", self.highlight_color_button)
        style_group.setLayout(style_layout)
        right_panel.addWidget(style_group)
        position_group = QGroupBox("Subtitle Position (Drag & Drop)")
        position_layout = QVBoxLayout()
        position_layout.addWidget(QLabel("Drag the subtitle box in the preview to position it"))
        self.save_position_button = QPushButton("Save Current Position")
        position_layout.addWidget(self.save_position_button)
        self.position_label = QLabel("Position: 50px, 50px")
        position_layout.addWidget(self.position_label)
        position_form = QFormLayout()
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 2000)
        self.x_spin.setValue(50)
        position_form.addRow("X Position (px):", self.x_spin)
        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 2000)
        self.y_spin.setValue(50)
        position_form.addRow("Y Position (px):", self.y_spin)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 2000)
        self.width_spin.setValue(800)
        position_form.addRow("Width (px):", self.width_spin)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(50, 1000)
        self.height_spin.setValue(200)
        position_form.addRow("Height (px):", self.height_spin)
        position_layout.addLayout(position_form)
        position_group.setLayout(position_layout)
        right_panel.addWidget(position_group)
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout()
        self.export_button = QPushButton("Export Video with Subtitles")
        self.export_button.setEnabled(False)
        export_layout.addWidget(self.export_button)
        self.export_label = QLabel("Exporting...")
        self.export_label.setVisible(False)
        export_layout.addWidget(self.export_label)
        export_group.setLayout(export_layout)
        right_panel.addWidget(export_group)
        right_panel.addStretch()
        main_layout.addLayout(left_panel, stretch=2)
        main_layout.addLayout(right_panel, stretch=1)

    def _setup_connections(self):
        self.play_button.clicked.connect(self._play_video)
        self.pause_button.clicked.connect(self._pause_video)
        self.stop_button.clicked.connect(self._stop_video)
        self.process_button.clicked.connect(self._generate_subtitles)
        self.font_combo.currentTextChanged.connect(self._update_style)
        self.font_size_spin.valueChanged.connect(self._update_style)
        self.highlight_scale_spin.valueChanged.connect(self._update_style)
        self.text_color_button.clicked.connect(self._choose_text_color)
        self.highlight_color_button.clicked.connect(self._choose_highlight_color)
        self.save_position_button.clicked.connect(self._save_position)
        self.x_spin.valueChanged.connect(self._update_position_from_spins)
        self.y_spin.valueChanged.connect(self._update_position_from_spins)
        self.width_spin.valueChanged.connect(self._update_position_from_spins)
        self.height_spin.valueChanged.connect(self._update_position_from_spins)
        self.preview_widget.position_changed.connect(self._update_position_spins)
        self.export_button.clicked.connect(self._export_video)

    def _setup_media_player(self):
        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.media_player.setAudioOutput(self.audio_output)
        self.video_sink = QVideoWidget(self)
        self.media_player.setVideoOutput(self.video_sink)
        self.media_player.positionChanged.connect(self._update_time_display)

    def _load_fonts(self):
        font_db = QFontDatabase()
        families = font_db.families()
        self.font_combo.clear()
        self.font_combo.addItems(families)
        for font in ["Arial", "Helvetica", "Times New Roman", "Courier New"]:
            if font in families:
                self.font_combo.setCurrentText(font)
                break

    def _populate_font_combo(self):
        self.font_combo.clear()
        self.font_combo.addItems(QFontDatabase().families())

    def _update_color_button(self, button, color):
        button.setStyleSheet(f"background-color: {color.name()}; color: {'black' if color.lightness() > 128 else 'white'};")

    def _update_style(self):
        if not self.project:
            self.project = VideoProject()
        self.project.style = SubtitleStyle(
            font_family=self.font_combo.currentText(),
            font_size=self.font_size_spin.value(),
            highlight_scale=self.highlight_scale_spin.value(),
            text_color=self.text_color.name(),
            highlight_color=self.highlight_color.name()
        )
        if self.preview_widget.project:
            self.preview_widget.set_project(self.project)

    def _choose_text_color(self):
        color = QColorDialog.getColor(self.text_color, self, "Choose Text Color")
        if color.isValid():
            self.text_color = color
            self._update_color_button(self.text_color_button, color)
            self._update_style()

    def _choose_highlight_color(self):
        color = QColorDialog.getColor(self.highlight_color, self, "Choose Highlight Color")
        if color.isValid():
            self.highlight_color = color
            self._update_color_button(self.highlight_color_button, color)
            self._update_style()

    def _update_position_spins(self, position: SubtitlePosition):
        self.x_spin.setValue(position.x)
        self.y_spin.setValue(position.y)
        self.width_spin.setValue(position.width)
        self.height_spin.setValue(position.height)
        self.position_label.setText(f"Position: {position.x}px, {position.y}px")

    def _update_position_from_spins(self):
        if not self.project:
            return
        position = SubtitlePosition(x=self.x_spin.value(), y=self.y_spin.value(), width=self.width_spin.value(), height=self.height_spin.value())
        self.project.position = position
        if self.preview_widget.scene.subtitle_box:
            self.preview_widget.scene.subtitle_box.setRect(0, 0, position.width, position.height)
            self.preview_widget.scene.subtitle_box.setPos(position.x, position.y)
            self.preview_widget.scene.subtitle_box.update_resize_handles()
        self.position_label.setText(f"Position: {position.x}px, {position.y}px")

    def _save_position(self):
        if self.preview_widget.scene.subtitle_box:
            position = self.preview_widget.scene.subtitle_box.get_position()
            self.project.position = position
            self._update_position_spins(position)

    def _update_time_display(self, position_ms):
        seconds = position_ms / 1000
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{secs:02d}")
        self.preview_widget.update_time(seconds)
        self.current_time = seconds

    def _update_playback(self):
        if self.media_player.duration() > 0:
            self.media_player.setPosition(self.media_player.position() + 33)

    def _play_video(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            return
        if not self.current_video_path:
            self._load_video()
        if self.current_video_path:
            self.media_player.play()
            self.preview_widget.set_playing(True)

    def _pause_video(self):
        self.media_player.pause()
        self.preview_widget.set_playing(False)

    def _stop_video(self):
        self.media_player.stop()
        self.preview_widget.set_playing(False)

    def _load_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov *.mkv)")
        if file_path:
            self.current_video_path = file_path
            self.project.video_path = file_path
            self.media_player.setSource(file_path)
            self.process_button.setEnabled(True)
            self._load_first_frame()

    def _load_first_frame(self):
        try:
            from moviepy import VideoFileClip
            video = VideoFileClip(self.current_video_path)
            first_frame = video.get_frame(0)
            height, width, _ = first_frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(first_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            self.preview_widget.set_video_frame(pixmap)
            video.close()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load first frame: {str(e)}")

    def _generate_subtitles(self):
        vosk_model_path = self.model_combo.currentText()
        if not os.path.exists(vosk_model_path):
            common_paths = [os.path.join(os.path.expanduser("~"), "vosk-models", vosk_model_path), os.path.join("models", vosk_model_path)]
            for path in common_paths:
                if os.path.exists(path):
                    vosk_model_path = path
                    break
            else:
                QMessageBox.warning(self, "Model Not Found", f"Vosk model not found. Download from:
https://alphacephei.com/vosk/models")
                return
        self.processing_label.setVisible(True)
        self.process_button.setEnabled(False)
        self.processing_thread = ProcessingThread(self.current_video_path, vosk_model_path)
        self.processing_thread.processing_complete.connect(self._on_processing_complete)
        self.processing_thread.error_occurred.connect(self._on_processing_error)
        self.processing_thread.start()

    def _on_processing_complete(self, project: VideoProject):
        self.project = project
        self.processing_label.setVisible(False)
        self.process_button.setEnabled(True)
        self.export_button.setEnabled(True)
        self._update_style()
        self.preview_widget.set_project(self.project)
        self._update_position_spins(self.project.position)
        QMessageBox.information(self, "Success", "Subtitles generated successfully!")

    def _on_processing_error(self, error: str):
        self.processing_label.setVisible(False)
        self.process_button.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Processing failed: {error}")

    def _export_video(self):
        if not self.project:
            QMessageBox.warning(self, "Error", "No project to export. Generate subtitles first.")
            return
        output_path, _ = QFileDialog.getSaveFileName(self, "Save Video", "", "MP4 Files (*.mp4);;All Files (*)")
        if not output_path:
            return
        if not output_path.lower().endswith('.mp4'):
            output_path += '.mp4'
        self.export_label.setVisible(True)
        self.export_button.setEnabled(False)
        self.export_thread = ExportThread(self.project, output_path)
        self.export_thread.export_complete.connect(self._on_export_complete)
        self.export_thread.error_occurred.connect(self._on_export_error)
        self.export_thread.start()

    def _on_export_complete(self, output_path: str):
        self.export_label.setVisible(False)
        self.export_button.setEnabled(True)
        QMessageBox.information(self, "Success", f"Video exported successfully to:
{output_path}")

    def _on_export_error(self, error: str):
        self.export_label.setVisible(False)
        self.export_button.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Export failed: {error}")

    def closeEvent(self, event):
        self._stop_video()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()