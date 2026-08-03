from typing import Optional, List
<<<<<<< HEAD
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGraphicsTextItem,
    QGraphicsRectItem,
    QGraphicsItem,
)
from PyQt6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QFont, QFontMetrics
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
=======
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsTextItem, QGraphicsRectItem, QGraphicsItem
<<<<<<< HEAD
from PyQt6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QFont, QFontMetrics, QMouseEvent
from PyQt6.QtCore import Qt, QPoint, QRect, QSize, QTimer, pyqtSignal
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
=======
from PyQt6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QFont, QFontMetrics
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c
from models import VideoProject, Word, SubtitleLine, SubtitleStyle, SubtitlePosition


class SubtitleBox(QGraphicsRectItem):
<<<<<<< HEAD
    """Resizable and draggable subtitle box with 8 resize handles."""

=======
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
    def __init__(self, x: int, y: int, width: int, height: int, parent=None):
        super().__init__(0, 0, width, height, parent)
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setPen(QPen(QColor(200, 200, 200, 200), 2, Qt.PenStyle.DashLine))
        self.setBrush(QBrush(QColor(0, 0, 0, 128)))
<<<<<<< HEAD

        # Resize handles
=======
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
        self.resize_handle_size = 10
        self.resize_handles = []
        self._create_handles()
        self.resizing = False
        self.resize_direction = None
        self.drag_start_pos = None
        self.original_rect = None

    def _create_resize_handles(self):
<<<<<<< HEAD
<<<<<<< HEAD
        handle_positions = [
            (0, 0, "top-left"),
            (1, 0, "top-right"),
            (0, 1, "bottom-left"),
            (1, 1, "bottom-right"),
            (0.5, 0, "top"),
            (1, 0.5, "right"),
            (0.5, 1, "bottom"),
            (0, 0.5, "left"),
        ]

        for rel_x, rel_y, direction in handle_positions:
            handle = QGraphicsRectItem(
                -self.resize_handle_size / 2,
                -self.resize_handle_size / 2,
                self.resize_handle_size,
                self.resize_handle_size,
                self,
            )
=======
        handle_positions = [(0, 0, "top-left"), (1, 0, "top-right"), (0, 1, "bottom-left"), (1, 1, "bottom-right"), (0.5, 0, "top"), (1, 0.5, "right"), (0.5, 1, "bottom"), (0, 0.5, "left")]
        for rel_x, rel_y, direction in handle_positions:
            handle = QGraphicsRectItem(-self.resize_handle_size/2, -self.resize_handle_size/2, self.resize_handle_size, self.resize_handle_size, self)
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
            handle.setPos(self.rect().width() * rel_x, self.rect().height() * rel_y)
=======
        handle_positions = [(0, 0, "tl"), (1, 0, "tr"), (0, 1, "bl"), (1, 1, "br"), (0.5, 0, "t"), (1, 0.5, "r"), (0.5, 1, "b"), (0, 0.5, "l")]
        for rx, ry, dirn in handle_positions:
            handle = QGraphicsRectItem(-5, -5, 10, 10, self)
            handle.setPos(self.rect().width() * rx, self.rect().height() * ry)
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c
            handle.setBrush(QBrush(QColor(255, 255, 255, 200)))
            handle.setPen(QPen(QColor(100, 100, 100), 1))
            handle.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            handle.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            handle.setAcceptHoverEvents(True)
            handle.setData(0, dirn)
            self.resize_handles.append(handle)

    def update_resize_handles(self):
<<<<<<< HEAD
<<<<<<< HEAD
        handle_positions = [
            (0, 0, "top-left"),
            (1, 0, "top-right"),
            (0, 1, "bottom-left"),
            (1, 1, "bottom-right"),
            (0.5, 0, "top"),
            (1, 0.5, "right"),
            (0.5, 1, "bottom"),
            (0, 0.5, "left"),
        ]
=======
        handle_positions = [(0, 0, "top-left"), (1, 0, "top-right"), (0, 1, "bottom-left"), (1, 1, "bottom-right"), (0.5, 0, "top"), (1, 0.5, "right"), (0.5, 1, "bottom"), (0, 0.5, "left")]
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
        for handle, (rel_x, rel_y, _) in zip(self.resize_handles, handle_positions):
            handle.setPos(self.rect().width() * rel_x, self.rect().height() * rel_y)
=======
        handle_positions = [(0, 0, "tl"), (1, 0, "tr"), (0, 1, "bl"), (1, 1, "br"), (0.5, 0, "t"), (1, 0.5, "r"), (0.5, 1, "b"), (0, 0.5, "l")]
        for handle, (rx, ry, _) in zip(self.resize_handles, handle_positions):
            handle.setPos(self.rect().width() * rx, self.rect().height() * ry)
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c

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
<<<<<<< HEAD
<<<<<<< HEAD

=======
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
            if "left" in self.resize_direction:
=======
            if "l" in self.resize_direction:
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c
                rect.setLeft(rect.left() + delta.x())
            if "r" in self.resize_direction:
                rect.setRight(rect.right() + delta.x())
            if "t" in self.resize_direction:
                rect.setTop(rect.top() + delta.y())
            if "b" in self.resize_direction:
                rect.setBottom(rect.bottom() + delta.y())
<<<<<<< HEAD

            # Minimum size constraints
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

=======
            if rect.width() < 50:
                if "l" in self.resize_direction:
                    rect.setLeft(rect.right() - 50)
                else:
                    rect.setRight(rect.left() + 50)
            if rect.height() < 30:
<<<<<<< HEAD
                rect.setTop(rect.bottom() - 30) if "top" in self.resize_direction else rect.setBottom(rect.top() + 30)
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
=======
                if "t" in self.resize_direction:
                    rect.setTop(rect.bottom() - 30)
                else:
                    rect.setBottom(rect.top() + 30)
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c
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
<<<<<<< HEAD
        return SubtitlePosition(
            x=int(pos.x()),
            y=int(pos.y()),
            width=int(rect.width()),
            height=int(rect.height()),
        )


=======
        return SubtitlePosition(x=int(pos.x()), y=int(pos.y()), width=int(rect.width()), height=int(rect.height()))


<<<<<<< HEAD
class SubtitleTextItem(QGraphicsTextItem):
    def __init__(self, word: Word, style: SubtitleStyle, parent=None):
        super().__init__(word.text, parent)
        self.word = word
        self.style = style
        self.is_highlighted = False
        self.set_default_appearance()

    def set_default_appearance(self):
        font = QFont(self.style.font_family, self.style.font_size)
        self.setFont(font)
        self.setDefaultTextColor(QColor(self.style.text_color))
        self.is_highlighted = False

    def set_highlighted_appearance(self):
        font = QFont(self.style.font_family, int(self.style.font_size * self.style.highlight_scale))
        self.setFont(font)
        self.setDefaultTextColor(QColor(self.style.highlight_color))
        self.is_highlighted = True


>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
=======
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c
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
<<<<<<< HEAD
<<<<<<< HEAD
        self.subtitle_box = SubtitleBox(
            position.x, position.y, position.width, position.height
        )
=======
        self.subtitle_box = SubtitleBox(position.x, position.y, position.width, position.height)
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
=======
        self.subtitle_box = SubtitleBox(pos.x, pos.y, pos.width, pos.height)
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c
        self.addItem(self.subtitle_box)
        self.subtitle_box.setZValue(10)

    def _update_subs(self):
        if self.project is None:
            return
<<<<<<< HEAD
<<<<<<< HEAD

        # Clear existing subtitle items
        for item in self.subtitle_items:
            self.removeItem(item)
        self.subtitle_items = []

        # Create or update subtitle box
        if self.subtitle_box is None:
            self.create_subtitle_box(self.project.position)
        else:
            self.subtitle_box.setRect(
                0, 0, self.project.position.width, self.project.position.height
            )
            self.subtitle_box.setPos(self.project.position.x, self.project.position.y)
            self.subtitle_box.update_resize_handles()

        # Draw words
        style = self.project.style
        x_offset = 20
        y_offset = 20 + style.font_size

        for line in self.project.subtitles:
            for word in line.words:
                # Check if this word should be highlighted
                is_active = (
                    self.current_time >= word.start_time
                    and self.current_time < word.end_time
                )

                # Create text item
                text_item = QGraphicsTextItem(word.text)
                if is_active:
                    font = QFont(
                        style.font_family, int(style.font_size * style.highlight_scale)
                    )
                    text_item.setDefaultTextColor(QColor(style.highlight_color))
                else:
                    font = QFont(style.font_family, style.font_size)
                    text_item.setDefaultTextColor(QColor(style.text_color))
                text_item.setFont(font)

                # Position relative to subtitle box
                text_item.setPos(
                    self.subtitle_box.pos().x() + x_offset,
                    self.subtitle_box.pos().y() + y_offset,
                )
                self.addItem(text_item)
                text_item.setZValue(20)
                self.subtitle_items.append(text_item)

                # Move x offset for next word
                font_metrics = QFontMetrics(font)
                word_width = font_metrics.horizontalAdvance(word.text)
                x_offset += word_width + 10

            # New line
=======
        for item in self.subtitle_items:
            self.removeItem(item)
        self.subtitle_items = []
=======
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c
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
<<<<<<< HEAD
                text_item = SubtitleTextItem(word, style)
                if is_active:
                    text_item.set_highlighted_appearance()
                else:
                    text_item.set_default_appearance()
                text_item.setPos(self.subtitle_box.pos().x() + x_offset, self.subtitle_box.pos().y() + y_offset)
                self.addItem(text_item)
                text_item.setZValue(20)
                self.subtitle_items.append(text_item)
                font = text_item.font()
                font_metrics = QFontMetrics(font)
                word_width = font_metrics.horizontalAdvance(word.text)
                x_offset += word_width + 10
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
            x_offset = 20
            y_offset += style.font_size * 1.5
=======
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
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c

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
<<<<<<< HEAD
        self.is_playing = False
<<<<<<< HEAD

        # Setup layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Graphics view
        self.graphics_view = QGraphicsView(self)
        self.graphics_view.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.graphics_view.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        self.graphics_view.setSizePolicy(
            QWidget.SizePolicy.Expanding, QWidget.SizePolicy.Expanding
        )

        # Scene
        self.scene = VideoPreviewScene(self)
        self.graphics_view.setScene(self.scene)
        self.layout.addWidget(self.graphics_view)

        # Connect position changes
        self.scene.position_changed_callback = self._on_position_changed

        # Timer for animation
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_frame)

=======
=======
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c
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
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
        self.setMinimumSize(400, 300)

    def set_project(self, project: VideoProject):
        self.project = project
        self.scene.set_project(project)
        self.scene.create_box(project.position)

    def set_video_frame(self, pixmap: QPixmap):
        self.scene.set_video_pixmap(pixmap)
<<<<<<< HEAD
<<<<<<< HEAD
        self.graphics_view.fitInView(
            self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio
        )
=======
        self.graphics_view.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
=======
        self.gview.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c

    def update_time(self, time: float):
        self.current_time = time
        self.scene.update_time(time)

    def set_playing(self, playing: bool):
        if playing:
<<<<<<< HEAD
            self.update_timer.start(33)  # ~30fps
=======
            self.update_timer.start(33)
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
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
<<<<<<< HEAD
            self.graphics_view.fitInView(
                self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio
            )
        super().resizeEvent(event)

    def sizeHint(self):
        return QSize(800, 600)
=======
            self.graphics_view.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
<<<<<<< HEAD
        super().resizeEvent(event)

    def sizeHint(self):
        return QSize(800, 600)
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
=======
        return super().resizeEvent(event)
>>>>>>> d68708e919fc1d12be8141077fdbfdeb7ddd243c
