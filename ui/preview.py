"""
Subtitle preview widget for the video editor.
Displays subtitles with real-time highlighting.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer


class SubtitlePreviewWidget(QWidget):
    """Widget for previewing subtitles with highlighting."""
    
    def __init__(self, subtitle_lines, parent=None):
        super().__init__(parent)
        self.subtitle_lines = subtitle_lines
        self.current_time = 0
        self.playing = False
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
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
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_subtitle)
    
    def start(self, interval=50):
        self.playing = True
        self.timer.start(interval)
    
    def stop(self):
        self.playing = False
        self.timer.stop()
    
    def set_time(self, time):
        self.current_time = time
        self.update_subtitle()
    
    def update_subtitle(self):
        if not self.subtitle_lines:
            self.subtitle_label.setText("")
            return
        
        active_line = None
        for line in self.subtitle_lines:
            if line.start_time <= self.current_time <= line.end_time:
                active_line = line
                break
        
        if active_line:
            html = "<div style='text-align: center;'>"
            for word in active_line.words:
                if word.start_time <= self.current_time <= word.end_time:
                    html += f"<span style='background-color: yellow; color: black; padding: 2px 4px; font-size: 1.2em;'>{word.text}</span> "
                else:
                    html += f"<span>{word.text}</span> "
            html += "</div>"
            self.subtitle_label.setText(html)
        else:
            self.subtitle_label.setText("")
    
    def set_subtitle_lines(self, subtitle_lines):
        self.subtitle_lines = subtitle_lines
        self.update_subtitle()