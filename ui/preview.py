from typing import Optional, List
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsItem
from PyQt6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QFont, QFontMetrics
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from models import VideoProject, SubtitleStyle, SubtitlePosition


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
        self.resize_dir = None
        self.drag_start = None
        self.orig_rect = None

    def _create_handles(self):
        positions = [(0,0,"tl"),(1,0,"tr"),(0,1,"bl"),(1,1,"br"),(0.5,0,"t"),(1,0.5,"r"),(0.5,1,"b"),(0,0.5,"l")]
        for rx, ry, d in positions:
            h = QGraphicsRectItem(-5, -5, 10, 10, self)
            h.setPos(self.rect().width() * rx, self.rect().height() * ry)
            h.setBrush(QBrush(QColor(255, 255, 255, 200)))
            h.setPen(QPen(QColor(100, 100, 100), 1))
            h.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            h.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            h.setAcceptHoverEvents(True)
            h.setData(0, d)
            self.resize_handles.append(h)

    def update_handles(self):
        positions = [(0,0,"tl"),(1,0,"tr"),(0,1,"bl"),(1,1,"br"),(0.5,0,"t"),(1,0.5,"r"),(0.5,1,"b"),(0,0.5,"l")]
        for h, (rx, ry, _) in zip(self.resize_handles, positions):
            h.setPos(self.rect().width() * rx, self.rect().height() * ry)

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
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.resizing:
            delta = event.scenePos() - self.drag_start
            r = self.orig_rect
            if "l" in self.resize_dir:
                r.setLeft(r.left() + delta.x())
            if "r" in self.resize_dir:
                r.setRight(r.right() + delta.x())
            if "t" in self.resize_dir:
                r.setTop(r.top() + delta.y())
            if "b" in self.resize_dir:
                r.setBottom(r.bottom() + delta.y())
            if r.width() < 50:
                r.setLeft(r.right() - 50) if "l" in self.resize_dir else r.setRight(r.left() + 50)
            if r.height() < 30:
                r.setTop(r.bottom() - 30) if "t" in self.resize_dir else r.setBottom(r.top() + 30)
            self.setRect(r)
            self.update_handles()
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.resizing = False
        self.resize_dir = None
        return super().mouseReleaseEvent(event)

    def get_position(self) -> SubtitlePosition:
        p = self.pos()
        r = self.rect()
        return SubtitlePosition(int(p.x()), int(p.y()), int(r.width()), int(r.height()))


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
        x, y = 20, 20 + style.font_size
        for line in self.project.subtitles:
            for word in line.words:
                is_active = self.current_time >= word.start_time and self.current_time < word.end_time
                item = QGraphicsPixmapItem()
                font = QFont(style.font_family, style.font_size * (style.highlight_scale if is_active else 1))
                color = QColor(style.highlight_color if is_active else style.text_color)
                # Create text item would be better but using simplified approach
                txt_item = QGraphicsPixmapItem()
                # Actually let's just use QGraphicsTextItem
                txt_item = QGraphicsTextItem(word.text)
                txt_item.setFont(font)
                txt_item.setDefaultTextColor(color)
                txt_item.setPos(self.subtitle_box.pos().x() + x, self.subtitle_box.pos().y() + y)
                self.addItem(txt_item)
                txt_item.setZValue(20)
                fm = QFontMetrics(font)
                x += fm.horizontalAdvance(word.text) + 10
            x = 20
            y += style.font_size * 1.5

    def update_time(self, time: float):
        self.current_time = time
        self._update_subs()

    def mouseReleaseEvent(self, event):
        if self.subtitle_box and self.pos_cb:
            self.pos_cb(self.subtitle_box.get_position())
        return super().mouseReleaseEvent(event)


class VideoPreviewWidget(QWidget):
    position_changed = pyqtSignal(SubtitlePosition)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.current_time = 0.0
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.gview = QGraphicsView(self)
        self.gview.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.gview.setSizePolicy(QWidget.SizePolicy.Expanding, QWidget.SizePolicy.Expanding)
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
            self.project.position = pos
        self.position_changed.emit(pos)

    def resizeEvent(self, event):
        if self.scene.video_item:
            self.gview.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        return super().resizeEvent(event)