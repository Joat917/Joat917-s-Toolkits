from basic_settings import *

def robustify_0arg(func):
    def wrapper():
        try:
            return func()
        except Exception as e:
            err_info = f"Exception in {func.__name__}: {e}\n"
            err_info += traceback.format_exc()
            print(err_info)
            with open(SETTINGS.error_log_file, "a+", encoding="utf-8") as f:
                f.write(err_info)
                f.write("\n\n")
    return wrapper

def robustify_1arg(func):
    def wrapper(arg):
        try:
            return func(arg)
        except Exception as e:
            err_info = f"Exception in {func.__name__}: {e}\n"
            err_info += traceback.format_exc()
            print(err_info)
            with open(SETTINGS.error_log_file, "a+", encoding="utf-8") as f:
                f.write(err_info)
                f.write("\n\n")
    return wrapper

class SwitchButton(QLabel):
    "长圆形开关，背景灰色或蓝色。包含一个白色圆形滑块可以左右滑动切换状态。"
    def __init__(self, parent=None, onchange=lambda state:None, onturnon=lambda:None, onturnoff=lambda:None):
        super().__init__(parent)
        self.setFixedSize(2*SETTINGS.switchbutton_size, SETTINGS.switchbutton_size)
        self.setCursor(Qt.PointingHandCursor)
        self.state = False  # 初始状态为关闭
        self.slider_position = SETTINGS.switchbutton_padding  # 滑块初始位置
        self.animation_timer = None
        self.animation_repeat_count = 0
        self.target_position = SETTINGS.switchbutton_padding  # 目标位置
        self.onchange = robustify_1arg(onchange)
        self.onturnon = robustify_0arg(onturnon)
        self.onturnoff = robustify_0arg(onturnoff)

        # self._old_under_mouse = False

    def mousePressEvent(self, event):
        self.state = not self.state  # 切换状态
        self.onchange(self.state)
        if self.state:
            self.onturnon()
            self.target_position = self.width() - (SETTINGS.switchbutton_size-SETTINGS.switchbutton_padding)  # 打开状态滑块位置
        else:
            self.onturnoff()
            self.target_position = SETTINGS.switchbutton_padding  # 关闭状态滑块位置
        if self.animation_timer is not None:
            self.animation_timer.stop()
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_slider)
        self.animation_timer.start(SETTINGS.switchbutton_animation_interval)  # 启动动画定时器
        self.animation_repeat_count = 0

    def animate_slider(self):
        if self.slider_position < self.target_position and self.animation_repeat_count < SETTINGS.switchbutton_animation_max_steps:
            self.slider_position += max(SETTINGS.switchbutton_animation_K * (self.target_position - self.slider_position), 1)
            self.slider_position = round(self.slider_position)
            if self.slider_position > self.target_position:
                self.slider_position = self.target_position
            self.animation_repeat_count += 1
        elif self.slider_position > self.target_position and self.animation_repeat_count < SETTINGS.switchbutton_animation_max_steps:
            self.slider_position += min(SETTINGS.switchbutton_animation_K * (self.target_position - self.slider_position), -1)
            self.slider_position = round(self.slider_position)
            if self.slider_position < self.target_position:
                self.slider_position = self.target_position
            self.animation_repeat_count += 1
        else:
            self.slider_position = self.target_position
            self.animation_timer.stop()  # 到达目标位置，停止动画
            self.animation_timer.timeout.disconnect()
            self.animation_timer.deleteLater()
            self.animation_timer = None
            self.animation_repeat_count = 0
        self.update()  # 触发重绘

    @property
    def alpha(self):
        # if self.underMouse():
        #     return 255
        return SETTINGS.switchbutton_alpha
    
    # def mouseMoveEvent(self, ev):
    #     if self._old_under_mouse != self.underMouse():
    #         self._old_under_mouse = self.underMouse()
    #         self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制背景
        if self.state:
            painter.setBrush(QColor(*SETTINGS.switchbutton_oncolor_tuple, self.alpha))
        else:
            painter.setBrush(QColor(*SETTINGS.switchbutton_offcolor_tuple, self.alpha))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), SETTINGS.switchbutton_size//2, SETTINGS.switchbutton_size//2)

        # 绘制滑块
        painter.setBrush(QColor(*SETTINGS.switchbutton_slidercolor_tuple, self.alpha))  # 白色滑块
        painter.drawEllipse(self.slider_position, SETTINGS.switchbutton_padding, SETTINGS.switchbutton_size-2*SETTINGS.switchbutton_padding, SETTINGS.switchbutton_size-2*SETTINGS.switchbutton_padding)
        painter.end()


class PushButton(QPushButton):
    "带背景色的圆角按钮"
    def __init__(
            self, text="", 
            *, 
            parent=None, 
            width=None, 
            height=SETTINGS.pushbutton_height, 
            fontSize=None,
            bg_color=QColor(SETTINGS.pushbutton_default_bgcolor), 
            hover_color=None, 
            pressed_color=None, 
            text_color=QColor(SETTINGS.pushbutton_default_fgcolor), 
            alpha = SETTINGS.pushbutton_alpha, 
            onclick=lambda:None):
        super().__init__(text, parent)

        self.fontSize = fontSize if fontSize is not None else SETTINGS.font_size
        self.setFont(QFont(SETTINGS.font_name, self.fontSize))
        if width is None:
            fm = QFontMetrics(self.font())
            text_width = fm.horizontalAdvance(text)
            width = text_width + round(height*0.75)  # 根据文本宽度和按钮高度计算总宽度，保证按钮足够大以容纳文本
        
        self.setFixedSize(width, height)
        self.text_color = QColor(text_color)
        self.bg_color = QColor(bg_color)
        if hover_color is None:
            hover_color = bg_color.lighter(SETTINGS.pushbutton_hoverlighter)
        self.hover_color = hover_color
        if pressed_color is None:
            pressed_color = bg_color.darker(SETTINGS.pushbutton_presseddarker)
        self.pressed_color = pressed_color
        self.bg_color.setAlpha(min(alpha, self.bg_color.alpha()))
        self.onclick = onclick
        self.border_radius = height//2

        self.clicked.connect(robustify_0arg(self.onclick))
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                color: rgba({self.text_color.red()}, {self.text_color.green()}, {self.text_color.blue()}, {self.text_color.alpha()});
                border: none;
                border-radius: {self.border_radius}px;
                font-size: {self.fontSize}pt;
            }}
        """)
        self.current_color = self.bg_color
        self.target_color = self.bg_color
        self.color_transition_timer = None
        self.color_decay_constant = SETTINGS.pushbutton_colordecay_mouseenter

    # 颜色缓变
    def enterEvent(self, event):
        self.target_color = self.hover_color
        self.color_decay_constant = SETTINGS.pushbutton_colordecay_mouseenter
        self.start_color_transition()
    def leaveEvent(self, event):
        self.target_color = self.bg_color
        self.color_decay_constant = SETTINGS.pushbutton_colordecay_mouseleave
        self.start_color_transition()
    def mousePressEvent(self, event):
        self.target_color = self.pressed_color
        self.color_decay_constant = SETTINGS.pushbutton_colordecay_mousepress
        self.start_color_transition()
        super().mousePressEvent(event)
    def mouseReleaseEvent(self, event):
        self.target_color = self.hover_color
        self.color_decay_constant = SETTINGS.pushbutton_colordecay_mouserelease
        self.start_color_transition()
        super().mouseReleaseEvent(event)
    def start_color_transition(self):
        if self.color_transition_timer is None:
            self.color_transition_timer = QTimer()
            self.color_transition_timer.timeout.connect(self.update_color)
            self.color_transition_timer.start(SETTINGS.pushbutton_colordecay_interval)
    def update_color(self):
        r_diff = self.target_color.red() - self.current_color.red()
        g_diff = self.target_color.green() - self.current_color.green()
        b_diff = self.target_color.blue() - self.current_color.blue()
        a_diff = self.target_color.alpha() - self.current_color.alpha()
        d_red = round(r_diff/self.color_decay_constant)
        d_green = round(g_diff/self.color_decay_constant)
        d_blue = round(b_diff/self.color_decay_constant)
        d_alpha = round(a_diff/self.color_decay_constant)

        if d_red == 0 and d_green == 0 and d_blue == 0:
            self.current_color = self.target_color
            self.color_transition_timer.stop()
            self.color_transition_timer.timeout.disconnect()
            self.color_transition_timer.deleteLater()
            self.color_transition_timer = None
        else:
            new_r = self.current_color.red() + d_red
            new_g = self.current_color.green() + d_green
            new_b = self.current_color.blue() + d_blue
            new_a = self.current_color.alpha() + d_alpha
            self.current_color = QColor(new_r, new_g, new_b, new_a)

        self.update()  # 触发重绘

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制背景
        painter.setBrush(self.current_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), self.border_radius, self.border_radius)

        # 绘制文本
        painter.setFont(self.font())
        painter.setPen(self.text_color)
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())

        painter.end()

    @staticmethod
    def color_shorthand(x):
        """
        使用一个三位整数描述一个颜色，每一位对应一个颜色通道。
        每一位取0-4，分别对应0,100,150,200,250

        这样做的好处是可以非常简洁地描述一个颜色，大幅缩小颜色空间，避免不必要的复杂度。
        建议取数位之和为6-8。
        """
        def digit_to_color(digit, channel_name):
            try:
                return [0, 100, 150, 200, 250][digit]
            except IndexError as exc:
                raise ValueError(f"Invalid digit '{digit}' in color shorthand '{x}' for channel {channel_name}. Must be 0-4.") from exc
        if not isinstance(x, int):
            raise ValueError(f"Color shorthand must be an integer, got {type(x).__name__}.")
        if x < 0:
            raise ValueError(f"Color shorthand must be a non-negative integer, got {x}.")
        if x > 999:
            raise ValueError(f"Color shorthand must be at most three digits, got {x}.")
        r = digit_to_color((x // 100) % 10, 'red')
        g = digit_to_color((x // 10) % 10, 'green')
        b = digit_to_color(x % 10, 'blue')
        return QColor(r, g, b)
        
