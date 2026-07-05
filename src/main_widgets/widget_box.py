from basic_settings import *


class PlainText(QLabel):
    def __init__(self, text:str="", parent:QWidget=None):
        super().__init__(parent)
        self.setText(text)
        self.setFont(QFont(SETTINGS.font_name, SETTINGS.font_size))
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setWordWrap(True)
        self.setStyleSheet(f"color: {SETTINGS.colors.text_color};")


class WidgetBox(QWidget):
    "一个盒子，里面可以自定义布局放置元素。盒子边界为圆角矩形，上边界中央显示标题"
    def __init__(self, parent:QWidget, title:str="WidgetBox", widgets:list[QWidget]=[]):
        super().__init__(parent=parent)
        self.master=parent
        self.main_layout=QVBoxLayout(self)
        self.title=QLabel(title, self)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont(SETTINGS.font_name, SETTINGS.font_size_large, QFont.Bold))
        self.title.setStyleSheet(f"color: {SETTINGS.colors.text_color};")
        self.main_layout.addWidget(self.title)
        if widgets:
            for widget in widgets:
                self.add(widget)

    def add(self, *widgets:QWidget|QLayout):
        "添加一个或多个组件或者布局元素。支持链式调用"
        for widget in widgets:
            if isinstance(widget, QWidget):
                self.main_layout.addWidget(widget)
            elif isinstance(widget, QLayout):
                self.main_layout.addLayout(widget)
            else:
                raise TypeError("widget must be a QWidget or QLayout")
        return self
        
    def addLine(self, *widgets:QWidget|None):
        "在盒子内添加一行组件，组件水平排列。"
        if all(w is None for w in widgets):
            return self
        line_layout = QHBoxLayout()
        for widget in widgets:
            if widget is None:
                continue
            line_layout.addWidget(widget)
        self.main_layout.addLayout(line_layout)
        return _AddLineResult(self, widgets, [line_layout])

    # 绘制边框和圆角
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制边框
        pen = QPen(Qt.gray, 2)
        painter.setPen(pen)
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, SETTINGS.geometry.widgetbox_border_radius, SETTINGS.geometry.widgetbox_border_radius)

        painter.end()

    # 捕获子类构造函数可能的报错，防止模块崩溃导致整个程序崩溃
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # __init__装饰器
        def init_wrapper(init_func):
            def wrapped_init(self, *args, **kwargs):
                try:
                    init_func(self, *args, **kwargs)
                except Exception as e:
                    with open(SETTINGS.paths.error_log_file, "a+", encoding="utf-8") as f:
                        f.write(f"Error in {cls.__name__}.__init__:\n")
                        f.write(traceback.format_exc())
                        f.write("\n\n")
                    # 调用父类构造函数，保证基本的UI结构被创建出来
                    try:
                        super(cls, self).__init__(*args, **kwargs)
                    except Exception as e:
                        raise RuntimeError(f"Failed to initialize base WidgetBox for {cls.__name__}") from e
                    # 覆盖各个方法
                    self.add = lambda *a, **k: None
                    self.addLine = lambda *a, **k: None
                    old_paintEvent = self.paintEvent
                    def new_paintEvent(event):
                        try:
                            old_paintEvent(event)
                        except Exception as e:
                            # 因为初始化失败，我们预期paintEvent也会无法正常工作。
                            return # 忽略次级异常
                    self.paintEvent = new_paintEvent
                    # 尝试显示错误信息
                    try:
                        error_label = QLabel("Error", self)
                        error_label.setStyleSheet(f"color: red; max-width: 300px; white-space: pre-wrap;")
                        error_label.setAlignment(Qt.AlignCenter)
                        self.main_layout.addWidget(error_label)
                    except Exception as e:
                        pass # 如果连显示错误信息都失败了，那就算了
            return wrapped_init
        cls.__init__ = init_wrapper(cls.__init__)
        


class _AddLineResult:
    def __init__(self, box:WidgetBox, elements:list[QWidget], lines:list[QLayout]):
        self.box = box
        self.elements = list(elements)
        self.lines = list(lines)

    def add(self, widget):
        self.box.add(widget)
        self.elements.append(widget)
        return self
    
    def addLine(self, *widgets:QWidget|None):
        if all(w is None for w in widgets):
            return self
        new_result = self.box.addLine(*widgets)
        self.elements.extend(new_result.elements)
        self.lines.extend(new_result.lines)
        return self
