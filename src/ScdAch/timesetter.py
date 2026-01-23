from tkwindow import *
import time
import datetime


class _TimeSetterDigit(TKButton):
    def __init__(self, master, x: int, y: int, digit=0) -> None:
        self._digit = digit
        if str(digit).isdigit():
            _fontPath="bahnschrift.ttf"
        else:
            _fontPath="simkai.ttf"
        super().__init__(master, TimeSetter.WIDTH, TimeSetter.DIGIT_HEIGHT,
                         x, y, TKPrompt.text2im(str(digit), _fontPath),
                         bgColor=WINDOW_BG_CLR, bgColor2=WINDOW_BG_CLR)

    def onRefresh(self, digit):
        if self._digit != digit:
            self._digit = digit
            pasted = TKPrompt.text2im(str(digit))
            self.image = Im.new(
                'RGB', (self.width, self.height), WINDOW_BG_CLR)
            Imd.Draw(self.image).rounded_rectangle(
                (0, 0, self.width, self.height), 20, self.bgColor)
            self.image.paste(pasted, ((self.width-pasted.width)//2,
                                      (self.height-pasted.height)//2),
                             pasted.getchannel('A'))
            self.image_tk = Imtk.PhotoImage(self.image)

            self.image2 = Im.new(
                'RGB', (self.width, self.height), WINDOW_BG_CLR)
            Imd.Draw(self.image2).rounded_rectangle(
                (0, 0, self.width, self.height), 20, self.bgColor2)
            self.image2.paste(pasted, ((self.width-pasted.width)//2,
                                       (self.height-pasted.height)//2),
                              pasted.getchannel('A'))
            self.image2_tk = Imtk.PhotoImage(self.image2)

            self.widget.config(image=self.image_tk)

    @property
    def digit(self):
        return self._digit

    @digit.setter
    def digit(self, x):
        self.onRefresh(x)


class _TimeSetterButton(TKButton):
    _inited=False
    @classmethod
    def init(cls):
        cls.pasted_plus = TKPrompt.text2im("+")
        cls.color_plus = '#ffbbdd'
        cls.color2_plus = ColorUtils.darken(cls.color_plus)
        cls.pasted_minus = TKPrompt.text2im("-")
        cls.color_minus = '#bbffdd'
        cls.color2_minus = ColorUtils.darken(cls.color_minus)
        cls._inited=True

    def __init__(self, master, x: int, y: int, figure: str,
                 timeSetter, timeDelta, onclick=lambda: None):
        if not self._inited:
            self.init()
        if not isinstance(timeSetter, TimeSetter):
            raise TypeError
        if not isinstance(timeDelta, datetime.timedelta):
            raise TypeError
        self.timeSetter = timeSetter
        self.timeDelta = timeDelta
        if figure == '+':
            def _onclick():
                self.timeSetter.dt += self.timeDelta
                self.timeSetter.onRefresh()
                onclick()
            super().__init__(master, TimeSetter.WIDTH, TimeSetter.BUTTON_HEIGHT,
                             x, y, self.pasted_plus, _onclick,
                             self.color_plus, self.color2_plus)
        elif figure == '-':
            def _onclick():
                self.timeSetter.dt -= self.timeDelta
                self.timeSetter.onRefresh()
                onclick()
            super().__init__(master, TimeSetter.WIDTH, TimeSetter.BUTTON_HEIGHT,
                             x, y, self.pasted_minus, _onclick,
                             self.color_minus, self.color2_minus)
        else:
            raise ValueError("figure must be '+' or '-'")


class TimeSetter:
    WIDTH = 15
    DIGIT_HEIGHT = 20
    BUTTON_HEIGHT = 15

    def __init__(self, master, x: int, y: int, dt: datetime.datetime, _onRefresh=lambda:None) -> None:
        self.master = master
        self.x = x
        self.y = y
        self.width = self.WIDTH*20
        self.height = self.BUTTON_HEIGHT*2+self.DIGIT_HEIGHT
        self.dt = dt
        self._onRefresh=_onRefresh

        self.frame = tk.Frame(
            self.master, borderwidth=0, bg=WINDOW_BG_CLR,
            width=self.width, height=self.height)
        self.frame.place(x=self.x, y=self.y)

        self.year_digit_0 = _TimeSetterDigit(
            self.frame, 0, self.BUTTON_HEIGHT)
        self.year_digit_1 = _TimeSetterDigit(
            self.frame, self.WIDTH, self.BUTTON_HEIGHT)
        self.year_digit_2 = _TimeSetterDigit(
            self.frame, self.WIDTH*2, self.BUTTON_HEIGHT)
        self.year_digit_3 = _TimeSetterDigit(
            self.frame, self.WIDTH*3, self.BUTTON_HEIGHT)
        self.year_hanzi = _TimeSetterDigit(
            self.frame, self.WIDTH*4, self.BUTTON_HEIGHT, digit='年')
        self.month_digit_0 = _TimeSetterDigit(
            self.frame, self.WIDTH*5, self.BUTTON_HEIGHT)
        self.month_digit_1 = _TimeSetterDigit(
            self.frame, self.WIDTH*6, self.BUTTON_HEIGHT)
        self.month_hanzi = _TimeSetterDigit(
            self.frame, self.WIDTH*7, self.BUTTON_HEIGHT, digit='月')
        self.day_digit_0 = _TimeSetterDigit(
            self.frame, self.WIDTH*8, self.BUTTON_HEIGHT)
        self.day_digit_1 = _TimeSetterDigit(
            self.frame, self.WIDTH*9, self.BUTTON_HEIGHT)
        self.day_hanzi = _TimeSetterDigit(
            self.frame, self.WIDTH*10, self.BUTTON_HEIGHT, digit='日')
        self.hour_digit_0 = _TimeSetterDigit(
            self.frame, self.WIDTH*11, self.BUTTON_HEIGHT)
        self.hour_digit_1 = _TimeSetterDigit(
            self.frame, self.WIDTH*12, self.BUTTON_HEIGHT)
        self.hour_hanzi = _TimeSetterDigit(
            self.frame, self.WIDTH*13, self.BUTTON_HEIGHT, digit='时')
        self.minu_digit_0 = _TimeSetterDigit(
            self.frame, self.WIDTH*14, self.BUTTON_HEIGHT)
        self.minu_digit_1 = _TimeSetterDigit(
            self.frame, self.WIDTH*15, self.BUTTON_HEIGHT)
        self.minu_hanzi = _TimeSetterDigit(
            self.frame, self.WIDTH*16, self.BUTTON_HEIGHT, digit='分')
        self.sec_digit_0 = _TimeSetterDigit(
            self.frame, self.WIDTH*17, self.BUTTON_HEIGHT)
        self.sec_digit_1 = _TimeSetterDigit(
            self.frame, self.WIDTH*18, self.BUTTON_HEIGHT)
        self.sec_hanzi = _TimeSetterDigit(
            self.frame, self.WIDTH*19, self.BUTTON_HEIGHT, digit='秒')

        self.day_digit_0_plus = _TimeSetterButton(
            self.frame, self.WIDTH*8, 0, '+',
            self, datetime.timedelta(days=10))
        self.day_digit_1_plus = _TimeSetterButton(
            self.frame, self.WIDTH*9, 0, '+',
            self, datetime.timedelta(days=1))
        self.hour_digit_0_plus = _TimeSetterButton(
            self.frame, self.WIDTH*11, 0, '+',
            self, datetime.timedelta(hours=10))
        self.hour_digit_1_plus = _TimeSetterButton(
            self.frame, self.WIDTH*12, 0, '+',
            self, datetime.timedelta(hours=1))
        self.minu_digit_0_plus = _TimeSetterButton(
            self.frame, self.WIDTH*14, 0, '+',
            self, datetime.timedelta(minutes=10))
        self.minu_digit_1_plus = _TimeSetterButton(
            self.frame, self.WIDTH*15, 0, '+',
            self, datetime.timedelta(minutes=1))
        self.sec_digit_0_plus = _TimeSetterButton(
            self.frame, self.WIDTH*17, 0, '+',
            self, datetime.timedelta(seconds=10))
        self.sec_digit_1_plus = _TimeSetterButton(
            self.frame, self.WIDTH*18, 0, '+',
            self, datetime.timedelta(seconds=1))

        self.day_digit_0_minus = _TimeSetterButton(
            self.frame, self.WIDTH*8, self.BUTTON_HEIGHT+self.DIGIT_HEIGHT, '-',
            self, datetime.timedelta(days=10))
        self.day_digit_1_minus = _TimeSetterButton(
            self.frame, self.WIDTH*9, self.BUTTON_HEIGHT+self.DIGIT_HEIGHT, '-',
            self, datetime.timedelta(days=1))
        self.hour_digit_0_minus = _TimeSetterButton(
            self.frame, self.WIDTH*11, self.BUTTON_HEIGHT+self.DIGIT_HEIGHT, '-',
            self, datetime.timedelta(hours=10))
        self.hour_digit_1_minus = _TimeSetterButton(
            self.frame, self.WIDTH*12, self.BUTTON_HEIGHT+self.DIGIT_HEIGHT, '-',
            self, datetime.timedelta(hours=1))
        self.minu_digit_0_minus = _TimeSetterButton(
            self.frame, self.WIDTH*14, self.BUTTON_HEIGHT+self.DIGIT_HEIGHT, '-',
            self, datetime.timedelta(minutes=10))
        self.minu_digit_1_minus = _TimeSetterButton(
            self.frame, self.WIDTH*15, self.BUTTON_HEIGHT+self.DIGIT_HEIGHT, '-',
            self, datetime.timedelta(minutes=1))
        self.sec_digit_0_minus = _TimeSetterButton(
            self.frame, self.WIDTH*17, self.BUTTON_HEIGHT+self.DIGIT_HEIGHT, '-',
            self, datetime.timedelta(seconds=10))
        self.sec_digit_1_minus = _TimeSetterButton(
            self.frame, self.WIDTH*18, self.BUTTON_HEIGHT+self.DIGIT_HEIGHT, '-',
            self, datetime.timedelta(seconds=1))
        
        self.onRefresh()

    def manualDeletion(self):
        print("Manually Delete a timesetter")
        for _name in dir(self):
            if _name.startswith('__'):
                continue
            try:
                getattr(self, _name).manualDeletion()
            except AttributeError:
                pass
            except Exception:
                import traceback
                print(_name)
                traceback.print_exc()
            try:
                delattr(self, _name)
            except AttributeError:
                pass
        return

    def onRefresh(self):
        self.year_digit_0.digit = self.dt.year//1000 % 10
        self.year_digit_1.digit = self.dt.year//100 % 10
        self.year_digit_2.digit = self.dt.year//10 % 10
        self.year_digit_3.digit = self.dt.year//1 % 10
        self.month_digit_0.digit = self.dt.month//10 % 10
        self.month_digit_1.digit = self.dt.month//1 % 10
        self.day_digit_0.digit = self.dt.day//10 % 10
        self.day_digit_1.digit = self.dt.day//1 % 10
        self.hour_digit_0.digit = self.dt.hour//10 % 10
        self.hour_digit_1.digit = self.dt.hour//1 % 10
        self.minu_digit_0.digit = self.dt.minute//10 % 10
        self.minu_digit_1.digit = self.dt.minute//1 % 10
        self.sec_digit_0.digit = self.dt.second//10 % 10
        self.sec_digit_1.digit = self.dt.second//1 % 10
        self._onRefresh()


if __name__ == "__main__":
    def main():
        r = TKWindow(150, 60, True)
        s = TKWindow(440, 300, False, 'TimeSetterTest')
        t = TimeSetter(s.root, 20, 40, datetime.datetime.now())
        tk.mainloop()
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        input("...")
