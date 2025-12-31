from base_import import *

class SwitchButton(QLabel):
    "长圆形开关，背景灰色或蓝色。包含一个白色圆形滑块可以左右滑动切换状态。"
    SIZE=60
    PADDING=5
    def __init__(self, parent=None, onchange=lambda state:None, onturnon=lambda:None, onturnoff=lambda:None):
        super().__init__(parent)
        self.setFixedSize(2*self.SIZE, self.SIZE)
        self.setCursor(Qt.PointingHandCursor)
        self.state = False  # 初始状态为关闭
        self.slider_position = self.PADDING  # 滑块初始位置
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_slider)
        self.target_position = self.PADDING  # 目标位置
        self.onchange = onchange
        self.onturnon = onturnon
        self.onturnoff = onturnoff

    def mousePressEvent(self, event):
        self.state = not self.state  # 切换状态
        self.onchange(self.state)
        if self.state:
            self.onturnon()
            self.target_position = self.width() - (self.SIZE-self.PADDING)  # 打开状态滑块位置
        else:
            self.onturnoff()
            self.target_position = self.PADDING  # 关闭状态滑块位置
        self.animation_timer.start(10)  # 启动动画定时器

    def animate_slider(self):
        if self.slider_position < self.target_position:
            self.slider_position += max(0.1 * (self.target_position - self.slider_position), 1)
            self.slider_position = round(self.slider_position)
            if self.slider_position > self.target_position:
                self.slider_position = self.target_position
        elif self.slider_position > self.target_position:
            self.slider_position += min(0.1 * (self.target_position - self.slider_position), -1)
            self.slider_position = round(self.slider_position)
            if self.slider_position < self.target_position:
                self.slider_position = self.target_position
        else:
            self.slider_position = self.target_position
            self.animation_timer.stop()  # 到达目标位置，停止动画
        self.update()  # 触发重绘

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制背景
        if self.state:
            painter.setBrush(QColor(0, 122, 204))  # 打开状态蓝色
        else:
            painter.setBrush(QColor(200, 200, 200))  # 关闭状态灰色
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), self.SIZE//2, self.SIZE//2)

        # 绘制滑块
        painter.setBrush(QColor(255, 255, 255))  # 白色滑块
        painter.drawEllipse(self.slider_position, self.PADDING, self.SIZE-2*self.PADDING, self.SIZE-2*self.PADDING)
        painter.end()

    
if __name__ == "__main__":
    from main_window import MainWindow, BackgroundWidget
    from start_check import check_started
    BackgroundWidget.IMAGE_PATH = os.path.join(os.path.dirname(__file__), "test_image.png")
    app = QApplication(sys.argv)
    check_started()
    window = MainWindow(app=app)
    window.addWidget(
        SwitchButton(
            onchange=lambda state: print("State changed to", state),
            onturnon=lambda: print("Turned ON"),
            onturnoff=lambda: print("Turned OFF")
        ))
    window.show()
    sys.exit(app.exec_())

