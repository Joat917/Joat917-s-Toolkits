import time
import datetime
from borax.calendars import lunardate, festivals2
from tkwindow import *
import cv2
import numpy as np


def get_lunar_info(date: datetime.date):
    lunar_date = lunardate.LunarDate.from_solar(date)
    festivals2.SolarFestival
    return {
        "year": lunar_date.gz_year,
        "month": ('闰' if lunar_date.leap else '')+lunar_date.cn_month+'月',
        "day": lunar_date.cn_day,
        "term": lunar_date.term,
    }


def get_lunar_info_calender(date: datetime.date):
    lunar_date = lunardate.LunarDate.from_solar(date)
    if lunar_date.term is None:
        if lunar_date.day == 1:
            return ('闰' if lunar_date.leap else '')+lunar_date.cn_month+'月'
        else:
            return lunar_date.cn_day
    else:
        return lunar_date.term


def zigzag(x, period, highest, lowest):
    "periodic function with a highest point(1) and a lowest point(0)"
    mid = (highest-lowest) % period
    x_r = (x-lowest) % period
    if x_r <= mid:
        return x_r/mid
    else:
        return (period-x_r)/(period-mid)


class DateDisplay(TKButton):
    WIDTH = 72
    HEIGHT = 66
    W_GAP = WIDTH+6
    H_GAP = HEIGHT+6
    W_0 = 20
    H_0 = 130

    def __init__(self, master, row_count: int, col_count: int, date: datetime.date | None, showColor=True):
        self.date = date
        self.row_count = row_count
        self.col_count = col_count
        canvas = Im.new('RGBA', (self.WIDTH, self.HEIGHT))
        if date is not None:
            _i1 = TKPrompt.text2im('%02d' % date.day, fontSize=50)
            canvas.paste(_i1, ((self.WIDTH-_i1.width)//2, 6))
            _i2 = TKPrompt.text2im(get_lunar_info_calender(date), "simkai.ttf")
            canvas.paste(_i2, ((self.WIDTH-_i2.width)//2, 46))
        x = self.W_0+self.col_count*self.W_GAP
        y = self.H_0+self.row_count*self.H_GAP

        if date is not None and showColor:
            bgcolor1 = ColorUtils.hsv2rgb((
                round(zigzag((date-datetime.date(date.year, 1, 1)).days,
                             period=365, highest=61, lowest=212)*90),
                0x44, 0xff))
            bgcolor2 = ColorUtils.hsv2rgb((
                round(zigzag((date-datetime.date(date.year, 1, 1)).days,
                             period=365, highest=61, lowest=212)*90),
                0x44, 0xaa))

        else:
            bgcolor1 = WINDOW_BG_CLR
            bgcolor2 = WINDOW_BG_CLR_DARKER
        super().__init__(master,
                         width=self.WIDTH, height=self.HEIGHT,
                         x=x, y=y, pasted=canvas,
                         bgColor=bgcolor1, bgColor2=bgcolor2)
        del canvas


class WeekCaptionDisplay(TKButton):
    TEXTS = ["日/SUN", "月/MON", "火/TUE", "水/WED", "木/THR", "金/FRI", "土/SAT"]
    H_C = DateDisplay.H_0-30-6

    def __init__(self, master, col_count: int):
        self.col_count = col_count
        self.text = self.TEXTS[self.col_count]
        canvas = Im.new('RGBA', (DateDisplay.WIDTH, 30))
        canvas.paste(_i1 := TKPrompt.text2im(self.text, fontSize=18, fontFp="simhei.ttf"),
                     ((DateDisplay.WIDTH-_i1.width)//2, 6))
        x = DateDisplay.W_0+self.col_count*DateDisplay.W_GAP
        y = self.H_C
        super().__init__(master,
                         width=DateDisplay.WIDTH, height=30,
                         x=x, y=y, pasted=canvas,
                         bgColor=ColorUtils.hsv2rgb(
                             (25*col_count, 0x44, 0xff)),
                         bgColor2=ColorUtils.hsv2rgb((25*col_count, 0x44, 0xaa)))


class WeekCaptionDisplays:
    def __init__(self, master):
        self.nodes = []
        for i in range(7):
            self.nodes.append(WeekCaptionDisplay(master, i))


class MonthCaptionDisplays:
    H_M = 40
    HEIGHT = 48

    def __init__(self, master, filt=lambda date: True) -> None:
        self.master = master
        self.filt = filt

        self.button_year_m1 = TKButton(
            master=master, width=50, height=self.HEIGHT,
            x=20, y=self.H_M, pasted=TKPrompt.text2im("<<", fontSize=40),
            onclick=self.onClickYearM1, bgColor=WINDOW_BG_CLR,
            bgColor2=WINDOW_BG_CLR_DARKER)
        self.button_year_p1 = TKButton(
            master=master, width=50, height=self.HEIGHT,
            x=516, y=self.H_M, pasted=TKPrompt.text2im(">>", fontSize=40),
            onclick=self.onClickYearP1, bgColor=WINDOW_BG_CLR,
            bgColor2=WINDOW_BG_CLR_DARKER)
        self.button_month_m1 = TKButton(
            master=master, width=50, height=self.HEIGHT,
            x=76, y=self.H_M, pasted=TKPrompt.text2im("<", fontSize=40),
            onclick=self.onClickMonthM1, bgColor=WINDOW_BG_CLR,
            bgColor2=WINDOW_BG_CLR_DARKER)
        self.button_month_p1 = TKButton(
            master=master, width=50, height=self.HEIGHT,
            x=460, y=self.H_M, pasted=TKPrompt.text2im(">", fontSize=40),
            onclick=self.onClickMonthP1, bgColor=WINDOW_BG_CLR,
            bgColor2=WINDOW_BG_CLR_DARKER)

        today = datetime.date.today()
        self.year = today.year
        self.month = today.month
        self.datesDisplay = DatesDisplay(
            self.year, self.month, self.master, self.filt)
        self.weekCaption = WeekCaptionDisplays(self.master)

        self.indicator = TKButton(
            master=master, width=320, height=self.HEIGHT,
            x=133, y=self.H_M, pasted=TKPrompt.text2im(
                "{}年{}月".format(
                    self.year, self.month, self.year, self.month),
                fontFp="simkai.ttf", fontSize=30),
            bgColor=WINDOW_BG_CLR, bgColor2=WINDOW_BG_CLR_DARKER)
        pass

    def onClickYearM1(self, *args):
        self.year -= 1
        self.onRefresh()
        return

    def onClickYearP1(self, *args):
        self.year += 1
        self.onRefresh()
        return

    def onClickMonthM1(self, *args):
        if self.month == 1:
            self.year -= 1
            self.month = 12
        else:
            self.month -= 1
        self.onRefresh()
        return

    def onClickMonthP1(self, *args):
        if self.month == 12:
            self.year += 1
            self.month = 1
        else:
            self.month += 1
        self.onRefresh()
        return

    def onRefresh(self, *args):
        self.datesDisplay = DatesDisplay(
            self.year, self.month, self.master, self.filt)
        self.indicator.manualDeletion()
        self.indicator = TKButton(
            master=self.master, width=320, height=self.HEIGHT,
            x=133, y=self.H_M, pasted=TKPrompt.text2im(
                "{}年{}月".format(
                    self.year, self.month, self.year, self.month),
                fontFp="simkai.ttf", fontSize=30),
            bgColor=WINDOW_BG_CLR, bgColor2=WINDOW_BG_CLR_DARKER)
        # TKPrompt("Caution: Unfixed Memory Leakage! ")


class DatesDisplay:
    def __init__(self, year: int, month: int, master, filt=lambda: True):
        self.year = year
        self.month = month
        self.dates = [datetime.date(self.year, self.month, 1)]
        while True:
            _u = self.dates[-1]+datetime.timedelta(days=1)
            if _u.year == self.year and _u.month == self.month:
                self.dates.append(_u)
            else:
                break
        self.offset = (self.dates[0].weekday()+1) % 7

        self.nodes = []
        self.nodes: list[DateDisplay]
        for i in range(35):
            if i < self.offset:
                self.nodes.append(DateDisplay(master, i//7, i % 7, None))
            elif i-self.offset < len(self.dates):
                self.nodes.append(DateDisplay(
                    master, i//7, i % 7,
                    self.dates[i-self.offset], filt(self.dates[i-self.offset])))
            else:
                self.nodes.append(DateDisplay(master, i//7, i % 7, None))

    def __del__(self):
        for _n in self.nodes:
            _n.manualDeletion()


if __name__ == "__main__":
    r = TKWindow(586, 510)
    c = MonthCaptionDisplays(r.root)
    tk.mainloop()
    pass
