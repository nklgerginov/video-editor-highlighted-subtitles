"""
Subtitle preview widget with drag-and-drop positioning.
Displays subtitles with real-time highlighting and Canva-style drag positioning.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QMouseEvent, QEnterEvent


class DraggableLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 150); border-radius: 10px; padding: 20px; font-weight: bold; color: white;")
        self.drag_start_position = None
        self.is_dragging = False
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.globalPosition().toPoint() - self.pos()
            self.is_dragging = True
            self.raise_()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if self.is_dragging and self.drag_start_position:
            new_pos = event.globalPosition().toPoint() - self.drag_start_position
            self.move(new_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.drag_start_position = None
            # Notify parent that position changed
            if hasattr(self.parent(), 'on_label_moved'):
                self.parent().on_label_moved()
            event.accept()
    
    def enterEvent(self, event):
        self.setStyleSheet("background-color: rgba(0, 0, 0, 180); border-radius: 10px; padding: 20px; font-weight: bold; color: white; border: 2px dashed #0078d7;")
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.setStyleSheet("background-color: rgba(0, 0, 0, 150); border-radius: 10px; padding: 20px; font-weight: bold; color: white;")
        super().leaveEvent(event)


class SubtitlePreviewWidget(QWidget):
    def __init__(self, subtitle_lines, subtitle_style=None, parent=None):
        super().__init__(parent)
        self.subtitle_lines = subtitle_lines
        self.subtitle_style = subtitle_style or {
            'position_x': 0.5,
            'position_y': 0.85,
            'font': 'Arial',
            'fontsize': 24,
            'color': 'white',
            'highlight_color': 'yellow'
        }
        self.current_time = 0
        self.playing = False
        self.draggable_label = None
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.container = QFrame(self)
        self.container.setLayout(QVBoxLayout())
        self.container.layout().setContentsMargins(0, 0, 0, 0)
        self.container.layout().setSpacing(0)
        self.container.setStyleSheet("background-color: transparent;")
        self.container.setMinimumHeight(400)
        self.layout.addWidget(self.container)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_subtitle)
        
        self.create_draggable_label()
    
    def create_draggable_label(self):
        if self.draggable_label:
            self.draggable_label.deleteLater()
        
        self.draggable_label = DraggableLabel("", self.container)
        self.draggable_label.setMinimumWidth(200)
        self.draggable_label.setMinimumHeight(50)
        self.container.layout().addWidget(self.draggable_label)
        self.update_label_style()
    
    def on_label_moved(self):
        pos = self.get_position()
        self.subtitle_style['position_x'] = pos['position_x']
        self.subtitle_style['position_y'] = pos['position_y']
    
    def update_label_style(self):
        if self.draggable_label:
            fontsize = self.subtitle_style.get('fontsize', 24)
            color = self.subtitle_style.get('color', 'white')
            font = self.subtitle_style.get('font', 'Arial')
            self.draggable_label.setStyleSheet(f"background-color: rgba(0, 0, 0, 150); border-radius: 10px; padding: 20px; font-weight: bold; color: {color}; font-size: {fontsize}px; font-family: {font};")
            
            container_width = self.container.width()
            container_height = self.container.height()
            if container_width > 0 and container_height > 0:
                x = int(self.subtitle_style.get('position_x', 0.5) * container_width)
                y = int(self.subtitle_style.get('position_y', 0.85) * container_height)
                self.draggable_label.move(x, y)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_label_style()
    
    def set_style(self, subtitle_style):
        self.subtitle_style.update(subtitle_style)
        self.update_label_style()
    
    def get_position(self):
        if self.draggable_label and self.container.width() > 0 and self.container.height() > 0:
            pos = self.draggable_label.pos()
            return {
                'position_x': pos.x() / self.container.width(),
                'position_y': pos.y() / self.container.height()
            }
        return {'position_x': 0.5, 'position_y': 0.85}
    
    def save_position(self):
        pos = self.get_position()
        self.subtitle_style.update(pos)
        return pos
    
    def start(self, interval=50):
        self.playing = True
        self.timer.start(interval)
    
    def stop(self):
        self.playing = False
        self.timer.stop()
    
    def set_time(self, time):
        self.current_time = time
        self.update_subtitle()
    
    def set_subtitle_lines(self, subtitle_lines):
        self.subtitle_lines = subtitle_lines
        self.update_subtitle()
    
    def update_subtitle(self):
        if not self.subtitle_lines:
            if self.draggable_label:
                self.draggable_label.setText("")
            return
        
        active_line = None
        for line in self.subtitle_lines:
            if line.start_time <= self.current_time <= line.end_time:
                active_line = line
                break
        
        if active_line and self.draggable_label:
            html = ""
            for word in active_line.words:
                if word.start_time <= self.current_time <= word.end_time:
                    html += f"<span style='background-color: yellow; color: black; padding: 2px 4px; font-size: 1.2em;'>{word.text}</span> "
                else:
                    html += f"<span>{word.text}</span> "
            self.draggable_label.setText(html)
        elif self.draggable_label:
            self.draggable_label.setText("")