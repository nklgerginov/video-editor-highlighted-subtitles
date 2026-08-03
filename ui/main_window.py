"""
Main application window for the video editor.
"""

import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton,
    QFileDialog, QProgressBar, QComboBox, QGroupBox, QScrollArea,
    QFrame, QSpinBox, QDoubleSpinBox, QFormLayout, QColorDialog
)
from PyQt6.QtCore import Qt, QTimer, QUrl, QSize
from PyQt6.QtGui import QPixmap, QIcon, QFont, QPalette, QColor, QFontDatabase
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget


class VideoEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Editor - Highlighted Subtitles")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)
        
        self.available_fonts = [f.family() for f in QFontDatabase.families() if f != '']
        
        self.video_path = None
        self.subtitle_lines = []
        self.processor = None
        self.exporter = None
        self.model_path = None
        
        self.subtitle_style = {
            'font': 'Arial', 'fontsize': 40, 'color': 'white',
            'highlight_color': 'yellow', 'stroke_color': 'black',
            'stroke_width': 2, 'highlight_scale': 1.2
        }
        
        self.init_ui()
        
        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.positionChanged.connect(self.on_media_position_changed)
    
    def init_ui(self):
        main_widget = QWidget(self)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        self.setCentralWidget(main_widget)
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        video_group = QGroupBox("Video Preview")
        video_layout = QVBoxLayout()
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(640, 360)
        self.video_widget.setStyleSheet("background-color: #000;")
        video_layout.addWidget(self.video_widget)
        controls_layout = QHBoxLayout()
        self.btn_open_video = QPushButton("Open Video")
        self.btn_open_video.clicked.connect(self.open_video)
        controls_layout.addWidget(self.btn_open_video)
        self.btn_play = QPushButton("Play")
        self.btn_play.clicked.connect(self.play_video)
        self.btn_play.setEnabled(False)
        controls_layout.addWidget(self.btn_play)
        self.btn_pause = QPushButton("Pause")
        self.btn_pause.clicked.connect(self.pause_video)
        self.btn_pause.setEnabled(False)
        controls_layout.addWidget(self.btn_pause)
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self.stop_video)
        self.btn_stop.setEnabled(False)
        controls_layout.addWidget(self.btn_stop)
        video_layout.addLayout(controls_layout)
        video_group.setLayout(video_layout)
        left_panel.addWidget(video_group)
        from ui.preview import SubtitlePreviewWidget
        self.subtitle_preview = SubtitlePreviewWidget([])
        left_panel.addWidget(self.subtitle_preview)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        left_panel.addWidget(self.progress_bar)
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)
        model_group = QGroupBox("Vosk Model")
        model_layout = QVBoxLayout()
        self.btn_select_model = QPushButton("Select Vosk Model")
        self.btn_select_model.clicked.connect(self.select_model)
        model_layout.addWidget(self.btn_select_model)
        self.lbl_model = QLabel("No model selected")
        self.lbl_model.setWordWrap(True)
        model_layout.addWidget(self.lbl_model)
        model_group.setLayout(model_layout)
        right_panel.addWidget(model_group)
        process_group = QGroupBox("Processing")
        process_layout = QVBoxLayout()
        self.btn_generate = QPushButton("Generate Subtitles")
        self.btn_generate.clicked.connect(self.generate_subtitles)
        self.btn_generate.setEnabled(False)
        process_layout.addWidget(self.btn_generate)
        self.progress_processing = QProgressBar()
        self.progress_processing.setTextVisible(True)
        self.progress_processing.setFormat("Processing: %p%")
        process_layout.addWidget(self.progress_processing)
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setWordWrap(True)
        process_layout.addWidget(self.lbl_status)
        process_group.setLayout(process_layout)
        right_panel.addWidget(process_group)
        style_group = QGroupBox("Subtitle Style")
        style_form = QFormLayout()
        self.cmb_font = QComboBox()
        self.cmb_font.addItems(self.available_fonts)
        self.cmb_font.setCurrentText(self.subtitle_style['font'])
        self.cmb_font.currentTextChanged.connect(self.update_style)
        style_form.addRow("Font:", self.cmb_font)
        self.spin_fontsize = QSpinBox()
        self.spin_fontsize.setRange(10, 100)
        self.spin_fontsize.setValue(self.subtitle_style['fontsize'])
        self.spin_fontsize.valueChanged.connect(self.update_style)
        style_form.addRow("Font Size:", self.spin_fontsize)
        self.spin_highlight_scale = QDoubleSpinBox()
        self.spin_highlight_scale.setRange(1.0, 2.0)
        self.spin_highlight_scale.setSingleStep(0.1)
        self.spin_highlight_scale.setValue(self.subtitle_style['highlight_scale'])
        self.spin_highlight_scale.valueChanged.connect(self.update_style)
        style_form.addRow("Highlight Scale:", self.spin_highlight_scale)
        self.btn_color = QPushButton("Choose Text Color")
        self.btn_color.clicked.connect(self.choose_text_color)
        style_form.addRow("Text Color:", self.btn_color)
        self.btn_highlight_color = QPushButton("Choose Highlight Color")
        self.btn_highlight_color.clicked.connect(self.choose_highlight_color)
        style_form.addRow("Highlight Color:", self.btn_highlight_color)
        style_group.setLayout(style_form)
        right_panel.addWidget(style_group)
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout()
        self.btn_export = QPushButton("Export Video with Subtitles")
        self.btn_export.clicked.connect(self.export_video)
        self.btn_export.setEnabled(False)
        export_layout.addWidget(self.btn_export)
        self.progress_export = QProgressBar()
        self.progress_export.setTextVisible(True)
        self.progress_export.setFormat("Exporting: %p%")
        export_layout.addWidget(self.progress_export)
        export_group.setLayout(export_layout)
        right_panel.addWidget(export_group)
        main_layout.addLayout(left_panel, 60)
        main_layout.addLayout(right_panel, 40)
        self.setStyleSheet(self._get_stylesheet())
        self.media_player.durationChanged.connect(self.on_duration_changed)
    
    def _get_stylesheet(self):
        return "QMainWindow { background-color: #2b2b2b; } QWidget { background-color: #2b2b2b; color: #ffffff; } QGroupBox { border: 1px solid #444; border-radius: 5px; margin-top: 10px; padding: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #aaa; } QLabel { color: #ccc; } QPushButton { background-color: #444; color: #fff; border: none; padding: 8px 16px; border-radius: 4px; min-width: 120px; } QPushButton:hover { background-color: #555; } QPushButton:disabled { background-color: #333; color: #666; } QProgressBar { border: 1px solid #444; border-radius: 4px; text-align: center; background-color: #333; color: #fff; } QProgressBar::chunk { background-color: #0078d7; border-radius: 3px; } QComboBox { background-color: #333; color: #fff; border: 1px solid #444; border-radius: 4px; padding: 5px; } QComboBox::drop-down { border: none; } QSpinBox, QDoubleSpinBox { background-color: #333; color: #fff; border: 1px solid #444; border-radius: 4px; padding: 5px; }"
    
    def update_style(self):
        self.subtitle_style['font'] = self.cmb_font.currentText()
        self.subtitle_style['fontsize'] = self.spin_fontsize.value()
        self.subtitle_style['highlight_scale'] = self.spin_highlight_scale.value()
    
    def choose_text_color(self):
        color = QColorDialog.getColor(QColor(self.subtitle_style.get('color', 'white')), self, "Choose Text Color")
        if color.isValid():
            self.subtitle_style['color'] = color.name()
    
    def choose_highlight_color(self):
        color = QColorDialog.getColor(QColor(self.subtitle_style.get('highlight_color', 'yellow')), self, "Choose Highlight Color")
        if color.isValid():
            self.subtitle_style['highlight_color'] = color.name()
    
    def open_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov *.mkv *.flv);;All Files (*)")
        if file_path:
            self.video_path = file_path
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.video_widget.setVisible(True)
            self.btn_play.setEnabled(True)
            self.btn_pause.setEnabled(True)
            self.btn_stop.setEnabled(True)
            self.btn_generate.setEnabled(True)
            self.lbl_status.setText(f"Video loaded: {os.path.basename(file_path)}")
    
    def play_video(self):
        if self.video_path:
            self.media_player.play()
            self.subtitle_preview.start()
    
    def pause_video(self):
        if self.video_path:
            self.media_player.pause()
    
    def stop_video(self):
        if self.video_path:
            self.media_player.stop()
            self.subtitle_preview.stop()
            self.subtitle_preview.set_time(0)
    
    def on_duration_changed(self, duration):
        self.progress_bar.setRange(0, duration)
    
    def on_media_position_changed(self, position):
        self.progress_bar.setValue(position)
        self.subtitle_preview.set_time(position / 1000)
    
    def select_model(self):
        model_dir = QFileDialog.getExistingDirectory(self, "Select Vosk Model Directory", "")
        if model_dir:
            self.model_path = model_dir
            self.lbl_model.setText(f"Model: {os.path.basename(model_dir)}")
            self.lbl_status.setText("Vosk model selected")
    
    def generate_subtitles(self):
        if not self.video_path:
            self.lbl_status.setText("Error: No video loaded")
            return
        if not self.model_path:
            self.lbl_status.setText("Error: No Vosk model selected")
            return
        self.btn_generate.setEnabled(False)
        self.btn_open_video.setEnabled(False)
        self.progress_processing.setValue(0)
        from processing import VideoProcessor
        self.processor = VideoProcessor(self.video_path, self.model_path)
        self.processor.progress.connect(self.progress_processing.setValue)
        self.processor.message.connect(self.lbl_status.setText)
        self.processor.processing_complete.connect(self.on_subtitles_generated)
        self.processor.error_occurred.connect(self.on_processing_error)
        self.processor.start()
    
    def on_subtitles_generated(self, subtitle_lines):
        self.subtitle_lines = subtitle_lines
        self.subtitle_preview.set_subtitle_lines(subtitle_lines)
        self.lbl_status.setText(f"Generated {len(subtitle_lines)} subtitle lines")
        self.btn_export.setEnabled(True)
        self.btn_generate.setEnabled(True)
        self.btn_open_video.setEnabled(True)
    
    def on_processing_error(self, error):
        self.lbl_status.setText(f"Error: {error}")
        self.btn_generate.setEnabled(True)
        self.btn_open_video.setEnabled(True)
    
    def export_video(self):
        if not self.video_path:
            self.lbl_status.setText("Error: No video loaded")
            return
        if not self.subtitle_lines:
            self.lbl_status.setText("Error: No subtitles generated")
            return
        output_path, _ = QFileDialog.getSaveFileName(self, "Save Video", "", "MP4 Files (*.mp4);;All Files (*)")
        if not output_path:
            return
        if not output_path.lower().endswith('.mp4'):
            output_path += '.mp4'
        self.btn_export.setEnabled(False)
        self.btn_generate.setEnabled(False)
        self.btn_open_video.setEnabled(False)
        self.progress_export.setValue(0)
        from export import VideoExporter
        self.exporter = VideoExporter(self.video_path, self.subtitle_lines, output_path, self.subtitle_style)
        self.exporter.progress.connect(self.progress_export.setValue)
        self.exporter.message.connect(self.lbl_status.setText)
        self.exporter.export_complete.connect(self.on_export_complete)
        self.exporter.error_occurred.connect(self.on_export_error)
        self.exporter.start()
    
    def on_export_complete(self, output_path):
        self.lbl_status.setText(f"Export complete: {os.path.basename(output_path)}")
        self.btn_export.setEnabled(True)
        self.btn_generate.setEnabled(True)
        self.btn_open_video.setEnabled(True)
    
    def on_export_error(self, error):
        self.lbl_status.setText(f"Export error: {error}")
        self.btn_export.setEnabled(True)
        self.btn_generate.setEnabled(True)
        self.btn_open_video.setEnabled(True)
    
    def closeEvent(self, event):
        if self.processor and self.processor.isRunning():
            self.processor.stop()
            self.processor.wait()
        if self.exporter and self.exporter.isRunning():
            self.exporter.stop()
            self.exporter.wait()
        self.media_player.stop()
        self.subtitle_preview.stop()
        event.accept()