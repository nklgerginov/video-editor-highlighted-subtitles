import os, sys
from typing import Optional
from PyQt6.QtWidgets import *
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
            gen = SubtitleGenerator(self.vosk_model_path)
            proj = gen.process_video(self.video_path, self.vosk_model_path)
            self.processing_complete.emit(proj)
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
        self.setMinimumSize(1000, 700)
        self.project = VideoProject()
        self.current_video_path = ""
        self._setup_ui()
        self._setup_connections()
        self._load_fonts()
        self._setup_media_player()

    def _setup_ui(self):
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
        self.font_cb.clear()
        self.font_cb.addItems(QFontDatabase().families())

    def _update_style(self):
        if not self.project:
            self.project = VideoProject()
        self.project.style = SubtitleStyle(
            font_family=self.font_cb.currentText(),
            font_size=self.fsize_sp.value(),
            highlight_scale=self.hscale_sp.value(),
            text_color="#FFFFFF",
            highlight_color="#FFFF00"
        )
        if self.preview.project:
            self.preview.set_project(self.project)

    def _update_pos_spins(self, pos: SubtitlePosition):
        self.x_sp.setValue(pos.x)
        self.y_sp.setValue(pos.y)
        self.w_sp.setValue(pos.width)
        self.h_sp.setValue(pos.height)
        self.pos_lbl.setText(f"Position: {pos.x}px, {pos.y}px")

    def _update_pos(self):
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


if __name__ == "__main__":
    main()