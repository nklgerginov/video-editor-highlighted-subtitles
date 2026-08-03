import os
import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout,
    QMessageBox, QFileDialog, QColorDialog, QApplication, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QImage, QFontDatabase, QFont, QColor
from PyQt6.QtCore import Qt, QTimer, QSize, QUrl, pyqtSignal, QThread
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
        self.setWindowTitle("Video Editor - Highlighted Subtitles"
)
        self.setMinimumSize(1200, 800)
        self.project = VideoProject()self.current_video_path = ""
        self.current_time = 0.0
        self._setup_ui()
        self._setup_connections()
        self._load_fonts()
        self._setup_media_player()

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
        self.font_combo.clear()
        self.font_combo.addItems(QFontDatabase.families())
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

        position_group = QGroupBox("Subtitle Position")
        position_layout = QVBoxLayout()
        position_layout.addWidget(QLabel("Drag the subtitle box in the preview"))
        self.save_position_button = QPushButton("Save Position")
        position_layout.
addWidget(self.save_position_button)
        self.position_label = QLabel("Position: 50px, 50px")
   
     position_layout.addWidget(self.position_label)

        position_form = QFormLayout()
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 2000)
        self.x_spin.setValue(50)
        position_form.addRow("X (px):", self.x_spin)
        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 2000)
        self.y_spin.setValue(50)
        position_form.addRow("Y (px):", self.y_spin)
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
        self.export_button = QPushButton("Export Video")
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
        self.play_button.clicked.connect(self._play)
        self.pause_button.clicked.connect(self._pause)
        self.stop_button.clicked.connect(self._stop)
        self.process_button.clicked.connect(self._gen_subs)
        self.font_combo.currentTextChanged.connect(self._update_style)
        self.font_size_spin.valueChanged.conn
ect(self._update_style)
        self.highlight_scale_spin.valueChanged.connect(self._update_style)
 
       self.text_color_button.clicked.connect(self._choose_text_color)
        self.highlight_color_button.clicked.connect(self._choose_highlight_color)
        self.save_position_button.clicked.connect(self._save_pos)
        self.x_spin.valueChanged.connect(self._update_pos)
        self.y_spin.valueChanged.connect(self._update_pos)
        self.width_spin.valueChanged.connect(self._update_pos)
        self.height_spin.valueChanged.connect(self._update_pos)
        self.preview_widget.position_changed.connect(self._update_pos_spins)
        self.export_button.clicked.connect(self._export)

    def _setup_media_player(self):
        self.media_player = QMediaPlayer(self)
        self.audio_out = QAudioOutput(self)
        self.media_player.setAudioOutput(self.audio_out)
        self.video_sink = QVideoWidget(self)
        self.media_player.setVideoOutput(self.video_sink)
        self.media_player.positionChanged.connect(self._update_time)

    def _load_fonts(self):
        families = QFontDatabase.families()
        self.font_combo.clear()
        self.font_combo.addItems(families)
        for f in ["Arial", "Helvetica"]:
            if f in families:
                self.font_combo.setCurrentText(f)
                break

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
        color = QC
olorDialog.getColor(self.text_color, self, "Choose Text Color")
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

    def _update_pos_spins(self, pos):
        self.x_spin.setValue(pos.x)
        self.y_spin.setValue(pos.y)
        self.width_spin.setValue(pos.width)
        self.height_spin.setValue(pos.height)
        self.position_label.setText(f"Position: {pos.x}px, {pos.y}px")

    def _update_pos(self):
        if not self.project:
            return
        pos = SubtitlePosition(self.x_spin.value(), self.y_spin.value(), self.width_spin.value(), self.height_spin.value())
        self.project.position = pos
        if self.preview_widget.scene.subtitle_box:
            self.preview_widget.scene.subtitle_box.setRect(0, 0, pos.width, pos.height)
            self.preview_widget.scene.subtitle_box.setPos(pos.x, pos.y)
            self.preview_widget.scene.subtitle_box.update_resize_handles()

    def _save_pos(self):
        if self.preview_widget.scene.subtitle_box:
            pos = self.preview_widget.scene.subtitle_box.get_position()
            self.project.position = pos
            self._update_pos_spins(pos)

    def _update_time(self, pos_ms):
        secs = pos_ms / 1000
        self.preview_widget.update_time(secs)

    def _play(self):
        if not self.current_video_path:
            self._load_video()
            return
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            return
        
self.media_player.play()

    def _pause(self):
        self.media_player.pause()

    def _stop(s
elf):
        self.media_player.stop()

    def _load_video(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Open Video", "", "Video (*.mp4 *.avi *.mov)")
        if fp:
            self.current_video_path = fp
            self.project.video_path = fp
            self.media_player.setSource(QUrl.fromLocalFile(fp))
            self.process_button.setEnabled(True)

    def _gen_subs(self):
        vmp = self.model_combo.currentText()
        if not os.path.exists(vmp):
            QMessageBox.warning(self, "Model Not Found", "Vosk model not found. Download from: https://alphacephei.com/vosk/models")
            return
        self.processing_label.setVisible(True)
        self.process_button.setEnabled(False)
        self.thread = ProcessingThread(self.current_video_path, vmp)
        self.thread.processing_complete.connect(self._on_proc_done)
        self.thread.error_occurred.connect(self._on_proc_err)
        self.thread.start()

    def _on_proc_done(self, project):
        self.project = project
        self.processing_label.setVisible(False)
        self.process_button.setEnabled(True)
        self.export_button.setEnabled(True)
        self._update_style()
        self.preview_widget.set_project(self.project)
        self._update_pos_spins(self.project.position)
        QMessageBox.information(self, "Success", "Subtitles generated successfully!")

    def _on_proc_err(self, error):
        self.processing_label.setVisible(False)
        self.process_button.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Failed: {error}")

    def _export(self):
        op, _ = QFileDialog.getSaveFileName(self, "Save", "", "MP4 (*.mp4)")
        if not op:
            return
        self.export_label.setVisible(True)
        self.export_button.setEnabled(False)
        self.exp_thread = ExportThread(self.project, op)
        self.exp_thread.export_complete.connect(self._on_exp_d
one)
        self.exp_thread.error_occurred.connect(self._on_exp_err)
       
 self.exp_thread.start()

    def _on_exp_done(self, path):
        self.export_label.setVisible(False)
        self.export_button.setEnabled(True)
        QMessageBox.information(self, "Success", f"Exported to {path}")

    def _on_exp_err(self, error):
        self.export_label.setVisible(False)
        self.export_button.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Failed: {error}")

    def closeEvent(self, event):
        self._stop()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()