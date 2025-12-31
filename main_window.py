from base_import import *
from popup_window import FadingPopup


class MainWindow(QWidget):
    # 大小和停靠位置参数
    WIDTH = 600
    HEIGHT = 1000
    PADDING = 20
    K=0.1 # 回弹系数
    R=100 # 回弹半径
    TITLE = "MyToolkitMainWindow"
    def __init__(self):
        super().__init__()

        # 停靠在屏幕右上角
        screen_geometry = QApplication.primaryScreen().geometry()
        self.position_1 = QPoint(screen_geometry.width()-self.WIDTH-self.PADDING, self.PADDING)
        self.position_2 = QPoint(screen_geometry.width()-self.PADDING, self.PADDING)
        self.setGeometry(self.position_1.x(), self.position_1.y(), self.WIDTH, self.HEIGHT)

        self.setAcceptDrops(True)
        self.setWindowTitle(self.TITLE)
        self.setStyleSheet("background-color: transparent;")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.bgwidget=BackgroundWidget(self)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        content_widget = QWidget(scroll)
        scroll.setWidget(content_widget)
        self.layout = QVBoxLayout(content_widget)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(scroll)

        self.widgets = []
        self.messages = queue.Queue()
        self.timer = QTimer(self)
        self.timer.singleShot(1000, self.checkMessage)
        self.drag_position = None # 鼠标拖动位置相对窗口左上角的偏移
        self.hidden=False # 是否收缩进屏幕右侧
        self._keyboard_moving_timer = None # 非鼠标导致窗口隐藏状态发生更改的动画

    def addWidget(self, widget):
        self.layout.addWidget(widget)
        self.widgets.append(widget)
        return

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for widget in self.widgets:
            if hasattr(widget, 'dropEvent'):
                widget.dropEvent(event)
        return
    
    def keyPressEvent(self, a0):
        # 如果按下F24，切换隐藏状态
        if a0.key() == Qt.Key_F24:
            self.refreshHiddenState(not self.hidden)
        # 如果按下F18，直接退出
        elif a0.key() == Qt.Key_F18:
            raise SystemExit

    # 可以拖动，但是总是试图回到停靠位置
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            # 将窗口移动到鼠标位置和初始偏移量之间
            mouse_pos = event.globalPos() - self.drag_position
            desired_pos = self.position_1
            if mouse_pos.x()>desired_pos.x():
                desired_pos=QPoint(mouse_pos.x(), desired_pos.y())
            delta = mouse_pos-desired_pos
            beta = (delta.x()**2+delta.y()**2)**0.5/self.R
            # beta_normalized = math.tanh(beta)/beta if not math.isclose(beta, 0) else 1
            beta_normalized = math.log(1+beta)/beta if not math.isclose(beta, 0) else 1
            target_pos = desired_pos + (mouse_pos - desired_pos) * beta_normalized
            self.move(target_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = None

        if self.hidden:
            self.hidden = False
        elif self.pos().x() > self.position_1.x() + self.WIDTH / 6:
            self.hidden = True

        # 动画回到停靠位置
        def update_position():
            if self.drag_position is not None:
                self.animation_timer.stop()
                self._set_hidden_position()
                return
            current_pos = self.pos()
            target_pos = self.position_1 if not self.hidden else self.position_2
            delta = target_pos - current_pos
            distance = math.hypot(delta.x(), delta.y())
            if distance < 1:
                self.move(target_pos)
                self.animation_timer.stop()
                self._set_hidden_position()
                return
            step = QPointF(delta.x() * self.K, delta.y() * self.K)
            new_pos = current_pos + step.toPoint()
            self.move(new_pos)
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(update_position)
        self.animation_timer.start(16)  # 大约60 FPS

        event.accept()

    def _set_hidden_position(self):
        if self.hidden:
            self.move(self.position_2)
        else:
            self.move(self.position_1)

    def _keyboard_moving_updater(self):
        if self.drag_position is not None:
            self._keyboard_moving_timer.stop()
            self._keyboard_moving_timer = None
            return
        current_pos = self.pos()
        target_pos = self.position_1 if not self.hidden else self.position_2
        delta = target_pos - current_pos
        distance = math.hypot(delta.x(), delta.y())
        if distance < 1:
            self.move(target_pos)
            if self._keyboard_moving_timer is not None:
                self._keyboard_moving_timer.stop()
                self._keyboard_moving_timer = None
            return
        step = QPointF(delta.x() * self.K, delta.y() * self.K)
        new_pos = current_pos + step.toPoint()
        self.move(new_pos)

    def refreshHiddenState(self, hidden: bool):
        if self._keyboard_moving_timer is not None:
            self._keyboard_moving_timer.stop()
            self._keyboard_moving_timer = None
            self._set_hidden_position()
        self.hidden = hidden
        self._keyboard_moving_timer = QTimer(self)
        self._keyboard_moving_timer.timeout.connect(self._keyboard_moving_updater)
        self._keyboard_moving_timer.start(16)

    @ staticmethod
    def showPopup(message, parent=None):
        popup = FadingPopup(message, parent)
        popup.fadeIn()
        return popup

    def checkMessage(self):
        messages = []
        while not self.messages.empty():
            message = self.messages.get_nowait()
            messages.append(message)
        if messages:
            self.showPopup('\n'.join(messages), parent=self)
        if self.isVisible():
            self.timer.singleShot(500, self.checkMessage)
        return
    
    def closeEvent(self, a0):
        raise SystemExit


class BackgroundWidget(QLabel):
    DEFAULT_COLOR = "lightblue"
    IMAGE_PATH = None  # "path/to/your/image.png"
    BORDER_RADIUS = 50
    def __init__(self, parent):
        super().__init__(parent)
        self.main=parent
        self.setGeometry(0, 0, self.main.width(), self.main.height())
        self.container=QLabel(self)
        self.container.setStyleSheet("background-color: transparent; font-size: 10pt; margin: 20px;")
        self.setStyleSheet(f"background-color: {self.DEFAULT_COLOR}; border-radius: {self.BORDER_RADIUS}px; ")
        if self.IMAGE_PATH and os.path.exists(self.IMAGE_PATH):
            # 读取并裁剪图片，使其具有透明圆角，且长宽比和窗口一致
            pixmap = QPixmap(self.IMAGE_PATH)
            mask = QPixmap(pixmap.size())
            mask.fill(Qt.transparent)
            painter = QPainter(mask)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(Qt.white)
            painter.setPen(Qt.NoPen)
            rect = QRectF(0, 0, pixmap.width(), pixmap.height())
            radius = min(pixmap.width(), pixmap.height()) * self.BORDER_RADIUS / min(self.main.width(), self.main.height())
            painter.drawRoundedRect(rect, radius, radius)
            painter.end()
            pixmap.setMask(mask.createMaskFromColor(Qt.transparent))
            self.setPixmap(pixmap)
            self.setScaledContents(True)

        self.container.show()
        
if __name__ == "__main__":
    from start_check import check_started
    BackgroundWidget.IMAGE_PATH = os.path.join(os.path.dirname(__file__), "test_image.png")
    app = QApplication(sys.argv)
    check_started()
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

