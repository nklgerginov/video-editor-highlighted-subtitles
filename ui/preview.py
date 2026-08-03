from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem, QGraphicsTextItem, QGraphicsRectItem, QGraphicsItem, QSizePolicy
)
from PyQt6.QtGui import (
    QPixmap, QPainter, QPen, QBrush, QColor, QFont, QFontMetrics
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from models import VideoProject, Word, SubtitleLine, SubtitleStyle, SubtitlePosition


class SubtitleBox(QGraphicsRectItem):
    """Resizable and draggable subtitle box with 8 resize handles."""

    def __init__(self, x: int, y: int, width: int, height: int, parent=None, bg_opacity: int = 128):
        super().__init__(0, 0, width, height, parent)
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setPen(QPen(QColor(200, 200, 200, 200), 2, Qt.PenStyle.DashLine))
        self.setBrush(QBrush(QColor(0, 0, 0, bg_opacity)))

        self.resize_handle_size = 10
        self.resize_handles = []
        self._create_resize_handles()
        self.resizing = False
        self.resize_direction = None
        self.drag_start_pos = None
        self.original_rect = None

    def _create_resize_handles(self):
        handle_positions = [
            (0, 0, "top-left"), (1, 0, "top-right"),
            (0, 1, "bottom-left"), (1, 1, "bottom-right"),
            (0.5, 0, "top"), (1, 0.5, "right"),
            (0.5, 1, "bottom"), (0, 0.5, "left")
        ]

        for rel_x, rel_y, direction in handle_positions:
            handle = QGraphicsRectItem(
                -self.resize_handle_size/2, -self.resize_handle_size/2,
                self.resize_handle_size, self.resize_handle_size, self
            )
            handle.setPos(self.rect().width() * rel_x, self.rect().height() * rel_y)
            handle.setBrush(QBrush(QColor(255, 255, 255, 200)))
            handle.setPen(QPen(QColor(100, 100, 100, 200), 1))
            handle.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            handle.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            handle.setAcceptHoverEvents(True)
            handle.setData(0, direction)
            self.resize_handles.append(handle)

    def update_resize_handles(self):
        handle_positions = [
            (0, 0, "top-left"), (1, 0, "top-right"),
            (0, 1, "bottom-left"), (1, 1, "bottom-right"),
            (0.5, 0, "top"), (1, 0.5, "right"),
            (0.5, 1, "bottom"), (0, 0.5, "left")
        ]
        for handle, (rel_x, rel_y, _) in zip(self.resize_handles, handle_positions):
            handle.setPos(self.rect().width() * rel_x, self.rect().height() * rel_y)

    def hoverEnterEvent(self, event):
        self.setPen(QPen(QColor(255, 255, 255, 200), 2, Qt.PenStyle.DashLine))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setPen(QPen(QColor(200, 200, 200, 200), 2, Qt.PenStyle.DashLine))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            for handle in self.resize_handles:
                if handle.contains(handle.mapFromScene(event.scenePos())):
                    self.resizing = True
                    self.resize_direction = handle.data(0)
                    self.drag_start_pos = event.scenePos()
                    self.original_rect = self.rect()
                    break
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.resizing:
            delta = event.scenePos() - self.drag_start_pos
            rect = self.original_rect

            if "left" in self.resize_direction:
                rect.setLeft(rect.left() + delta.x())
            if "right" in self.resize_direction:
                rect.setRight(rect.right() + delta.x())
            if "top" in self.resize_direction:
                rect.setTop(rect.top() + delta.y())
            if "bottom" in self.resize_direction:
                rect.setBottom(rect.bottom() + delta.y())

            if rect.width() < 50:
                if "left" in self.resize_direction:
                    rect.setLeft(rect.right() - 50)
                else:
                    rect.setRight(rect.left() + 50)
            if rect.height() < 30:
                if "top" in self.resize_direction:
                    rect.setTop(rect.bottom() - 30)
                else:
                    rect.setBottom(rect.top() + 30)

            self.setRect(rect)
            self.update_resize_handles()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.resizing = False
        self.resize_direction = None
        super().mouseReleaseEvent(event)

    def get_position(self) -> SubtitlePosition:
        pos = self.pos()
        rect = self.rect()
        return SubtitlePosition(
            x=int(pos.x()),
            y=int(pos.y()),
            width=int(rect.width()),
            height=int(rect.height())
        )


class VideoPreviewScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_item = None
        self.subtitle_box = None
        self.subtitle_items = []
        self.project = None
        self.current_time = 0.0
        self.position_changed_callback = None

    def set_project(self, project: VideoProject):
        self.project = project
        self.update_subtitles()

    def set_video_pixmap(self, pixmap: QPixmap):
        if self.video_item is None:
            self.video_item = QGraphicsPixmapItem(pixmap)
            self.addItem(self.video_item)
        else:
            self.video_item.setPixmap(pixmap)
        self.video_item.setPos(0, 0)

    def create_subtitle_box(self, position: SubtitlePosition):
        if self.subtitle_box is not None:
            self.removeItem(self.subtitle_box)
        bg_opacity = 128
        if self.project and self.project.style:
            bg_opacity = self.project.style.background_opacity
        self.subtitle_box = SubtitleBox(
            position.x, position.y, position.width, position.height, bg_opacity=bg_opacity
        )
        self.addItem(self.subtitle_box)
        self.subtitle_box.setZValue(10)

    def update_subtitles(self):
        if self.project is None:
            return

        for item in self.subtitle_items:
            self.removeItem(item)
        self.subtitle_items = []

        if self.subtitle_box is None:
            self.create_subtitle_box(self.project.position)
        else:
            self.subtitle_box.setRect(0, 0, self.project.position.width, self.project.position.height)
            self.subtitle_box.setPos(self.project.position.x, self.project.position.y)
            self.subtitle_box.update_resize_handles()

        style = self.project.style
        x_offset = 20
        y_offset = 20 + style.font_size

        for line in self.project.subtitles:
            for word in line.words:
                is_active = (self.current_time >= word.start_time and
                           self.current_time < word.end_time)

                text_item = QGraphicsTextItem(word.text, self.subtitle_box)
                if is_active:
                    font = QFont(style.font_family, style.highlight_font_size)
                    font.setBold(style.bold)
                    font.setItalic(style.italic)
                    text_item.setDefaultTextColor(QColor(style.highlight_color))
                else:
                    font = QFont(style.font_family, style.font_size)
                    font.setBold(style.bold)
                    font.setItalic(style.italic)
                    text_item.setDefaultTextColor(QColor(style.text_color))
                text_item.setFont(font)

                text_item.setPos(x_offset, y_offset)
                text_item.setZValue(20)
                self.subtitle_items.append(text_item)

                font_metrics = QFontMetrics(font)
                word_width = font_metrics.horizontalAdvance(word.text)
                x_offset += word_width + 10

            x_offset = 20
            y_offset += style.font_size * 1.5

    def update_time(self, time: float):
        self.current_time = time
        self.update_subtitles()

    def mouseReleaseEvent(self, event):
        if self.subtitle_box and self.position_changed_callback:
            position = self.subtitle_box.get_position()
            self.position_changed_callback(position)
            self.update_subtitles()
        super().mouseReleaseEvent(event)


class VideoPreviewWidget(QWidget):
    position_changed = pyqtSignal(SubtitlePosition)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.current_time = 0.0
        self.is_playing = False

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.graphics_view = QGraphicsView(self)
        self.graphics_view.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.graphics_view.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        self.graphics_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.scene = VideoPreviewScene(self)
        self.graphics_view.setScene(self.scene)
        self.layout.addWidget(self.graphics_view)

        self.scene.position_changed_callback = self._on_position_changed

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_frame)

        self.setMinimumSize(400, 300)

    def set_project(self, project: VideoProject):
        self.project = project
        self.scene.set_project(project)
        self.scene.create_subtitle_box(project.position)

    def set_video_frame(self, pixmap: QPixmap):
        self.scene.set_video_pixmap(pixmap)
        self.graphics_view.fitInView(
            self.scene.itemsBoundingRect(),
            Qt.AspectRatioMode.KeepAspectRatio
        )

    def update_time(self, time: float):
        self.current_time = time
        self.scene.update_time(time)

    def set_playing(self, playing: bool):
        self.is_playing = playing
        if playing:
            self.update_timer.start(33)
        else:
            self.update_timer.stop()

    def _update_frame(self):
        if self.project:
            self.scene.update_time(self.current_time)

    def _on_position_changed(self, position: SubtitlePosition):
        if self.project:
            self.project.position = position
        self.position_changed.emit(position)

    def get_current_position(self) -> SubtitlePosition:
        if self.scene.subtitle_box:
            return self.scene.subtitle_box.get_position()
        return self.project.position if self.project else SubtitlePosition()

    def resizeEvent(self, event):
        if self.scene.video_item:
            self.graphics_view.fitInView(
                self.scene.itemsBoundingRect(),
                Qt.AspectRatioMode.KeepAspectRatio
            )
        super().resizeEvent(event)

    def sizeHint(self):
        return QSize(800, 600)