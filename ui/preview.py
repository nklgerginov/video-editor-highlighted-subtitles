from typing import Optional, List
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsTextItem, QGraphicsRectItem, QGraphicsItem
from PyQt6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QFont, QFontMetrics
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from models import VideoProject, Word, SubtitleLine, SubtitleStyle, SubtitlePosition


class SubtitleBox(QGraphicsRectItem):
    def __init__(self, x: int, y: int, width: int, height: int, parent=None):
        super().__init__(0, 0, width, height, parent)
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setPen(QPen(QColor(200, 200, 200, 200), 2, Qt.PenStyle.DashLine))
        self.setBrush(QBrush(QColor(0, 0, 0, 128)))
        self.resize_handle_size = 10
        self.resize_handles = []
        self._create_handles()
        self.resizing = False
        self.resize_direction = None
        self.drag_start_pos = None
        self.original_rect = None

    def _create_resize_handles(self):
        handle_positions = [(0, 0, "tl"), (1, 0, "tr"), (0, 1, "bl"), (1, 1, "br"), (0.5, 0, "t"), (1, 0.5, "r"), (0.5, 1, "b"), (0, 0.5, "l")]
        for rx, ry, dirn in handle_positions:
            handle = QGraphicsRectItem(-5, -5, 10, 10, self)
            handle.setPos(self.rect().width() * rx, self.rect().height() * ry)
            handle.setBrush(QBrush(QColor(255, 255, 255, 200)))
            handle.setPen(QPen(QColor(100, 100, 100), 1))
            handle.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            handle.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            handle.setAcceptHoverEvents(True)
            handle.setData(0, dirn)
            self.resize_handles.append(handle)

    def update_resize_handles(self):
        handle_positions = [(0, 0, "tl"), (1, 0, "tr"), (0, 1, "bl"), (1, 1, "br"), (0.5, 0, "t"), (1, 0.5, "r"), (0.5, 1, "b"), (0, 0.5, "l")]
        for handle, (rx, ry, _) in zip(self.resize_handles, handle_positions):
            handle.setPos(self.rect().width() * rx, self.rect().height() * ry)

    def hoverEnterEvent(self, event):
        self.setPen(QPen(QColor(255, 255, 255, 200), 2, Qt.PenStyle.DashLine))
        return super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setPen(QPen(QColor(200, 200, 200, 200), 2, Qt.PenStyle.DashLine))
        return super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            for h in self.resize_handles:
                if h.contains(h.mapFromScene(event.scenePos())):
                    self.resizing = True
                    self.resize_dir = h.data(0)
                    self.drag_start = event.scenePos()
                    self.orig_rect = self.rect()
                    break
            else:
                return super().mousePressEvent(event)
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.resizing:
            delta = event.scenePos() - self.drag_start_pos
            rect = self.original_rect
            if "l" in self.resize_direction:
                rect.setLeft(rect.left() + delta.x())
            if "r" in self.resize_direction:
                rect.setRight(rect.right() + delta.x())
            if "t" in self.resize_direction:
                rect.setTop(rect.top() + delta.y())
            if "b" in self.resize_direction:
                rect.setBottom(rect.bottom() + delta.y())
            if rect.width() < 50:
                if "l" in self.resize_direction:
                    rect.setLeft(rect.right() - 50)
                else:
                    rect.setRight(rect.left() + 50)
            if rect.height() < 30:
                if "t" in self.resize_direction:
                    rect.setTop(rect.bottom() - 30)
                else:
                    rect.setBottom(rect.top() + 30)
            self.setRect(rect)
            self.update_resize_handles()
        else:
            return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.resizing = False
        self.resize_direction = None
        return super().mouseReleaseEvent(event)

    def get_position(self) -> SubtitlePosition:
        pos = self.pos()
        rect = self.rect()
        return SubtitlePosition(x=int(pos.x()), y=int(pos.y()), width=int(rect.width()), height=int(rect.height()))


class VideoPreviewScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_item = None
        self.subtitle_box = None
        self.project = None
        self.current_time = 0.0
        self.pos_cb = None

    def set_project(self, project: VideoProject):
        self.project = project
        self._update_subs()

    def set_video_pixmap(self, pixmap: QPixmap):
        if self.video_item is None:
            self.video_item = QGraphicsPixmapItem(pixmap)
            self.addItem(self.video_item)
        else:
            self.video_item.setPixmap(pixmap)
        self.video_item.setPos(0, 0)

    def create_box(self, pos: SubtitlePosition):
        if self.subtitle_box is not None:
            self.removeItem(self.subtitle_box)
        self.subtitle_box = SubtitleBox(pos.x, pos.y, pos.width, pos.height)
        self.addItem(self.subtitle_box)
        self.subtitle_box.setZValue(10)

    def _update_subs(self):
        if self.project is None:
            return
        if self.subtitle_box is None:
            self.create_box(self.project.position)
        else:
            self.subtitle_box.setRect(0, 0, self.project.position.width, self.project.position.height)
            self.subtitle_box.setPos(self.project.position.x, self.project.position.y)
            self.subtitle_box.update_handles()
        style = self.project.style
        x_off, y_off = 20, 20 + style.font_size
        for line in self.project.subtitles:
            for word in line.words:
                is_active = self.current_time >= word.start_time and self.current_time < word.end_time
                item = QGraphicsTextItem(word.text)
                font = QFont(style.font_family, style.font_size * (style.highlight_scale if is_active else 1))
                item.setFont(font)
                item.setDefaultTextColor(QColor(style.highlight_color if is_active else style.text_color))
                item.setPos(self.subtitle_box.pos().x() + x_off, self.subtitle_box.pos().y() + y_off)
                self.addItem(item)
                item.setZValue(20)
                self.subtitle_items.append(item)
                fm = QFontMetrics(font)
                x_off += fm.horizontalAdvance(word.text) + 10
            x_off = 20
            y_off += style.font_size * 1.5

    def update_time(self, time: float):
        self.current_time = time
        self._update_subs()

    def mouseReleaseEvent(self, event):
        if self.subtitle_box and self.position_changed_callback:
            self.position_changed_callback(self.subtitle_box.get_position())
        return super().mouseReleaseEvent(event)


class VideoPreviewWidget(QWidget):
    position_changed = pyqtSignal(SubtitlePosition)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.current_time = 0.0
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.graphics_view = QGraphicsView(self)
        self.graphics_view.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.graphics_view.setSizePolicy(QWidget.SizePolicy.Expanding, QWidget.SizePolicy.Expanding)
        self.scene = VideoPreviewScene(self)
        self.gview.setScene(self.scene)
        self.layout.addWidget(self.gview)
        self.scene.pos_cb = self._on_pos_changed
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_frame)
        self.setMinimumSize(400, 300)

    def set_project(self, project: VideoProject):
        self.project = project
        self.scene.set_project(project)
        self.scene.create_box(project.position)

    def set_video_frame(self, pixmap: QPixmap):
        self.scene.set_video_pixmap(pixmap)
        self.gview.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def update_time(self, time: float):
        self.current_time = time
        self.scene.update_time(time)

    def set_playing(self, playing: bool):
        if playing:
            self.update_timer.start(33)
        else:
            self.update_timer.stop()

    def _update_frame(self):
        if self.project:
            self.scene.update_time(self.current_time)

    def _on_pos_changed(self, pos: SubtitlePosition):
        if self.project:
            self.project.position = position
        self.position_changed.emit(position)

    def resizeEvent(self, event):
        if self.scene.video_item:
            self.graphics_view.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        return super().resizeEvent(event)