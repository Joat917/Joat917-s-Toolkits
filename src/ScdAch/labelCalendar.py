from math import ceil
from calendarA import *
from schReader import *


def getDatesMon(file: LogFile, label: LabelType, year: int, month: int):
    o = []
    logs = file.getLogsM(year, month)
    logs: list[LogInfo]
    for eve in map(SchdEvent.fromLogInfo, logs):
        if label in eve.labl:
            o.append(eve.dt_start.date())
    o: list[datetime.date]
    return frozenset(o)


class CalendarRenderer:
    def __init__(self, file: LogFile, label: LabelType, title=None) -> None:
        if title is None:
            title = label.name.upper()
        self.window = TKWindow(586, 510, rooted=False, title=title)
        self.buf = {}

        def filtFunc(date: datetime.date):
            try:
                return date in self.buf[date.year, date.month]
            except KeyError:
                _t = self.buf[date.year, date.month] = getDatesMon(
                    file, label, date.year, date.month)
                return date in _t
        self.calendar = MonthCaptionDisplays(self.window.root, filtFunc)
        self.window.widgets.append(self)
        self.window.widgets.append(self.calendar)
        return


class CalendarStarter:
    BUTTON_WIDTH = 100
    BUTTON_HEIGHT = 30
    GAP = 10

    def __init__(self, master, colCount=4, lf: LogFile | None = None, x=20, y=40) -> None:
        self.buttons = []
        self.master = master
        if lf is None:
            self.logfile = LogFile("logfile.dat.xz")
        else:
            self.logfile = lf

        self.frame = tk.Frame(
            master=self.master, bg=WINDOW_BG_CLR, borderwidth=0,
            width=(self.BUTTON_WIDTH+self.GAP)*colCount,
            height=(self.BUTTON_HEIGHT+self.GAP)*ceil(
                len(LabelType._member_names_)/colCount))
        self.frame.place(x=x, y=y)
        for _name, _mem in LabelType._member_map_.items():
            _str = _mem.value
            self.buttons.append(TKButton(
                self.frame, self.BUTTON_WIDTH, self.BUTTON_HEIGHT,
                (self.BUTTON_WIDTH+self.GAP)*(len(self.buttons) % colCount),
                (self.BUTTON_HEIGHT+self.GAP)*(len(self.buttons)//colCount),
                TKPrompt.text2im(_str, "simkai.ttf"),
                onclick=eval(
                    "lambda:f({})".format(repr(_name)),
                    {'f': self.callbackStart}),
                bgColor=label2color(_mem),
                bgColor2=ColorUtils.darken(label2color(_mem))))
        del _name, _mem

    def callbackStart(self, labelName: str):
        CalendarRenderer(self.logfile, LabelType._member_map_[labelName])

    def manualDeletion(self):
        try:
            self.frame.destroy()
        except Exception:
            pass
        for but in self.buttons:
            but.manualDeletion()
        delattr(self, "buttons")
        delattr(self, "master")
        delattr(self, "frame")


if __name__ == "__main__":
    def main():
        r = TKWindow(150, 60, rooted=True)
        t = TKWindow(490, 180, rooted=False, title="OPT_CALENDAR")
        s = CalendarStarter(t.root)
        t.widgets.append(s)
        del s
        tk.mainloop()
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        print("...")
