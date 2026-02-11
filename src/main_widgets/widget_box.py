from basic_settings import *


class PlainText(QLabel):
    def __init__(self, text:str="", parent:QWidget=None):
        super().__init__(parent)
        self.setText(text)
        self.setFont(QFont(SETTINGS.font_name, SETTINGS.font_size))
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setWordWrap(True)
        self.setStyleSheet(f"color: {SETTINGS.text_color};")


class WidgetBox(QWidget):
    "一个盒子，里面可以自定义布局放置元素。盒子边界为圆角矩形，上边界中央显示标题"
    def __init__(self, parent:QWidget, title:str="WidgetBox", widgets:list[QWidget]=[]):
        super().__init__(parent=parent)
        self.master=parent
        self.main_layout=QVBoxLayout(self)
        self.title=QLabel(title, self)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont(SETTINGS.font_name, SETTINGS.font_size_large, QFont.Bold))
        self.title.setStyleSheet(f"color: {SETTINGS.text_color};")
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
        
    def addLine(self, *widgets:QWidget):
        "在盒子内添加一行组件，组件水平排列。"
        line_layout = QHBoxLayout()
        for widget in widgets:
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
        painter.drawRoundedRect(rect, SETTINGS.widgetbox_border_radius, SETTINGS.widgetbox_border_radius)

        painter.end()


class _AddLineResult:
    def __init__(self, box:WidgetBox, elements:list[QWidget], lines:list[QLayout]):
        self.box = box
        self.elements = list(elements)
        self.lines = list(lines)

    def add(self, widget):
        self.box.add(widget)
        self.elements.append(widget)
        return self
    
    def addLine(self, *widgets):
        new_result = self.box.addLine(*widgets)
        self.elements.extend(new_result.elements)
        self.lines.extend(new_result.lines)
        return self
