from base_import import *
from popup_window import FadingPopup
from keyboard_listener import KeyboardListenerSignalPatched as KeyboardListener

class MainWindow(QWidget):
    # 大小和停靠位置参数
    WIDTH = SETTINGS.window_width
    HEIGHT = SETTINGS.window_height
    PADDING = SETTINGS.window_padding
    K=SETTINGS.window_animation_K # 回弹系数
    R=SETTINGS.window_animation_R # 回弹半径
    TOTAL_ANIMATION_FRAMES = SETTINGS.window_animation_frames
    TOTAL_ANIMATION_TIME_MS = SETTINGS.window_animation_time_ms
    def __init__(self, app:QApplication):
        super().__init__()
        self.app=app

        # 停靠在屏幕右上角
        screen_geometry = QApplication.primaryScreen().geometry()
        self.position_1 = QPoint(screen_geometry.width()-self.WIDTH-self.PADDING, self.PADDING)
        self.position_2 = QPoint(screen_geometry.width()-self.PADDING, self.PADDING)
        self.setGeometry(self.position_1.x(), self.position_1.y(), self.WIDTH, self.HEIGHT)

        self.setAcceptDrops(True)
        self.setWindowTitle(SETTINGS.window_title)
        self.setStyleSheet("background-color: transparent;")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.bgwidget=BackgroundWidget(self)
        self.trayWidget=TrayIconWidget(self)

        # self.globalKeyboardListener = None
        self.globalKeyboardListener=KeyboardListener(press_callbacks=[], release_callbacks=[], parent=self, auto_start=True)
        self.globalKeyboardListener.press_callbacks.append(self._globalHotkeyHandler)
        self.hotkey_callbacks = {} # name: callback

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        content_widget = QWidget(scroll)
        scroll.setWidget(content_widget)
        scroll.viewport().installEventFilter(self) # 捕获横向滚轮（触摸板/鼠标）事件，交给 MainWindow 处理
        scroll.verticalScrollBar().setContextMenuPolicy(Qt.NoContextMenu)
        # 圆形滚动条样式
        scroll.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                background: transparent;
                width: %dpx;
                margin: 0px 0px 0px 0px;
                border-radius: %dpx;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 150);
                min-height: %dpx;
                border-radius: %dpx;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """ % (
            SETTINGS.window_scrollbar_width,
            SETTINGS.window_scrollbar_width // 2,
            SETTINGS.window_scrollbar_min_height,
            SETTINGS.window_scrollbar_width // 2
        ))

        self.layout = QVBoxLayout(content_widget)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(scroll)

        self.widgets = []
        self.messages = queue.Queue()
        self.timer = QTimer(self)
        self.timer.singleShot(SETTINGS.window_checkmessage_interval, self.checkMessage)
        self.timer.singleShot(SETTINGS.window_checkapp_interval, self.checkApp)

        self.hidden=False # 是否收缩进屏幕右侧

        self.drag_position = None # 鼠标拖动位置相对窗口左上角的偏移
        self._mouse_animation_timer = None # 窗口位置动画定时器
        self._mouse_animation_countleft = 0 # 鼠标拖动动画剩余帧数
        
        self._keyboard_moving_timer = None # 非鼠标导致窗口隐藏状态发生更改的动画
        self._keyboard_moving_countleft = 0 # 键盘隐藏动画剩余帧数

    def addWidget(self, widget):
        self.layout.addWidget(widget)
        widget.show()
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
        if a0.key() == SETTINGS.window_exitkey_code:
            self.trayWidget.exit()
        
    def _globalHotkeyHandler(self, key_str):
        if key_str == SETTINGS.window_toggleshowkey:
            self.refreshHiddenState(not self.hidden)
        for callback in self.hotkey_callbacks.values():
            try:
                callback(key_str)
            except Exception as e:
                message=f"Error in hotkey callback: {e}"
                warnings.warn(message)
                if hasattr(self, 'droprunner'):
                    self.droprunner.push_message()
        
    def contextMenuEvent(self, a0):
        self.trayWidget.tray_icon.contextMenu().exec_(a0.globalPos())

    # 可以拖动，但是总是试图回到停靠位置
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            self._stop_moving_animation()
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

    def _stop_moving_animation(self, *, stopmouse=True, stopkeyboard=True):
        if stopmouse and self._mouse_animation_timer is not None:
            self._mouse_animation_timer.stop()
            self._mouse_animation_timer.timeout.disconnect()
            self._mouse_animation_timer.deleteLater()
            self._mouse_animation_timer = None
            self._mouse_animation_countleft = 0
        if stopkeyboard and self._keyboard_moving_timer is not None:
            self._keyboard_moving_timer.stop()
            self._keyboard_moving_timer.timeout.disconnect()
            self._keyboard_moving_timer.deleteLater()
            self._keyboard_moving_timer = None
            self._keyboard_moving_countleft = 0

    def _mouse_animation_step(self):
        if self.drag_position is not None: # 窗口正在被拖动
            self._stop_moving_animation()
            return
        if self._mouse_animation_countleft <= 0:
            self._settle_hidden_position()
            return
        self._mouse_animation_countleft -= 1

        current_pos = self.pos()
        target_pos = self.position_1 if not self.hidden else self.position_2
        delta = target_pos - current_pos
        distance = math.hypot(delta.x(), delta.y())
        if distance <= 2 or self._mouse_animation_countleft <= 0:
            self._settle_hidden_position()
            return
        
        # 以正弦函数轨迹移动
        # next_delta_proportion = (1-math.cos(self._mouse_animation_countleft/self.TOTAL_ANIMATION_FRAMES*(math.pi / 2)))/(1-math.cos((self._mouse_animation_countleft+1)/self.TOTAL_ANIMATION_FRAMES*(math.pi / 2)))
        # 以抛物线轨迹移动
        # next_delta_proportion = (self._mouse_animation_countleft)**2/(self._mouse_animation_countleft+1)**2
        # 以双曲函数轨迹移动
        next_delta_proportion = (math.cosh(self.K*self._mouse_animation_countleft/self.TOTAL_ANIMATION_FRAMES)-1)/(math.cosh(self.K*(self._mouse_animation_countleft+1)/self.TOTAL_ANIMATION_FRAMES)-1)
        new_pos = QPointF(target_pos.x() - delta.x() * next_delta_proportion,
                          target_pos.y() - delta.y() * next_delta_proportion).toPoint()
        self.move(new_pos)

    def mouseReleaseEvent(self, event):
        self.drag_position = None
        if self.hidden:
            self.hidden = False
        elif self.pos().x() > self.position_1.x() + self.WIDTH / 6:
            self.hidden = True
        self._stop_moving_animation()
        self._mouse_animation_timer = QTimer(self)
        self._mouse_animation_timer.timeout.connect(self._mouse_animation_step)
        self._mouse_animation_countleft = self.TOTAL_ANIMATION_FRAMES
        self._mouse_animation_timer.start(self.TOTAL_ANIMATION_TIME_MS//self.TOTAL_ANIMATION_FRAMES)
        event.accept()

    def _settle_hidden_position(self):
        self.drag_position = None
        self._stop_moving_animation()
        if self.hidden:
            self.move(self.position_2)
        else:
            self.move(self.position_1)

    def _keyboard_moving_updater(self):
        if self.drag_position is not None:
            self._stop_moving_animation()
            return
        if self._mouse_animation_timer is not None:
            self._stop_moving_animation(stopmouse=False, stopkeyboard=True)
            return
        if self._keyboard_moving_countleft <= 0:
            self._settle_hidden_position()
            return
        self._keyboard_moving_countleft -= 1

        current_pos = self.pos()
        target_pos = self.position_1 if not self.hidden else self.position_2
        delta = target_pos - current_pos
        distance = math.hypot(delta.x(), delta.y())
        # next_delta_proportion = (1-math.cos(self._keyboard_moving_countleft/self.TOTAL_ANIMATION_FRAMES*(math.pi / 2)))/(1-math.cos((self._keyboard_moving_countleft+1)/self.TOTAL_ANIMATION_FRAMES*(math.pi / 2)))
        # next_delta_proportion = (self._keyboard_moving_countleft)**2/(self._keyboard_moving_countleft+1)**2
        next_delta_proportion = (math.cosh(self.K*self._keyboard_moving_countleft/self.TOTAL_ANIMATION_FRAMES)-1)/(math.cosh(self.K*(self._keyboard_moving_countleft+1)/self.TOTAL_ANIMATION_FRAMES)-1)
        new_pos = QPointF(target_pos.x() - delta.x() * next_delta_proportion,
                          target_pos.y() - delta.y() * next_delta_proportion).toPoint()
        
        step = new_pos - current_pos
        if distance <=2 or step.isNull():
            self._settle_hidden_position()
            return
        self.move(new_pos)

    def refreshHiddenState(self, hidden: bool):
        if not hidden and self.hidden:
            self.hidden = hidden
            self.activateCallback()
        self.hidden = hidden
        self._stop_moving_animation()
        self._keyboard_moving_timer = QTimer(self)
        self._keyboard_moving_timer.timeout.connect(self._keyboard_moving_updater)
        self._keyboard_moving_countleft = self.TOTAL_ANIMATION_FRAMES
        self._keyboard_moving_timer.start(self.TOTAL_ANIMATION_TIME_MS//self.TOTAL_ANIMATION_FRAMES)

    def activateCallback(self):
        self.refreshHiddenState(False)
        self.show()
        self.activateWindow()
        self.raise_()

    def eventFilter(self, obj, event):
        # 监听安装到 scroll.viewport() 的滚轮事件，检测横向滚动
        try:
            if event.type() == QEvent.Wheel:
                delta = event.angleDelta()
                dx = delta.x()
                dy = delta.y()
                # 当横向位移明显大于纵向时，视为横向滚动输入
                if abs(dx) > abs(dy):
                    if not self.hidden and dx > 0:
                        self.refreshHiddenState(True)
                    elif self.hidden and dx < 0:
                        self.refreshHiddenState(False)
        except Exception:
            pass
        return super().eventFilter(obj, event)

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
            self.timer.singleShot(SETTINGS.window_checkmessage_interval, self.checkMessage)
        return
    
    def checkApp(self):
        if self.app is None:
            raise RuntimeError("App not found, exiting.")
        handle = self.windowHandle()
        if handle is None:
            raise RuntimeError("Window handle not found, exiting.")
        self.timer.singleShot(SETTINGS.window_checkapp_interval, self.checkApp)
    
    def closeEvent(self, a0):
        self._stop_moving_animation()
        self.hotkey_callbacks.clear()
        if self.globalKeyboardListener is not None:
            self.globalKeyboardListener.press_callbacks.clear()
            self.globalKeyboardListener.release_callbacks.clear()
            self.globalKeyboardListener.close()
            self.globalKeyboardListener.deleteLater()
        self.deleteLater()
        return super().closeEvent(a0)
    
    @property
    def isMoving(self):
        return self.drag_position is not None or (self._keyboard_moving_timer is not None)


class BackgroundWidget(QLabel):
    def __init__(self, parent:QWidget):
        super().__init__(parent)
        self.main=parent
        self.setGeometry(0, 0, self.main.width(), self.main.height())
        self.container=QLabel(self)
        self.container.setStyleSheet(f"background-color: transparent; font-size: {SETTINGS.font_size}pt; margin: {SETTINGS.window_padding}px;")
        self.setStyleSheet(f"background-color: {SETTINGS.window_default_bgcolor}; border-radius: {SETTINGS.window_border_radius}px; ")
        self.initialize()
        

    def initialize(self):
        if SETTINGS.window_bgimage_path and os.path.exists(SETTINGS.window_bgimage_path):
            pixmap = QPixmap(SETTINGS.window_bgimage_path)
            # 缩放到填满窗口并裁剪多余部分
            picwidth, picheight = pixmap.width(), pixmap.height()
            targetwidth, targetheight = self.main.width(), self.main.height()
            scale = max(targetwidth/picwidth, targetheight/picheight)
            newwidth, newheight = int(picwidth*scale), int(picheight*scale)
            pixmap = pixmap.scaled(newwidth, newheight, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            xoffset = (newwidth - targetwidth) // 2
            yoffset = (newheight - targetheight) // 2
            pixmap = pixmap.copy(xoffset, yoffset, targetwidth, targetheight)
            # 应用圆角遮罩
            mask = QPixmap(pixmap.size())
            mask.fill(Qt.transparent)
            painter = QPainter(mask)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(Qt.white)
            painter.setPen(Qt.NoPen)
            rect = QRectF(0, 0, pixmap.width(), pixmap.height())
            radius = min(pixmap.width(), pixmap.height()) * SETTINGS.window_border_radius / min(self.main.width(), self.main.height())
            painter.drawRoundedRect(rect, radius, radius)
            painter.end()
            pixmap.setMask(mask.createMaskFromColor(Qt.transparent))
            self.setPixmap(pixmap)
            self.setScaledContents(True)
        self.container.show()


    def reset_background_image(self):
        SETTINGS.load()
        path, _ = QFileDialog.getOpenFileName(
            None, 
            "Select Background Image", 
            SETTINGS.clipboard_image_save_dir, 
            "Image Files (*.png *.jpg *.bmp);;All Files (*)"
        )
        if not path:
            return
        if not os.path.isfile(path):
            warnings.warn("Selected file does not exist.")
            return
        try:
            im=Image.open(path)
            im.verify()
            im=Image.open(path)
            assert im.fp is not None, "Invalid image file."
        except Exception as e:
            warnings.warn(f"Selected file is not a valid image: {e}")
            return
        im=im.convert('RGBA')
        im.paste(Image.new('RGBA', im.size, (0,0,0,255)), (0,0), Image.new('L', im.size, SETTINGS.reset_background_image_opacity))
        save_path = os.path.join(SETTINGS.working_dir, "img", "bg_image.png")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        im.save(save_path)
        SETTINGS.custom_bgimage_path = None
        SETTINGS.save()
        self.initialize()


class WidgetBox(QWidget):
    "一个盒子，里面可以自定义布局放置元素。盒子边界为圆角矩形，上边界中央显示标题"
    def __init__(self, parent:QWidget=None, title:str="WidgetBox", widgets:list[QWidget]=[]):
        super().__init__(parent)
        self.master=parent
        self.layout=QVBoxLayout(self)
        self.title=QLabel(title, self)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont(SETTINGS.font_name, SETTINGS.font_size_large, QFont.Bold))
        self.title.setStyleSheet(f"color: {PlainText.TEXT_COLOR};")
        self.layout.addWidget(self.title)
        self.content=QWidget(self)
        self.content_layout=QVBoxLayout(self.content)
        self.layout.addWidget(self.content)
        if widgets:
            for widget in widgets:
                self.addWidget(widget)

    def addWidget(self, widget:QWidget):
        self.content_layout.addWidget(widget)
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

class PlainText(QLabel):
    TEXT_COLOR = 'white'
    def __init__(self, text:str="", parent:QWidget=None):
        super().__init__(parent)
        self.setText(text)
        self.setFont(QFont(SETTINGS.font_name, SETTINGS.font_size))
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setWordWrap(True)
        self.setStyleSheet(f"color: {self.TEXT_COLOR};")
    

class TrayIconWidget:
    def __init__(self, manager:MainWindow=None):
        self.manager=manager
        self.app = QApplication(sys.argv)

        if not os.path.exists(SETTINGS.icon_path) or not os.path.isfile(SETTINGS.icon_path):
            raise FileNotFoundError(f"Icon file not found: {SETTINGS.icon_path}")

        self.tray_icon = QSystemTrayIcon(QIcon(SETTINGS.icon_path), self.app)
        self.tray_icon.setToolTip(SETTINGS.window_title)

        menu = self.menu = QMenu()

        self.tray_actions = {}
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

        self.add_action(SETTINGS.window_title, lambda:FadingPopup(SETTINGS.window_welcome).fadeIn())
        self.add_action(f"Hide/Show({SETTINGS.window_toggleshowkey})", lambda:self.manager.refreshHiddenState(not self.manager.hidden))
        self.add_action(f"Exit({SETTINGS.window_exitkey})", self.exit)
        self.add_action("Set Background", self.manager.bgwidget.reset_background_image)
        self.add_action("Settings", SETTINGS.open_popup_file)

        self.tray_icon.show()

    def add_action(self, name:str, callback):
        action = QAction(name, self.app)
        action.triggered.connect(callback)
        self.menu.addAction(action)
        self.tray_actions[name] = action
        return action

    def remove_action(self, name:str):
        if name in self.tray_actions:
            action = self.tray_actions[name]
            self.menu.removeAction(action)
            self.tray_actions[name].deleteLater()
            self.tray_actions.pop(name)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.manager.activateCallback()

    def exit(self):
        self.app.quit()
        self.app.deleteLater()
        self.manager.close()
        self.manager.deleteLater()
        main_app=self.manager.app
        main_app.closeAllWindows()
        main_app.quit()
        print("Exiting application...")
