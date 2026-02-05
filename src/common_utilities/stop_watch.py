from basic_settings import *
from main_widgets import WidgetBox, PlainText, SwitchButton, MainWindow, CustomMenu

# digital tube manager

DIGITS = {
    1: [1, 1, 0, 0, 0, 0, 0],
    2: [1, 0, 1, 1, 0, 1, 1],
    3: [1, 1, 1, 0, 0, 1, 1],
    4: [1, 1, 0, 0, 1, 0, 1],
    5: [0, 1, 1, 0, 1, 1, 1],
    6: [0, 1, 1, 1, 1, 1, 1],
    7: [1, 1, 0, 0, 0, 1, 0],
    8: [1, 1, 1, 1, 1, 1, 1],
    9: [1, 1, 1, 0, 1, 1, 1],
    0: [1, 1, 1, 1, 1, 1, 0],
    'H': [1, 1, 0, 1, 1, 0, 1]
}

class TubePainter:
    def __init__(self, size=128, width=24, color=(255, 255, 255, 255)):
        self.size=size
        self.width=width
        self.color=color
        self.tubeLayoutH=self.paintSingleTube()
        self.tubeLayoutV=self.tubeLayoutH.transpose(Image.Transpose.ROTATE_90)

    def paintSingleTube(self):
        color, width, size=self.color, self.width, self.size
        gap = round(width*0.9)
        image = Image.new("RGBA", (size, width), color)
        for _ in range(4):
            ImageDraw.Draw(image).polygon([(0,0),(gap, 0),(0,gap)], fill=(0,0,0,0))
            image=image.transpose(Image.Transpose.ROTATE_90)
        return image
    
    def _putTube(self, im, lefttop, vertical):
        if vertical:
            im.paste(self.tubeLayoutV, lefttop, self.tubeLayoutV.getchannel('A'))
        else:
            im.paste(self.tubeLayoutH, lefttop, self.tubeLayoutH.getchannel('A'))

    def paintdigit(self, digit: int):
        width, size=self.width, self.size
        image = Image.new("RGBA", (size, size*2), (0, 0, 0, 0))

        if DIGITS[digit][0]:
            self._putTube(image, (size-width, width//4), 1)
        if DIGITS[digit][1]:
            self._putTube(image, (size-width, size-width//4), 1)
        if DIGITS[digit][2]:
            self._putTube(image, (0, 2*size-width), 0)
        if DIGITS[digit][3]:
            self._putTube(image, (0, size-width//4), 1)
        if DIGITS[digit][4]:
            self._putTube(image, (0, width//4), 1)
        if DIGITS[digit][5]:
            self._putTube(image, (0, 0), 0)
        if DIGITS[digit][6]:
            self._putTube(image, (0, size-width//2), 0)

        return image
    
    def paintcolon(self):
        color, width, size=self.color, self.width, self.size
        gap = width//2
        image = Image.new("RGBA", (size, size*2), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((size//2-gap, size//2-gap, size//2+gap, size//2+gap), fill=color)
        draw.rectangle((size//2-gap, size+size//2-gap, size//2+gap, size+size//2+gap), fill=color)

        return image
    
    def paintdot(self):
        color, width, size=self.color, self.width, self.size
        gap = width//2
        image = Image.new("RGBA", (size, size*2), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((size//2-gap, 2*size-width, size//2+gap, 2*size), fill=color)

        return image

    @classmethod
    def paint_and_save(cls):
        tp=TubePainter(size=SETTINGS.stopwatch_tube_length, width=SETTINGS.stopwatch_tube_width, color=SETTINGS.stopwatch_tube_color)
        for digit in DIGITS:
            tp.paintdigit(digit).save(os.path.join(SETTINGS.img_dir, f'digitTube{digit}.png'))
        tp.paintcolon().save(os.path.join(SETTINGS.img_dir, 'digitTubeC.png'))
        tp.paintdot().save(os.path.join(SETTINGS.img_dir, 'digitTubeD.png'))
        Image.new("RGBA", (tp.size, 2*tp.size), (0,0,0,0)).save(os.path.join(SETTINGS.img_dir, 'digitTubeS.png'))

class TubeReader:
    def __init__(self):
        TubePainter.paint_and_save()
        self.initialize()

    def initialize(self):
        for d in DIGITS.keys():
            if not os.path.isfile(os.path.join(SETTINGS.img_dir, f'digitTube{d}.png')):
                raise FileNotFoundError(f'Image file for digit {d} not found.')
        if not os.path.isfile(os.path.join(SETTINGS.img_dir, 'digitTubeC.png')):
            raise FileNotFoundError('Image file for colon not found.')
        if not os.path.isfile(os.path.join(SETTINGS.img_dir, 'digitTubeD.png')):
            raise FileNotFoundError('Image file for dot not found.')
        if not os.path.isfile(os.path.join(SETTINGS.img_dir, 'digitTubeS.png')):
            raise FileNotFoundError('Image file for space not found.')
        
        self.pictures={d:QPixmap(os.path.join(SETTINGS.img_dir, f'digitTube{d}.png')) for d in DIGITS.keys()}
        self.pictures[':']=QPixmap(os.path.join(SETTINGS.img_dir, 'digitTubeC.png'))
        self.pictures['.']=QPixmap(os.path.join(SETTINGS.img_dir, 'digitTubeD.png'))
        self.pictures[' ']=QPixmap(os.path.join(SETTINGS.img_dir, 'digitTubeS.png'))
        

class TubeUnit(QLabel):
    def __init__(self, parent, number:int, tubeReader:TubeReader):
        super().__init__(parent)
        self._number=number
        self._tubeReader=tubeReader
        self.setPixmap(self._tubeReader.pictures[self._number])

    def changeNumber(self, number:int):
        if number==self._number:
            return
        if isinstance(number, int) and number>=10:
            self._number='H'
        self._number=number
        self.setPixmap(self._tubeReader.pictures[self._number])

# Stopwatch Main window

class StopWatchMainWindow(QWidget):
    def __init__(self, mainWindow=None):
        super().__init__()
        self.setWindowTitle("StopWatch14")
        screen_geometry = QApplication.primaryScreen().geometry()

        _width = SETTINGS.stopwatch_size * 5
        _height = SETTINGS.stopwatch_size
        if SETTINGS.stopwatch_xpos>=0:
            xpos=SETTINGS.stopwatch_xpos
        else:
            xpos=screen_geometry.width()+SETTINGS.stopwatch_xpos-_width
        if SETTINGS.stopwatch_ypos>=0:
            ypos=SETTINGS.stopwatch_ypos
        else:
            ypos=screen_geometry.height()+SETTINGS.stopwatch_ypos-_height
        self.setGeometry(xpos, ypos, _width, _height)
        self.setWindowOpacity(SETTINGS.stopwatch_opacity)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout=QHBoxLayout()
        tubeReader=TubeReader()
        for k in tubeReader.pictures:
            tubeReader.pictures[k]=tubeReader.pictures[k].scaled(round(SETTINGS.stopwatch_size/2), SETTINGS.stopwatch_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.tubeunitsList=[
            ('h1',TubeUnit(self, 8, tubeReader)), 
            ('h0',TubeUnit(self, 8, tubeReader)), 
            ('c1',TubeUnit(self, ':', tubeReader)), 
            ('m1',TubeUnit(self, 8, tubeReader)), 
            ('m0',TubeUnit(self, 8, tubeReader)), 
            ('c0',TubeUnit(self, ':', tubeReader)), 
            ('s1',TubeUnit(self, 8, tubeReader)), 
            ('s0',TubeUnit(self, 8, tubeReader)), 
            ('c-1',TubeUnit(self, '.', tubeReader)), 
            ('s-1',TubeUnit(self, 8, tubeReader)), 
        ]
        self.tubeunitsDict=dict(self.tubeunitsList)
        for _,tu in self.tubeunitsList:
            layout.addWidget(tu)

        self.setLayout(layout)

        self._mode=0
        self._timeRecord=0

        self._timer=QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(1)

        self._tray=None
        self._action=None
        self._master=mainWindow
        if self._master is not None:
            assert isinstance(self._master, MainWindow)
            self._tray=self._master.trayWidget
            self._hotkey = SETTINGS.stopwatch_hotkey
            self._action = self._tray.add_action("Stopwatch:START"+f"({self._hotkey})", self.action)
            self._master.hotkey_callbacks[self._hotkey] = lambda key_str: self.action() if key_str == self._hotkey else None
        else:
            self._action = QAction("Stopwatch:START", self)
            self._action.triggered.connect(self.action)
            
        self._refresh(0)
        self.show()

    def action(self):
        if self._mode==0:
            self._mode=1
            self._timeRecord=time.time()
            if self._action is not None:
                self._action.setText('Stopwatch:STOP'+(f"({self._hotkey})" if self._master is not None else ''))
        elif self._mode==1:
            self._mode=2
            self._timeRecord=time.time()-self._timeRecord
            self._refresh(self._timeRecord)
            if self._action is not None:
                self._action.setText('Stopwatch:RESET'+(f"({self._hotkey})" if self._master is not None else ''))
        elif self._mode==2:
            self._mode=0
            self._timeRecord=None
            self._refresh(0)
            if self._action is not None:
                self._action.setText('Stopwatch:START'+(f"({self._hotkey})" if self._master is not None else ''))
        else:
            assert False
        return

    def _refresh(self, dt:float):
        if dt>=360000:
            dt=359999.9
        self.tubeunitsDict['h1'].changeNumber(dt//36000)
        self.tubeunitsDict['h0'].changeNumber(dt//3600%10)
        self.tubeunitsDict['m1'].changeNumber(dt%3600//600)
        self.tubeunitsDict['m0'].changeNumber(dt%3600//60%10)
        self.tubeunitsDict['s1'].changeNumber(dt%60//10)
        self.tubeunitsDict['s0'].changeNumber(dt%60//1%10)
        self.tubeunitsDict['s-1'].changeNumber(dt*10%10//1)

    def _refreshColon(self):
        if self._mode==1:
            if (time.time()-self._timeRecord)%1<=0.5:
                self.tubeunitsDict['c1'].changeNumber(':')
                self.tubeunitsDict['c0'].changeNumber(':')
                self.tubeunitsDict['c-1'].changeNumber('.')
            else:
                self.tubeunitsDict['c1'].changeNumber(' ')
                self.tubeunitsDict['c0'].changeNumber(' ')
                self.tubeunitsDict['c-1'].changeNumber(' ')
        else:
            if time.time()%1<=0.5:
                self.tubeunitsDict['c1'].changeNumber(':')
                self.tubeunitsDict['c0'].changeNumber(':')
                self.tubeunitsDict['c-1'].changeNumber('.')
            else:
                self.tubeunitsDict['c1'].changeNumber(' ')
                self.tubeunitsDict['c0'].changeNumber(' ')
                self.tubeunitsDict['c-1'].changeNumber(' ')

    def refresh(self):
        self._refreshColon()
        if self._mode!=1:
            return
        dt=time.time()-self._timeRecord
        self._refresh(dt)

    def contextMenuEvent(self, event):
        if self._action is None:
            return
        menu = CustomMenu(self)
        menu.addAction(self._action)
        menu.exec_(event.globalPos())

    def close(self):
        if self._tray is not None:
            self._tray.remove_action(self._action.text())
            self._tray = None
        if self._action is not None:
            self._action.deleteLater()
            self._action = None
        if self._master is not None:
            self._master.hotkey_callbacks.pop(self._hotkey, None)
            self._master = None
        self._timer.stop()
        self._timer.timeout.disconnect()
        self._timer.deleteLater()
        self._timer = None
        self.deleteLater()
        return super().close()


class StopWatchWidgetBox(WidgetBox):
    def __init__(self, master):
        super().__init__(parent=master, title="Stopwatch")
        self.stopwatch_mainwindow=None
        self.toggle_button = SwitchButton(
            onturnon=self.enable_stopwatch, 
            onturnoff=self.disable_stopwatch
        )
        self.status_label = PlainText(
            text="Disabled",
            parent=self
        )
        self.sublayout = QHBoxLayout()
        self.sublayout.addWidget(self.toggle_button)
        self.sublayout.addWidget(self.status_label)
        self.layout.addLayout(self.sublayout)

    def enable_stopwatch(self):
        if self.stopwatch_mainwindow is not None:
            self.disable_stopwatch()
        self.stopwatch_mainwindow=StopWatchMainWindow(self.master)
        self.status_label.setText(f"Enabled (hotkey:{self.stopwatch_mainwindow._hotkey})")

    def disable_stopwatch(self):
        if self.stopwatch_mainwindow is not None:
            self.stopwatch_mainwindow.close()
            self.stopwatch_mainwindow=None
        self.status_label.setText("Disabled")
