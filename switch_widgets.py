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
        self.animation_timer = None
        self.animation_repeat_count = 0
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
        if self.animation_timer is not None:
            self.animation_timer.stop()
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_slider)
        self.animation_timer.start(10)  # 启动动画定时器
        self.animation_repeat_count = 0

    def animate_slider(self):
        if self.slider_position < self.target_position and self.animation_repeat_count < 100:
            self.slider_position += max(0.1 * (self.target_position - self.slider_position), 1)
            self.slider_position = round(self.slider_position)
            if self.slider_position > self.target_position:
                self.slider_position = self.target_position
            self.animation_repeat_count += 1
        elif self.slider_position > self.target_position and self.animation_repeat_count < 100:
            self.slider_position += min(0.1 * (self.target_position - self.slider_position), -1)
            self.slider_position = round(self.slider_position)
            if self.slider_position < self.target_position:
                self.slider_position = self.target_position
            self.animation_repeat_count += 1
        else:
            self.slider_position = self.target_position
            self.animation_timer.stop()  # 到达目标位置，停止动画
            self.animation_timer = None
            self.animation_repeat_count = 0
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


class ColoredButton(QPushButton):
    "带背景色的圆角按钮"
    FONT_NAME = "STXINWEI"
    def __init__(
            self, text="", parent=None, 
            width=160, height=60, fontSize=10,
            bg_color=QColor(100, 100, 250), 
            hover_color=None, 
            pressed_color=None, 
            text_color=QColor(255, 255, 255), 
            onclick=lambda:None):
        super().__init__(text, parent)
        self.setFixedSize(width, height)
        self.fontSize = fontSize
        self.text_color = text_color
        self.bg_color = bg_color
        if hover_color is None:
            hover_color = bg_color.lighter(110)
        self.hover_color = hover_color
        if pressed_color is None:
            pressed_color = bg_color.darker(110)
        self.pressed_color = pressed_color
        self.onclick = onclick
        self.border_radius = height//2

        self.clicked.connect(self.onclick)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                color: rgb({self.text_color.red()}, {self.text_color.green()}, {self.text_color.blue()});
                border: none;
                border-radius: {self.border_radius}px;
                font-size: {self.fontSize}pt;
            }}
        """)
        self.current_color = self.bg_color
        self.target_color = self.bg_color
        self.color_transition_timer = None
        self.color_decay_constant = 5

    # 颜色缓变
    def enterEvent(self, event):
        self.target_color = self.hover_color
        self.color_decay_constant = 5
        self.start_color_transition()
    def leaveEvent(self, event):
        self.target_color = self.bg_color
        self.color_decay_constant = 10
        self.start_color_transition()
    def mousePressEvent(self, event):
        self.target_color = self.pressed_color
        self.color_decay_constant = 2
        self.start_color_transition()
        super().mousePressEvent(event)
    def mouseReleaseEvent(self, event):
        self.target_color = self.hover_color
        self.color_decay_constant = 10
        self.start_color_transition()
        super().mouseReleaseEvent(event)
    def start_color_transition(self):
        if self.color_transition_timer is None:
            self.color_transition_timer = QTimer()
            self.color_transition_timer.timeout.connect(self.update_color)
            self.color_transition_timer.start(30)
    def update_color(self):
        r_diff = self.target_color.red() - self.current_color.red()
        g_diff = self.target_color.green() - self.current_color.green()
        b_diff = self.target_color.blue() - self.current_color.blue()
        d_red = round(r_diff/self.color_decay_constant)
        d_green = round(g_diff/self.color_decay_constant)
        d_blue = round(b_diff/self.color_decay_constant)

        if d_red == 0 and d_green == 0 and d_blue == 0:
            self.current_color = self.target_color
            self.color_transition_timer.stop()
            self.color_transition_timer = None
        else:
            new_r = self.current_color.red() + d_red
            new_g = self.current_color.green() + d_green
            new_b = self.current_color.blue() + d_blue
            self.current_color = QColor(new_r, new_g, new_b)

        self.update()  # 触发重绘

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制背景
        painter.setBrush(self.current_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), self.border_radius, self.border_radius)

        # 绘制文本
        painter.setPen(self.text_color)
        font = QFont(self.FONT_NAME)
        font.setPointSize(self.fontSize)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())

        painter.end()

    
if __name__ == "__main__":
    from main_window import MainWindow, BackgroundWidget, WidgetBox
    from start_check import check_started
    BackgroundWidget.IMAGE_PATH = os.path.join(os.path.dirname(__file__), "test_image.png")
    app = QApplication(sys.argv)
    check_started()
    MainWindow.TITLE = "Switches Test"
    window = MainWindow(app=app)
    window.addWidget(WidgetBox(
        window, 
        title="Switch Buttons",
        widgets=[SwitchButton(
            onchange=lambda state: print("State changed to", state),
            onturnon=lambda: print("Turned ON"),
            onturnoff=lambda: print("Turned OFF")
        ), 
        SwitchButton()
        ]
    ))
    window.addWidget(WidgetBox(
        window,
        title="Colored Buttons",
        widgets=[
        ColoredButton(
            text="Colored Button #1",
            width=240,
            bg_color=QColor(100, 200, 100), 
            onclick=lambda: print("Colored Button #1 Clicked")
        ), ColoredButton(
            text="Colored Button #2",
            width=240,
            bg_color=QColor(200, 100, 150),
            onclick=lambda: print("Colored Button #2 Clicked")
        ), 
        ColoredButton(
            text="Colored Button #3",
            width=240,
            bg_color=QColor(150, 100, 200), 
            onclick=lambda: print("Colored Button #3 Clicked")
        )
        ]
    ))
    window.show()
    sys.exit(app.exec_())

