from base_import import *

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
        from PIL import Image
        self.size=size
        self.width=width
        self.color=color
        self.tubeLayoutH=self.paintSingleTube()
        self.tubeLayoutV=self.tubeLayoutH.transpose(Image.Transpose.ROTATE_90)

    def paintSingleTube(self):
        from PIL import Image as Im, ImageDraw as Imd
        color, width, size=self.color, self.width, self.size
        gap = round(width*0.9)
        image = Im.new("RGBA", (size, width), color)
        for _ in range(4):
            Imd.Draw(image).polygon([(0,0),(gap, 0),(0,gap)], fill=(0,0,0,0))
            image=image.transpose(Im.Transpose.ROTATE_90)
        return image
    
    def _putTube(self, im, lefttop, vertical):
        if vertical:
            im.paste(self.tubeLayoutV, lefttop, self.tubeLayoutV.getchannel('A'))
        else:
            im.paste(self.tubeLayoutH, lefttop, self.tubeLayoutH.getchannel('A'))

    def paintdigit(self, digit: int):
        from PIL import Image as Im, ImageDraw as Imd
        width, size=self.width, self.size
        image = Im.new("RGBA", (size, size*2), (0, 0, 0, 0))

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
        from PIL import Image as Im, ImageDraw as Imd
        color, width, size=self.color, self.width, self.size
        gap = width//2
        image = Im.new("RGBA", (size, size*2), (0, 0, 0, 0))
        draw = Imd.Draw(image)
        draw.rectangle((size//2-gap, size//2-gap, size//2+gap, size//2+gap), fill=color)
        draw.rectangle((size//2-gap, size+size//2-gap, size//2+gap, size+size//2+gap), fill=color)

        return image
    
    def paintdot(self):
        from PIL import Image as Im, ImageDraw as Imd
        color, width, size=self.color, self.width, self.size
        gap = width//2
        image = Im.new("RGBA", (size, size*2), (0, 0, 0, 0))
        draw = Imd.Draw(image)
        draw.rectangle((size//2-gap, 2*size-width, size//2+gap, 2*size), fill=color)

        return image

    @classmethod
    def paint_and_save(cls):
        tp=TubePainter()
        os.makedirs('./img', exist_ok=True)
        for digit in DIGITS:
            tp.paintdigit(digit).save(f'./img/digitTube{digit}.png')
        tp.paintcolon().save('./img/digitTubeC.png')
        tp.paintdot().save('./img/digitTubeD.png')
        __import__('PIL').Image.new("RGBA", (tp.size, 2*tp.size), (0,0,0,0)).save('./img/digitTubeS.png')

class TubeReader:
    def __init__(self):
        self.pictures={d:QPixmap(f'./img/digitTube{d}.png') for d in DIGITS.keys()}
        self.pictures[':']=QPixmap('./img/digitTubeC.png')
        self.pictures['.']=QPixmap('./img/digitTubeD.png')
        self.pictures[' ']=QPixmap('./img/digitTubeS.png')
        
    @classmethod
    def constructor(cls):
        try:
            return TubeReader()
        except FileNotFoundError:
            pass
        try:
            TubePainter.paint_and_save()
            return TubeReader()
        except ImportError:
            raise


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
        self.setGeometry(50, screen_geometry.height()-300, 500, 100)
        self.setWindowOpacity(0.8)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setStyleSheet("background-color:rgba(0,0,0,0.5);border-radius: 10px")

        layout=QHBoxLayout()
        tubeReader=TubeReader()
        for k in tubeReader.pictures:
            tubeReader.pictures[k]=tubeReader.pictures[k].scaled(50, 100)
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
            from main_window import MainWindow
            assert isinstance(self._master, MainWindow)
            self._tray=self._master.trayWidget
            self._action = self._tray.add_action("Stopwatch:START", self.action)
            self._hotkey = 'F13'
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
                self._action.setText('Stopwatch:STOP')
        elif self._mode==1:
            self._mode=2
            self._timeRecord=time.time()-self._timeRecord
            self._refresh(self._timeRecord)
            if self._action is not None:
                self._action.setText('Stopwatch:RESET')
        elif self._mode==2:
            self._mode=0
            self._timeRecord=None
            self._refresh(0)
            if self._action is not None:
                self._action.setText('Stopwatch:START')
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
        menu = QMenu(self)
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
        self._timer = None
        return super().close()


if __name__ == "__main__":
    from main_window import MainWindow, WidgetBox
    from switch_widgets import SwitchButton
    from start_check import check_started
    app = QApplication(sys.argv)
    check_started()
    MainWindow.TITLE = "StopWatch Test"
    window = MainWindow(app=app)

    stopwatch = []

    window.addWidget(WidgetBox(
        parent=window, 
        title="Stopwatch", 
        widgets=[SwitchButton(
            onturnon=lambda: stopwatch.append(StopWatchMainWindow(window)), 
            onturnoff=lambda: (stopwatch.pop().close() if stopwatch else None)
        )]
    ))

    window.show()
    sys.exit(app.exec_())
