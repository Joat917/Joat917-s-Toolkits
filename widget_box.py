from base_import import *


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
        super().__init__(parent)
        self.master=parent
        self.layout=QVBoxLayout(self)
        self.title=QLabel(title, self)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont(SETTINGS.font_name, SETTINGS.font_size_large, QFont.Bold))
        self.title.setStyleSheet(f"color: {SETTINGS.text_color};")
        self.layout.addWidget(self.title)
        if widgets:
            for widget in widgets:
                self.addWidget(widget)

    def addWidget(self, widget:QWidget):
        self.layout.addWidget(widget)
        widget.show()

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

