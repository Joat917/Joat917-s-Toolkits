from basic_settings import *
from main_widgets import MainWindow, WidgetBox, PlainText, SwitchButton


class KeyDisplay(QWidget):
    X_L = SETTINGS.c1124_X_L
    Y_R = SETTINGS.c1124_Y_R
    margin = SETTINGS.c1124_margin
    padding = SETTINGS.c1124_padding
    borderRadius = SETTINGS.c1124_borderRadius
    opacity = SETTINGS.c1124_opacity
    main_color = SETTINGS.c1124_main_color
    _font = QFont(SETTINGS.font_name, SETTINGS.c1124_font_size)
    _fontMetrics = QFontMetrics(_font)

    def __init__(self, pos, text='Sample Text', manager=None):
        super().__init__()
        self.setFont(KeyDisplay._font)

        width, height=self.getSize(text)
        x,y=pos
        self.color = self.main_color
        self.text = text
        self.manager=manager
        self.radius=min(self.borderRadius, width//2)

        self.setGeometry(x, y, width, height)
        self.setFont(KeyDisplay._font)
        self.setStyleSheet(f"color: black; background-color: transparent; text-align: center;line-height: {height}; border-radius: {self.radius};")
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.label = QLabel(text, self)
        self.label.setFont(KeyDisplay._font)
        self.label.setGeometry(0,0,width, height)
        self.label.setStyleSheet(f"background-color: {self.color};")
        self.label.setAlignment(Qt.AlignCenter)

        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(self.opacity)
        
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        QTimer.singleShot(SETTINGS.c1124_check_existence_interval, self.checkExistence)

        self.animation_level=0
        self.animation=None
        self.animation2=None

    def setColor(self, newColor=None):
        self.color=newColor if newColor is not None else SETTINGS.c1124_sub_color
        self.label.setStyleSheet(f"background-color: {self.color};")

    def delayedFadeOut(self):
        self.animation_level+=1
        x=self.animation_level
        QTimer.singleShot(SETTINGS.c1124_fadeout_delay, lambda:self.fade_out(x))

    def fade_out(self, targeted_level:int):
        if targeted_level<self.animation_level:
            return
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(SETTINGS.c1124_fadeout_animation_duration)
        self.animation.setStartValue(self.opacity)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.Linear)
        self.animation.finished.connect(self.close)
        self.animation.start()

    def move_to(self, new_pos):
        new_x, new_y=new_pos
        end_point = QPoint(new_x, new_y)
        if self.pos()==end_point:
            return
        self.animation2 = QPropertyAnimation(self, b"pos")
        self.animation2.setDuration(SETTINGS.c1124_move_duration)
        self.animation2.setStartValue(self.pos())
        self.animation2.setEndValue(end_point)
        self.animation2.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation2.start()

    def close(self):
        if self.animation is not None:
            self.animation.stop()
            self.animation.deleteLater()
            self.animation = None
        if self.animation2 is not None:
            self.animation2.stop()
            self.animation2.deleteLater()
            self.animation2 = None
        self.animation_level=float('inf')
        if self.manager is not None:
            self.manager._kill(self)
            self.manager = None
        try:
            self.deleteLater()
        except RuntimeError:
            pass
        super().close()

    def checkExistence(self):
        if self.manager is None or self.manager.master is None:
            self.close()
            self.deleteLater()
            return
        QTimer.singleShot(SETTINGS.c1124_check_existence_interval, self.checkExistence)

    @classmethod
    def distribute_places(cls, boxes:list[tuple[int,int]]):
        "Arrange the boxes left to right and top to bottom"
        lineIndex=0
        lineHeights=[0]
        xOffset=0
        xLineList=[]
        for x,y in boxes:
            wid_required=x+2*cls.margin
            assert wid_required<=cls.width_tot
            if wid_required>cls.width_tot-xOffset:
                lineIndex+=1
                lineHeights.append(0)
                assert len(lineHeights)==lineIndex+1
                xOffset=0
            xLineList.append((xOffset, lineIndex))
            lineHeights[lineIndex]=max(lineHeights[lineIndex], y)
            xOffset+=x+cls.margin
        yList=[0]
        for lh in lineHeights:
            yList.append(yList[-1]+lh+cls.margin)
        out=[]
        for x,i in xLineList:
            out.append((x+cls.margin, yList[i]+cls.margin))
        return out

    @classmethod
    def getSize(cls, text):
        return (
            round(cls._fontMetrics.horizontalAdvance(text)*SETTINGS.c1124_font_horizontal_scale+2*cls.padding),
            round(cls._fontMetrics.height()*SETTINGS.c1124_font_vertical_scale+2*cls.padding)
        )

    @classmethod
    def coordMap(cls, coord0):
        return (cls.base_x+coord0[0], 
                cls.base_y-coord0[1]-cls._fontMetrics.height()-cls.margin)


class KeyDisplayerManager(QObject):
    def __init__(self, master:MainWindow):
        super().__init__()
        self.master = master

        KeyDisplay.screen_geometry = screen_geometry = QApplication.desktop().screenGeometry()
        KeyDisplay.screen_x=screen_geometry.width()
        KeyDisplay.screen_y=screen_geometry.height()
        KeyDisplay.base_x = int(screen_geometry.width() * KeyDisplay.X_L)
        KeyDisplay.base_y = int(screen_geometry.height() * KeyDisplay.Y_R)
        KeyDisplay.width_tot=screen_geometry.width()-KeyDisplay.base_x
        KeyDisplay.height_tot=screen_geometry.height()-KeyDisplay.base_y

        if self.master.globalKeyboardListener is not None:
            self.master.globalKeyboardListener.press_callbacks.append(self.callbackPress)
            self.master.globalKeyboardListener.release_callbacks.append(self.callbackRelease)
        self.master.trayWidget.add_action("Key&Mouse: Release All", self.releaseAll)
        self.master.trayWidget.add_action("Key&Mouse: Remove All", self.removeAll)

        self.displays=[]
        self.boxes=[]
        self.texts=[]
        self.textCount={}

        self._newText('Key&Mouse')
        pass

    def callbackPress(self, text):
        self.textCount[text]=self.textCount.get(text, 0)+1
        if text in self.texts:
            ind=self.texts.index(text)
            self._stopCountDown(ind)
        else:
            self._newText(text)

    def callbackRelease(self, text):
        time.sleep(SETTINGS.c1124_release_event_delay)
        if text in self.texts:
            ind=self.texts.index(text)
            self._countDown(ind)

    def _newText(self, text):
        ind=len(self.texts)
        self.texts.append(text)
        self.boxes.append(KeyDisplay.getSize(text))
        new_places=KeyDisplay.distribute_places(self.boxes)
        self.displays.append(KeyDisplay(KeyDisplay.coordMap(new_places[-1]), text=text, manager=self))
        self._reSort()
        self.displays[-1].show()

    def _countDown(self, ind):
        self.displays[ind].delayedFadeOut()
        self.displays[ind].setColor()

    def _stopCountDown(self, ind):
        self.displays[ind].setColor(KeyDisplay.main_color)
        self.displays[ind].animation_level+=1
        try:
            self.displays[ind].animation.stop()
            self.displays[ind].opacity_effect.setOpacity(KeyDisplay.opacity)
        except AttributeError:
            pass

    def _kill(self, obj:KeyDisplay):
        try:
            ind=self.displays.index(obj)
        except ValueError:
            return
        self.displays.pop(ind)
        self.boxes.pop(ind)
        self.texts.pop(ind)
        self._reSort()

    def _reSort(self):
        self._reArrange()

    def _reArrange(self):
        places=KeyDisplay.distribute_places(self.boxes)
        for i in range(len(self.boxes)):
            self.displays[i].move_to(KeyDisplay.coordMap(places[i]))

    def close(self):
        for display in self.displays:
            display.close()
        self.displays.clear()
        self.boxes.clear()
        self.texts.clear()

        if self.master.globalKeyboardListener is not None:
            self.master.globalKeyboardListener.press_callbacks.remove(self.callbackPress)
            self.master.globalKeyboardListener.release_callbacks.remove(self.callbackRelease)
        self.master.trayWidget.remove_action("Key&Mouse: Release All")
        self.master.trayWidget.remove_action("Key&Mouse: Remove All")
        self.master = None
        try:
            self.deleteLater()
        except RuntimeError:
            pass


    def releaseAll(self):
        for i in range(1, len(self.texts)):
            self._countDown(i)

    def removeAll(self):
        for i in range(len(self.texts)-1, 0, -1):
            self.displays[i].close()

class KeyDisplayerWidget(WidgetBox):
    def __init__(self, master:MainWindow):
        super().__init__(parent=master, title="Key&Mouse Displayer")
        self.keydisplayer_manager=None
        self.toggle_button = SwitchButton(
            onturnon=self.enable_keydisplayer, 
            onturnoff=self.disable_keydisplayer
        )
        self.status_label = PlainText(
            text="Disabled",
            parent=self
        )
        self.sublayout = QHBoxLayout()
        self.sublayout.addWidget(self.toggle_button)
        self.sublayout.addWidget(self.status_label)
        self.layout.addLayout(self.sublayout)

    def enable_keydisplayer(self):
        if self.keydisplayer_manager is not None:
            self.disable_keydisplayer()
        self.keydisplayer_manager=KeyDisplayerManager(self.master)
        self.status_label.setText("Enabled")

    def disable_keydisplayer(self):
        if self.keydisplayer_manager is not None:
            self.keydisplayer_manager.close()
            self.keydisplayer_manager=None
        self.status_label.setText("Disabled")

