import os
import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout,
    QMessageBox, QFileDialog, QColorDialog, QApplication, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QImage, QFontDatabase, QFont, QColor, QPalette
from PyQt6.QtCore import Qt, QTimer, QSize, QUrl, pyqtSignal, QThread, QObject
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


class VideoFrameGrabber(QObject):
    frame_available = pyqtSignal(QPixmap)

    def __init__(self, video_widget):
        super().__init__()
        self.video_widget = video_widget
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.grab_frame)

    def start(self, interval=33):
        self.timer.start(interval)

    def stop(self):
        self.timer.stop()

    def grab_frame(self):
        if self.video_widget:
            pixmap = self.video_widget.grab()
            self.frame_available.emit(pixmap)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._setup_dark_theme()
        self.setWindowTitle("Video Editor - Highlighted Subtitles")
        self.setMinimumSize(1200, 800)
        self.project = VideoProject()
        self.current_video_path = ""
        self.current_time = 0.0
        self._setup_ui()
        self._setup_connections()
        self._load_fonts()
        self._setup_media_player()

    def _setup_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        dark_palette.setColor(QPalette.ColorRole.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
        dark_palette.setColor(QPalette.ColorRole.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
        QApplication.setPalette(dark_palette)
        QApplication.setStyle("Fusion")

    def _setup_ui(self):
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Left panel - Video Preview
        left_panel = QVBoxLayout()
        left_panel.setSpacing(15)

        preview_group = QGroupBox("Video Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_widget = VideoPreviewWidget()
        self.preview_widget.setMinimumSize(800, 450)
        self.preview_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        preview_layout.addWidget(self.preview_widget)
        preview_group.setLayout(preview_layout)
        left_panel.addWidget(preview_group, stretch=1)

        # Video Controls
        controls_group = QGroupBox("Video Controls")
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        self.upload_button = QPushButton("Upload Video")
        self.upload_button.setStyleSheet("QPushButton { background-color: #2a82da; color: white; padding: 8px 16px; border-radius: 4px; } QPushButton:hover { background-color: #359aea; }")
        self.play_button = QPushButton("Play")
        self.play_button.setStyleSheet("QPushButton { background-color: #2ecc71; color: white; padding: 8px 16px; border-radius: 4px; } QPushButton:hover { background-color: #37d477; }")
        self.pause_button = QPushButton("Pause")
        self.pause_button.setStyleSheet("QPushButton { background-color: #f39c12; color: white; padding: 8px 16px; border-radius: 4px; } QPushButton:hover { background-color: #f5ab35; }")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; padding: 8px 16px; border-radius: 4px; } QPushButton:hover { background-color: #ec7063; }")
        
        controls_layout.addWidget(self.upload_button)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addStretch()
        
        self.time_label = QLabel("00:00:00")
        self.time_label.setStyleSheet("color: #ecf0f1; font-size: 14px;")
        controls_layout.addWidget(self.time_label)
        controls_group.setLayout(controls_layout)
        left_panel.addWidget(controls_group)

        # Right panel - Settings
        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)

        # Vosk Model Section
        vosk_group = QGroupBox("Vosk Model")
        vosk_layout = QVBoxLayout()
        vosk_layout.setSpacing(10)
        
        self.model_combo = QComboBox()
        self._scan_models()
        self.model_combo.setEditable(True)
        self.model_combo.setStyleSheet("QComboBox { background-color: #34495e; color: #ecf0f1; border: 1px solid #2c3e50; padding: 6px; border-radius: 4px; } QComboBox QAbstractItemView { background-color: #34495e; color: #ecf0f1; }")
        
        model_label = QLabel("Select Vosk Model:")
        model_label.setStyleSheet("color: #ecf0f1;")
        vosk_layout.addWidget(model_label)
        vosk_layout.addWidget(self.model_combo)
        vosk_group.setLayout(vosk_layout)
        right_panel.addWidget(vosk_group)

        # Process Button
        self.process_button = QPushButton("Generate Subtitles")
        self.process_button.setStyleSheet("QPushButton { background-color: #9b59b6; color: white; padding: 10px; border-radius: 4px; font-size: 14px; } QPushButton:hover { background-color: #a569bd; } QPushButton:disabled { background-color: #7f8c8d; }")
        self.process_button.setEnabled(False)
        right_panel.addWidget(self.process_button)

        self.processing_label = QLabel("Processing...")
        self.processing_label.setStyleSheet("color: #f39c12;")
        self.processing_label.setVisible(False)
        right_panel.addWidget(self.processing_label)

        # Subtitle Style Section
        style_group = QGroupBox("Subtitle Style")
        style_layout = QFormLayout()
        style_layout.setSpacing(10)
        style_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.font_combo = QComboBox()
        self.font_combo.setStyleSheet("QComboBox { background-color: #34495e; color: #ecf0f1; border: 1px solid #2c3e50; padding: 6px; border-radius: 4px; }")
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setStyleSheet("QSpinBox { background-color: #34495e; color: #ecf0f1; border: 1px solid #2c3e50; padding: 6px; border-radius: 4px; }")
        self.highlight_scale_spin = QDoubleSpinBox()
        self.highlight_scale_spin.setStyleSheet("QDoubleSpinBox { background-color: #34495e; color: #ecf0f1; border: 1px solid #2c3e50; padding: 6px; border-radius: 4px; }")
        
        self.font_size_spin.setRange(10, 200)
        self.font_size_spin.setValue(40)
        self.highlight_scale_spin.setRange(1.0, 3.0)
        self.highlight_scale_spin.setValue(1.5)
        self.highlight_scale_spin.setSingleStep(0.1)
        
        style_layout.addRow("Font:", self.font_combo)
        style_layout.addRow("Font Size:", self.font_size_spin)
        style_layout.addRow("Highlight Scale:", self.highlight_scale_spin)
        
        self.text_color_button = QPushButton("Choose Text Color")
        self.text_color_button.setStyleSheet("QPushButton { background-color: #34495e; color: #ecf0f1; padding: 6px; border-radius: 4px; border: 1px solid #2c3e50; }")
        self.text_color = QColor(255, 255, 255)
        self._update_color_button(self.text_color_button, self.text_color)
        style_layout.addRow("Text Color:", self.text_color_button)
        
        self.highlight_color_button = QPushButton("Choose Highlight Color")
        self.highlight_color_button.setStyleSheet("QPushButton { background-color: #34495e; color: #ecf0f1; padding: 6px; border-radius: 4px; border: 1px solid #2c3e50; }")
        self.highlight_color = QColor(255, 255, 0)
        self._update_color_button(self.highlight_color_button, self.highlight_color)
        style_layout.addRow("Highlight Color:", self.highlight_color_button)
        
        style_group.setLayout(style_layout)
        right_panel.addWidget(style_group)

        # Subtitle Position Section
        position_group = QGroupBox("Subtitle Position")
        position_layout = QVBoxLayout()
        position_layout.setSpacing(10)
        
        position_info = QLabel("Drag the subtitle box in the preview")
        position_info.setStyleSheet("color: #bdc3c7;")
        position_layout.addWidget(position_info)
        
        self.save_position_button = QPushButton("Save Position")
        self.save_position_button.setStyleSheet("QPushButton { background-color: #3498db; color: white; padding: 6px; border-radius: 4px; }")
        position_layout.addWidget(self.save_position_button)
        
        self.position_label = QLabel("Position: 50px, 50px")
        self.position_label.setStyleSheet("color: #ecf0f1;")
        position_layout.addWidget(self.position_label)

        position_form = QFormLayout()
        position_form.setSpacing(8)
        
        self.x_spin = QSpinBox()
        self.y_spin = QSpinBox()
        self.width_spin = QSpinBox()
        self.height_spin = QSpinBox()
        
        for spin in [self.x_spin, self.y_spin, self.width_spin, self.height_spin]:
            spin.setStyleSheet("QSpinBox { background-color: #34495e; color: #ecf0f1; border: 1px solid #2c3e50; padding: 4px; border-radius: 4px; }")
        
        self.x_spin.setRange(0, 2000)
        self.x_spin.setValue(50)
        position_form.addRow("X (px):", self.x_spin)
        
        self.y_spin.setRange(0, 2000)
        self.y_spin.setValue(50)
        position_form.addRow("Y (px):", self.y_spin)
        
        self.width_spin.setRange(100, 2000)
        self.width_spin.setValue(800)
        position_form.addRow("Width (px):", self.width_spin)
        
        self.height_spin.setRange(50, 1000)
        self.height_spin.setValue(200)
        position_form.addRow("Height (px):", self.height_spin)
        
        position_layout.addLayout(position_form)
        position_group.setLayout(position_layout)
        right_panel.addWidget(position_group)

        # Export Section
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout()
        export_layout.setSpacing(10)
        
        self.export_button = QPushButton("Export Video")
        self.export_button.setStyleSheet("QPushButton { background-color: #e67e22; color: white; padding: 10px; border-radius: 4px; font-size: 14px; } QPushButton:hover { background-color: #e88a32; } QPushButton:disabled { background-color: #7f8c8d; }")
        self.export_button.setEnabled(False)
        export_layout.addWidget(self.export_button)
        
        self.export_label = QLabel("Exporting...")
        self.export_label.setStyleSheet("color: #f39c12;")
        self.export_label.setVisible(False)
        export_layout.addWidget(self.export_label)
        
        export_group.setLayout(export_layout)
        right_panel.addWidget(export_group)
        right_panel.addStretch()

        main_layout.addLayout(left_panel, stretch=2)
        main_layout.addLayout(right_panel, stretch=1)

    def _scan_models(self):
        models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
        if os.path.exists(models_dir):
            for item in os.listdir(models_dir):
                if os.path.isdir(os.path.join(models_dir, item)):
                    self.model_combo.addItem(os.path.join("models", item))
        self.model_combo.addItem("vosk-model-en-us-0.22-lgraph")
        self.model_combo.addItem("vosk-model-small-en-us-0.15")

    def _setup_connections(self):
        self.upload_button.clicked.connect(self._load_video)
        self.play_button.clicked.connect(self._play)
        self.pause_button.clicked.connect(self._pause)
        self.stop_button.clicked.connect(self._stop)
        self.process_button.clicked.connect(self._gen_subs)
        self.font_combo.currentTextChanged.connect(self._update_style)
        self.font_size_spin.valueChanged.connect(self._update_style)
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
        
        self.video_sink.hide()
        
        self.frame_grabber = VideoFrameGrabber(self.video_sink)
        self.frame_grabber.frame_available.connect(self._update_preview_frame)

    def _load_fonts(self):
        families = QFontDatabase.families()
        self.font_combo.clear()
        self.font_combo.addItems(families)
        for f in ["Arial", "Helvetica", "Roboto", "Segoe UI"]:
            if f in families:
                self.font_combo.setCurrentText(f)
                break

    def _update_color_button(self, button, color):
        button.setStyleSheet(f"QPushButton {{ background-color: {color.name()}; color: {'black' if color.lightness() > 128 else 'white'}; padding: 6px; border-radius: 4px; border: 1px solid #2c3e50; }}")

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
        self.current_time = secs
        self.preview_widget.update_time(secs)
        self.time_label.setText(self._format_time(secs))

    def _format_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _update_preview_frame(self, pixmap):
        self.preview_widget.set_video_frame(pixmap)

    def _play(self):
        if not self.current_video_path:
            QMessageBox.warning(self, "No Video", "Please upload a video first")
            return
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            return
        self.media_player.play()
        self.frame_grabber.start()
        self.preview_widget.set_playing(True)

    def _pause(self):
        self.media_player.pause()
        self.frame_grabber.stop()
        self.preview_widget.set_playing(False)

    def _stop(self):
        self.media_player.stop()
        self.frame_grabber.stop()
        self.preview_widget.set_playing(False)
        self._update_time(0)

    def _load_video(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Open Video", "", "Video Files (*.mp4 *.avi *.mov *.mkv)")
        if fp:
            self.current_video_path = fp
            self.project.video_path = fp
            self.media_player.setSource(QUrl.fromLocalFile(fp))
            self.process_button.setEnabled(True)
            self.export_button.setEnabled(False)
            self._update_time(0)
            QMessageBox.information(self, "Video Loaded", f"Video loaded: {os.path.basename(fp)}")

    def _gen_subs(self):
        model_path = self.model_combo.currentText()
        
        if not os.path.exists(model_path):
            models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
            try_model = os.path.join(models_dir, model_path)
            if os.path.exists(try_model):
                model_path = try_model
            else:
                for prefix in ["models/", "", "vosk-models/"]:
                    try_path = os.path.join(models_dir, prefix, model_path)
                    if os.path.exists(try_path):
                        model_path = try_path
                        break
        
        if not os.path.exists(model_path):
            QMessageBox.warning(
                self, "Model Not Found", 
                f"Vosk model not found at: {model_path}

"
                "Download models from: https://alphacephei.com/vosk/models
"
                "and place them in the 'models' folder"
            )
            return
        
        self.processing_label.setVisible(True)
        self.process_button.setEnabled(False)
        self.thread = ProcessingThread(self.current_video_path, model_path)
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
        QMessageBox.critical(self, "Error", f"Failed to generate subtitles:
{error}")

    def _export(self):
        default_name = os.path.splitext(os.path.basename(self.current_video_path))[0] + "_subtitled.mp4"
        op, _ = QFileDialog.getSaveFileName(
            self, "Save Video", default_name, "MP4 Files (*.mp4)"
        )
        if not op:
            return
        self.export_label.setVisible(True)
        self.export_button.setEnabled(False)
        self.exp_thread = ExportThread(self.project, op)
        self.exp_thread.export_complete.connect(self._on_exp_done)
        self.exp_thread.error_occurred.connect(self._on_exp_err)
        self.exp_thread.start()

    def _on_exp_done(self, path):
        self.export_label.setVisible(False)
        self.export_button.setEnabled(True)
        QMessageBox.information(self, "Success", f"Video exported to:
{path}")

    def _on_exp_err(self, error):
        self.export_label.setVisible(False)
        self.export_button.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Export failed:
{error}")

    def closeEvent(self, event):
        self._stop()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()