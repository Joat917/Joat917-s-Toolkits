from base_import import *

class PopupWindow(QWidget):
    WINDOW_WIDTH = 300
    WINDOW_HEIGHT = 100
    def __init__(self):
        super().__init__()
        self.resize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

    def show_popup(self):
        self.show()

class InformationPopup(PopupWindow):
    def __init__(self, message, title="Information"):
        super().__init__()
        self.setWindowTitle(title)

        self.label = QLabel(message, self)
        self.label.setWordWrap(True)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.close)

        # 一行文字，最后一行居中显示按钮
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.ok_button, alignment=Qt.AlignCenter)
        self.setLayout(self.layout)

class ConfirmationPopup(PopupWindow):
    def __init__(self, message, title="Confirmation", callback=lambda response: None):
        super().__init__()
        self.setWindowTitle(title)
        self.callback = callback
        self.user_response = None
        
        self.label = QLabel(message, self)
        self.label.setWordWrap(True)

        self.yes_button = QPushButton("Yes")
        self.yes_button.clicked.connect(self.yes_clicked)
        self.no_button = QPushButton("No")
        self.no_button.clicked.connect(self.no_clicked)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.yes_button)
        button_layout.addWidget(self.no_button)
        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)


    def yes_clicked(self):
        self.user_response = True
        # run callback in main thread
        self.callback(self.user_response)
        self.close()

    def no_clicked(self):
        self.user_response = False
        self.callback(self.user_response)
        self.close()


class FadingPopup(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setupUi(text)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool| Qt.WindowStaysOnTopHint)  # 无边框且保持在顶部
        self.setAttribute(Qt.WA_TranslucentBackground)  # 背景透明

        self.animation = QPropertyAnimation(self, b"pos")
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.timer = QTimer(self)

        self.initAnimations()

    def setupUi(self, text):
        layout = QVBoxLayout(self)
        self.label = QLabel(text)
        palette = self.label.palette()
        palette.setColor(QPalette.WindowText, Qt.white)
        self.label.setPalette(palette)
        self.label.setStyleSheet(
            "background-color: #ddd; border-radius: 20px; padding: 10px; color: #222; font-size: 36px"
        )
        layout.addWidget(self.label)
        self.setLayout(layout)

    def initAnimations(self):
        self.animation.setDuration(500)
        self.opacity_animation.setDuration(500)
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(0.7)
        self.opacity_animation.finished.connect(self.startHideTimer)

    def startHideTimer(self):
        self.timer.singleShot(3000, self.fadeOut)

    def fadeIn(self):
        screen_geometry = QApplication.desktop().screenGeometry()
        self.show()

        window_width = self.width()
        window_height = self.height()
        x_position = (screen_geometry.width() - window_width) // 2
        y_position = round(screen_geometry.height() * 0.8 - window_height)
        self.move(x_position, screen_geometry.height())
        self.setWindowOpacity(0.0)
        self.animation.setStartValue(
            QPoint(x_position, screen_geometry.height()))
        self.animation.setEndValue(QPoint(x_position, y_position))
        self.animation.start()
        self.opacity_animation.start()

    def fadeOut(self):
        self.opacity_animation.setDirection(QPropertyAnimation.Backward)
        self.opacity_animation.start()
        self.opacity_animation.finished.connect(self.close)

