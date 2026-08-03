import os, sys
from typing import Optional
<<<<<<< HEAD
<<<<<<< HEAD
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QFileDialog,
    QColorDialog,
    QApplication,
)
=======
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout, QMessageBox, QFileDialog, QColorDialog, QApplication)
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
=======
from PyQt6.QtWidgets import *
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c
from PyQt6.QtGui import QPixmap, QImage, QFontDatabase, QFont, QColor
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal, QThread
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from models import VideoProject, SubtitleStyle, SubtitlePosition
from processing import SubtitleGenerator
from export import VideoExporter
from .preview import VideoPreviewWidget

from models import VideoProject, SubtitleStyle, SubtitlePosition
from processing import SubtitleGenerator
from export import VideoExporter
from .preview import VideoPreviewWidget

<<<<<<< HEAD

class ProcessingThread(QThread):
    processing_complete = pyqtSignal(VideoProject)
    error_occurred = pyqtSignal(str)
<<<<<<< HEAD

=======
class ProcessingThread(QThread):
    processing_complete = pyqtSignal(VideoProject)
    error_occurred = pyqtSignal(str)
    
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
=======
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c
    def __init__(self, video_path: str, vosk_model_path: str):
        super().__init__()
        self.video_path = video_path
        self.vosk_model_path = vosk_model_path
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
=======
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c
    def run(self):
        try:
            gen = SubtitleGenerator(self.vosk_model_path)
            proj = gen.process_video(self.video_path, self.vosk_model_path)
            self.processing_complete.emit(proj)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ExportThread(QThread):
    export_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
=======
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c
    def __init__(self, project: VideoProject, output_path: str):
        super().__init__()
        self.project = project
        self.output_path = output_path
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
=======
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c
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
        self.setMinimumSize(1000, 700)
        self.project = VideoProject()
        self.current_video_path = ""
        self._setup_ui()
        self._setup_connections()
        self._load_fonts()
        self._setup_media_player()

    def _setup_ui(self):
<<<<<<< HEAD
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
<<<<<<< HEAD

        # Left panel - Preview
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)

        self.preview_widget = VideoPreviewWidget()
        self.preview_widget.setMinimumSize(800, 450)
        left_panel.addWidget(self.preview_widget, stretch=1)

=======
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        self.preview_widget = VideoPreviewWidget()
        self.preview_widget.setMinimumSize(800, 450)
        left_panel.addWidget(self.preview_widget, stretch=1)
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
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
<<<<<<< HEAD

        # Right panel - Settings
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)

        # Vosk Model
=======
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
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
<<<<<<< HEAD

        self.process_button = QPushButton("Generate Subtitles")
        self.process_button.setEnabled(False)
        right_panel.addWidget(self.process_button)

        self.processing_label = QLabel("Processing...")
        self.processing_label.setVisible(False)
        right_panel.addWidget(self.processing_label)

        # Style
=======
        self.process_button = QPushButton("Generate Subtitles")
        self.process_button.setEnabled(False)
        right_panel.addWidget(self.process_button)
        self.processing_label = QLabel("Processing...")
        self.processing_label.setVisible(False)
        right_panel.addWidget(self.processing_label)
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
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
<<<<<<< HEAD

        # Position
        position_group = QGroupBox("Subtitle Position (Drag & Drop)")
        position_layout = QVBoxLayout()
        position_layout.addWidget(
            QLabel("Drag the subtitle box in the preview to position it")
        )
=======
        position_group = QGroupBox("Subtitle Position (Drag & Drop)")
        position_layout = QVBoxLayout()
        position_layout.addWidget(QLabel("Drag the subtitle box in the preview to position it"))
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
        self.save_position_button = QPushButton("Save Current Position")
        position_layout.addWidget(self.save_position_button)
        self.position_label = QLabel("Position: 50px, 50px")
        position_layout.addWidget(self.position_label)
<<<<<<< HEAD

=======
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
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
<<<<<<< HEAD

        # Export
=======
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
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
<<<<<<< HEAD

=======
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
        main_layout.addLayout(left_panel, stretch=2)
        main_layout.addLayout(right_panel, stretch=1)
=======
        mw = QWidget(self)
        self.setCentralWidget(mw)
        ml = QHBoxLayout(mw)
        ml.setContentsMargins(10, 10, 10, 10)
        lp = QVBoxLayout()
        self.preview = VideoPreviewWidget()
        lp.addWidget(self.preview, 1)
        cg = QGroupBox("Controls")
        cl = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.pause_btn = QPushButton("Pause")
        self.stop_btn = QPushButton("Stop")
        cl.addWidget(self.play_btn)
        cl.addWidget(self.pause_btn)
        cl.addWidget(self.stop_btn)
        cg.setLayout(cl)
        lp.addWidget(cg)
        rp = QVBoxLayout()
        vg = QGroupBox("Vosk Model")
        vl = QVBoxLayout()
        self.model_cb = QComboBox()
        self.model_cb.addItems(["vosk-model-en-us-0.22-lgraph", "vosk-model-small-en-us-0.15"])
        self.model_cb.setEditable(True)
        vl.addWidget(QLabel("Model:"))
        vl.addWidget(self.model_cb)
        vg.setLayout(vl)
        rp.addWidget(vg)
        self.proc_btn = QPushButton("Generate Subtitles")
        self.proc_btn.setEnabled(False)
        rp.addWidget(self.proc_btn)
        self.proc_lbl = QLabel("Processing...")
        self.proc_lbl.setVisible(False)
        rp.addWidget(self.proc_lbl)
        sg = QGroupBox("Style")
        sl = QFormLayout()
        self.font_cb = QComboBox()
        self._populate_font_combo()
        sl.addRow("Font:", self.font_cb)
        self.fsize_sp = QSpinBox()
        self.fsize_sp.setRange(10, 200)
        self.fsize_sp.setValue(40)
        sl.addRow("Size:", self.fsize_sp)
        self.hscale_sp = QDoubleSpinBox()
        self.hscale_sp.setRange(1.0, 3.0)
        self.hscale_sp.setValue(1.5)
        sl.addRow("Highlight Scale:", self.hscale_sp)
        sg.setLayout(sl)
        rp.addWidget(sg)
        pg = QGroupBox("Position (Drag Box)")
        pl = QVBoxLayout()
        pl.addWidget(QLabel("Drag subtitle box in preview"))
        self.save_pos_btn = QPushButton("Save Position")
        pl.addWidget(self.save_pos_btn)
        self.pos_lbl = QLabel("Position: 50px, 50px")
        pl.addWidget(self.pos_lbl)
        pf = QFormLayout()
        self.x_sp = QSpinBox()
        self.x_sp.setRange(0, 2000)
        self.x_sp.setValue(50)
        pf.addRow("X (px):", self.x_sp)
        self.y_sp = QSpinBox()
        self.y_sp.setRange(0, 2000)
        self.y_sp.setValue(50)
        pf.addRow("Y (px):", self.y_sp)
        self.w_sp = QSpinBox()
        self.w_sp.setRange(100, 2000)
        self.w_sp.setValue(800)
        pf.addRow("Width (px):", self.w_sp)
        self.h_sp = QSpinBox()
        self.h_sp.setRange(50, 1000)
        self.h_sp.setValue(200)
        pf.addRow("Height (px):", self.h_sp)
        pl.addLayout(pf)
        pg.setLayout(pl)
        rp.addWidget(pg)
        eg = QGroupBox("Export")
        el = QVBoxLayout()
        self.exp_btn = QPushButton("Export Video")
        self.exp_btn.setEnabled(False)
        el.addWidget(self.exp_btn)
        self.exp_lbl = QLabel("Exporting...")
        self.exp_lbl.setVisible(False)
        el.addWidget(self.exp_lbl)
        eg.setLayout(el)
        rp.addWidget(eg)
        rp.addStretch()
        ml.addLayout(lp, 2)
        ml.addLayout(rp, 1)
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c

    def _setup_connections(self):
        self.play_btn.clicked.connect(self._play)
        self.pause_btn.clicked.connect(self._pause)
        self.stop_btn.clicked.connect(self._stop)
        self.proc_btn.clicked.connect(self._gen_subs)
        self.font_cb.currentTextChanged.connect(self._update_style)
        self.fsize_sp.valueChanged.connect(self._update_style)
        self.hscale_sp.valueChanged.connect(self._update_style)
        self.save_pos_btn.clicked.connect(self._save_pos)
        self.x_sp.valueChanged.connect(self._update_pos)
        self.y_sp.valueChanged.connect(self._update_pos)
        self.w_sp.valueChanged.connect(self._update_pos)
        self.h_sp.valueChanged.connect(self._update_pos)
        self.preview.position_changed.connect(self._update_pos_spins)
        self.exp_btn.clicked.connect(self._export)

    def _setup_media_player(self):
        self.player = QMediaPlayer(self)
        self.audio_out = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_out)
        self.video_sink = QVideoWidget(self)
        self.player.setVideoOutput(self.video_sink)
        self.player.positionChanged.connect(self._update_time)

    def _load_fonts(self):
        font_db = QFontDatabase()
        families = font_db.families()
        self.font_combo.clear()
        self.font_combo.addItems(families)
        for font in ["Arial", "Helvetica"]:
            if font in families:
                self.font_combo.setCurrentText(font)
                break

    def _populate_font_combo(self):
<<<<<<< HEAD
        self.font_combo.clear()
        self.font_combo.addItems(QFontDatabase().families())

    def _update_color_button(self, button, color):
<<<<<<< HEAD
        button.setStyleSheet(
            f"background-color: {color.name()}; "
            f"color: {'black' if color.lightness() > 128 else 'white'};"
        )
=======
        button.setStyleSheet(f"background-color: {color.name()}; color: {'black' if color.lightness() > 128 else 'white'};")
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
=======
        self.font_cb.clear()
        self.font_cb.addItems(QFontDatabase().families())
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c

    def _update_style(self):
        if not self.project:
            self.project = VideoProject()
        self.project.style = SubtitleStyle(
<<<<<<< HEAD
            font_family=self.font_combo.currentText(),
            font_size=self.font_size_spin.value(),
            highlight_scale=self.highlight_scale_spin.value(),
            text_color=self.text_color.name(),
<<<<<<< HEAD
            highlight_color=self.highlight_color.name(),
=======
            highlight_color=self.highlight_color.name()
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
=======
            font_family=self.font_cb.currentText(),
            font_size=self.fsize_sp.value(),
            highlight_scale=self.hscale_sp.value(),
            text_color="#FFFFFF",
            highlight_color="#FFFF00"
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c
        )
        if self.preview.project:
            self.preview.set_project(self.project)

    def _update_pos_spins(self, pos: SubtitlePosition):
        self.x_sp.setValue(pos.x)
        self.y_sp.setValue(pos.y)
        self.w_sp.setValue(pos.width)
        self.h_sp.setValue(pos.height)
        self.pos_lbl.setText(f"Position: {pos.x}px, {pos.y}px")

<<<<<<< HEAD
    def _choose_highlight_color(self):
<<<<<<< HEAD
        color = QColorDialog.getColor(
            self.highlight_color, self, "Choose Highlight Color"
        )
=======
        color = QColorDialog.getColor(self.highlight_color, self, "Choose Highlight Color")
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
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
=======
    def _update_pos(self):
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c
        if not self.project:
            return
<<<<<<< HEAD
        position = SubtitlePosition(
            x=self.x_spin.value(),
            y=self.y_spin.value(),
            width=self.width_spin.value(),
            height=self.height_spin.value(),
        )
        self.project.position = position
        if self.preview_widget.scene.subtitle_box:
            self.preview_widget.scene.subtitle_box.setRect(
                0, 0, position.width, position.height
            )
=======
        position = SubtitlePosition(x=self.x_spin.value(), y=self.y_spin.value(), width=self.width_spin.value(), height=self.height_spin.value())
        self.project.position = position
        if self.preview_widget.scene.subtitle_box:
            self.preview_widget.scene.subtitle_box.setRect(0, 0, position.width, position.height)
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
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

    def _play_video(self):
        if not self.current_video_path:
            self._load_video()
            return
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            return
        self.media_player.play()
        self.preview_widget.set_playing(True)

    def _pause(self):
        self.player.pause()

    def _stop(self):
        self.player.stop()

    def _load_video(self):
<<<<<<< HEAD
<<<<<<< HEAD
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
=======
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov *.mkv)")
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
        if file_path:
            self.current_video_path = file_path
            self.project.video_path = file_path
            self.media_player.setSource(file_path)
            self.process_button.setEnabled(True)
            self._load_first_frame()

    def _load_first_frame(self):
        try:
            from moviepy import VideoFileClip
<<<<<<< HEAD

=======
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
            video = VideoFileClip(self.current_video_path)
            first_frame = video.get_frame(0)
            height, width, _ = first_frame.shape
            bytes_per_line = 3 * width
<<<<<<< HEAD
            q_image = QImage(
                first_frame.data,
                width,
                height,
                bytes_per_line,
                QImage.Format.Format_RGB888,
            )
=======
            q_image = QImage(first_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
            pixmap = QPixmap.fromImage(q_image)
            self.preview_widget.set_video_frame(pixmap)
            video.close()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load first frame: {str(e)}")

    def _generate_subtitles(self):
        vosk_model_path = self.model_combo.currentText()
        if not os.path.exists(vosk_model_path):
<<<<<<< HEAD
            common_paths = [
                os.path.join(os.path.expanduser("~"), "vosk-models", vosk_model_path),
                os.path.join("models", vosk_model_path),
            ]
            found = False
            for path in common_paths:
                if os.path.exists(path):
                    vosk_model_path = path
                    found = True
                    break
            if not found:
                QMessageBox.warning(
                    self,
                    "Model Not Found",
                    f"Vosk model not found. Download from:\nhttps://alphacephei.com/vosk/models",
                )
                return

        self.processing_label.setVisible(True)
        self.process_button.setEnabled(False)
        self.processing_thread = ProcessingThread(
            self.current_video_path, vosk_model_path
        )
=======
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
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
        self.processing_thread.processing_complete.connect(self._on_processing_complete)
        self.processing_thread.error_occurred.connect(self._on_processing_error)
        self.processing_thread.start()

    def _on_processing_complete(self, project: VideoProject):
=======
        fp, _ = QFileDialog.getOpenFileName(self, "Open Video", "", "Video (*.mp4 *.avi *.mov)")
        if fp:
            self.current_video_path = fp
            self.project.video_path = fp
            self.player.setSource(fp)
            self.proc_btn.setEnabled(True)

    def _gen_subs(self):
        vmp = self.model_cb.currentText()
        if not os.path.exists(vmp):
            QMessageBox.warning(self, "Error", "Vosk model not found")
            return
        self.proc_lbl.setVisible(True)
        self.proc_btn.setEnabled(False)
        self.thread = ProcessingThread(self.current_video_path, vmp)
        self.thread.processing_complete.connect(self._on_proc_done)
        self.thread.error_occurred.connect(self._on_proc_err)
        self.thread.start()

    def _on_proc_done(self, project: VideoProject):
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c
        self.project = project
        self.proc_lbl.setVisible(False)
        self.proc_btn.setEnabled(True)
        self.exp_btn.setEnabled(True)
        self._update_style()
        self.preview.set_project(self.project)
        self._update_pos_spins(self.project.position)

    def _on_proc_err(self, error: str):
        self.proc_lbl.setVisible(False)
        self.proc_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", error)

<<<<<<< HEAD
    def _export_video(self):
        if not self.project:
<<<<<<< HEAD
            QMessageBox.warning(
                self, "Error", "No project to export. Generate subtitles first."
            )
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Video", "", "MP4 Files (*.mp4);;All Files (*)"
        )
        if not output_path:
            return
        if not output_path.lower().endswith(".mp4"):
            output_path += ".mp4"

=======
            QMessageBox.warning(self, "Error", "No project to export. Generate subtitles first.")
            return
        output_path, _ = QFileDialog.getSaveFileName(self, "Save Video", "", "MP4 Files (*.mp4);;All Files (*)")
        if not output_path:
            return
        if not output_path.lower().endswith('.mp4'):
            output_path += '.mp4'
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
        self.export_label.setVisible(True)
        self.export_button.setEnabled(False)
        self.export_thread = ExportThread(self.project, output_path)
        self.export_thread.export_complete.connect(self._on_export_complete)
        self.export_thread.error_occurred.connect(self._on_export_error)
        self.export_thread.start()

    def _on_export_complete(self, output_path: str):
        self.export_label.setVisible(False)
        self.export_button.setEnabled(True)
<<<<<<< HEAD
        QMessageBox.information(
            self, "Success", f"Video exported successfully to:\n{output_path}"
        )
=======
        QMessageBox.information(self, "Success", f"Video exported successfully to:
{output_path}")
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
=======
    def _export(self):
        op, _ = QFileDialog.getSaveFileName(self, "Save", "", "MP4 (*.mp4)")
        if not op:
            return
        self.exp_lbl.setVisible(True)
        self.exp_btn.setEnabled(False)
        self.exp_thread = ExportThread(self.project, op)
        self.exp_thread.export_complete.connect(self._on_exp_done)
        self.exp_thread.error_occurred.connect(self._on_exp_err)
        self.exp_thread.start()

    def _on_exp_done(self, path: str):
        self.exp_lbl.setVisible(False)
        self.exp_btn.setEnabled(True)
        QMessageBox.information(self, "Success", f"Exported to {path}")
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c

    def _on_exp_err(self, error: str):
        self.exp_lbl.setVisible(False)
        self.exp_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", error)

    def closeEvent(self, event):
        self._stop()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


<<<<<<< HEAD
if __name__ == "____main__":
    main()
=======
if __name__ == "__main__":
    main()
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
