from math import ceil
from tkwindow import *
from schReader import *
from timesetter import *


class TimeLineButton:
    "一个类似TKButton的类，专门为TimelineDisplay而用"

    def __init__(self, master: tk.Toplevel | tk.Tk, width: int, height: int,
                 x: int, y: int, color: str | tuple, onclick=lambda: None,
                 shrinkDepth=5, started=False, ended=False):
        self.master = master
        self.width = width
        self.height = height
        self._onclick = onclick
        self.x = x
        self.y = y

        self.image = Im.new('RGB', (self.width, self.height), WINDOW_BG_CLR)
        _radius = min(20, self.height//2-shrinkDepth -
                      1, self.width//2-shrinkDepth-1)
        # print((0, shrinkDepth, self.width, self.height-shrinkDepth),
        #       _radius, color, (started, ended, ended, started))
        if _radius < 0:
            Imd.Draw(self.image).rectangle(
                (0, shrinkDepth, self.width, self.height-shrinkDepth),
                fill=color)
        else:
            Imd.Draw(self.image).rounded_rectangle(
                (0, shrinkDepth, self.width, self.height-shrinkDepth),
                radius=_radius, fill=color, corners=(started, ended, ended, started))
        self.image_tk = Imtk.PhotoImage(self.image)

        self.image2 = Im.new('RGB', (self.width, self.height), WINDOW_BG_CLR)
        _radius = min(20, self.height//2 - 1, self.width//2-1)
        if _radius < 0:
            Imd.Draw(self.image2).rectangle(
                (0, 0, self.width, self.height), fill=color)
        else:
            Imd.Draw(self.image2).rounded_rectangle(
                (0, 0, self.width, self.height), radius=_radius,
                fill=color, corners=(started, ended, ended, started))
        self.image2_tk = Imtk.PhotoImage(self.image2)

        self.widget = tk.Label(
            self.master, image=self.image_tk,
            borderwidth=0, width=self.width, height=self.height)
        self.widget.bind('<Enter>', self.onEnter)
        self.widget.bind('<Leave>', self.onLeave)
        self.widget.bind('<Button-1>', self.onClick)
        self.widget.place(x=self.x, y=self.y)

    def onEnter(self, *args):
        # print("TimeLineButton:Enter")
        self.widget.config(image=self.image2_tk)

    def onLeave(self, *args):
        # print("TimeLineButton:Leave")
        self.widget.config(image=self.image_tk)

    def onClick(self, *args):
        # print("TimeLineButton:Clear")
        self._onclick()

    def manualDeletion(self):
        "Since TKButton objects cannot delete on itself, THIS FUNCTION MUST BE CALLED TO AVOID MEMORY LEAKAGE!!!"
        try:
            self.widget.destroy()
        except Exception:
            pass
        for _name in dir(self):
            if _name.startswith('__'):
                continue
            try:
                delattr(self, _name)
            except AttributeError:
                pass

    def __del__(self):
        WDPs.inst.countAdd('widget')
        try:
            self.widget.destroy()
        except Exception:
            pass


class TimeLineDisplay:
    "在给定窗口中显示时间轴"

    def __init__(self, lf: LogFile, mst: tk.Tk | tk.Toplevel,
                 date=None, width=680, height=40, x=20, y=40):
        self.lf = lf
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        if isinstance(mst, tk.Wm):
            self.mst = mst
        else:
            raise TypeError
        if date is None:
            self.date = datetime.date.today()
        elif isinstance(date, datetime.date):
            self.date = date
        else:
            raise TypeError
        self.components = []

        self.onRefresh()
        self.onHighLight = lambda x: None

    @property
    def dt_start(self):
        yesterday = self.date-datetime.timedelta(days=1)
        return datetime.datetime(
            year=yesterday.year, month=yesterday.month, day=yesterday.day,
            hour=20, minute=0, second=0)

    @property
    def dt_end(self):
        return datetime.datetime(
            year=self.date.year, month=self.date.month, day=self.date.day,
            hour=23, minute=59, second=59)

    def onRefresh(self):
        timeline = TimeLine(self.dt_start, self.dt_end, self.lf)
        timelist = timeline.getTimeLine()
        # print("timelist", timelist)
        for widget in self.components:
            widget.manualDeletion()
        self.components.clear()
        for i in range(len(timelist)):
            st, ed, ev = timelist[i]
            prop_st = (st-timeline.dt_start)/timeline.dt_duration
            prop_ed = (ed-timeline.dt_start)/timeline.dt_duration
            ain_start = i == 0
            ain_end = i == len(timelist)-1

            but = TimeLineButton(
                self.mst, round(self.width*(prop_ed-prop_st)), self.height,
                self.x+round(self.width*prop_st), self.y,
                event2color(
                    ev.typ if ev is not None else EventType.UNALLOCATED),
                onclick=lambda: self.onHighLight(ev), started=ain_start, ended=ain_end)
            self.components.append(but)
            # print("button", but.widget.place_info())
        return


class LabelSelectorDisplay:
    BUTTON_WIDTH = 100
    BUTTON_HEIGHT = 30
    GAP = 10

    def __init__(self, master, oncheck=lambda x: None,
                 onuncheck=lambda x: None, colCount=6, x=0, y=0, 
                 initLabels:frozenset[LabelType]=frozenset()) -> None:
        self.buttons = []
        self.master = master
        self.frame = tk.Frame(
            master=self.master, bg=WINDOW_BG_CLR, borderwidth=0,
            width=(self.BUTTON_WIDTH+self.GAP)*colCount,
            height=(self.BUTTON_HEIGHT+self.GAP)*ceil(
                len(LabelType._member_names_)/colCount))
        self.frame.place(x=x, y=y)
        for _name, _mem in LabelType._member_map_.items():
            _str = _mem.value
            self.buttons.append(TKCheckBox(
                self.frame, self.BUTTON_WIDTH, self.BUTTON_HEIGHT,
                (self.BUTTON_WIDTH+self.GAP)*(len(self.buttons) % colCount),
                (self.BUTTON_HEIGHT+self.GAP)*(len(self.buttons)//colCount),
                TKPrompt.text2im(_str, "simkai.ttf"),
                onCheck=eval(f"lambda:oncheck({repr(_name)})",
                             {"oncheck": oncheck}),
                onUncheck=eval(f"lambda:onuncheck({repr(_name)})",
                               {"onuncheck": onuncheck}),
                bgColorCheck=label2color(_mem),
                bgColorCheck2=ColorUtils.darken(label2color(_mem)),
                checked=(_mem in initLabels)))
            del _name, _mem

    def manualDeletion(self):
        self.frame.destroy()
        for but in self.buttons:
            but.manualDeletion()
        delattr(self, "buttons")
        delattr(self, "master")
        delattr(self, "frame")


class EventEditorDisplay:
    def __init__(self, timeline: TimeLineDisplay,
                 width=680, height=400, x=20, y=90) -> None:
        self.mst = timeline.mst
        self.lf = timeline.lf
        self.timeline = timeline
        self.width = width
        self.scroller = Scroller(self.mst, self.width, height, x, y)

        adwg_height = 80
        adwg = ScrollerWidget(self.scroller, adwg_height)
        adwg_pasted = Im.new('RGBA', (width-400, adwg_height-4))
        adwgimd = Imd.Draw(adwg_pasted)
        adwgimd.line((adwg_pasted.width//2, adwg_pasted.height//2-10,
                      adwg_pasted.width//2, adwg_pasted.height//2+10), WINDOW_BD_CLR, 4)
        adwgimd.line((adwg_pasted.width//2-10, adwg_pasted.height//2,
                      adwg_pasted.width//2+10, adwg_pasted.height//2), WINDOW_BD_CLR, 4)
        adwgwg = TKButton(adwg.root, width-400, adwg_height-4, 200, 2,
                          adwg_pasted, onclick=self.addEventCallback,
                          bgColor=WINDOW_BG_CLR, bgColor2=WINDOW_BG_CLR_DARKER)
        adwg.widgets.append(adwgwg)
        self.scroller.appendWidget(adwg)

        self.schds = []
        self.timeline.onHighLight = self.onHighLight

        # load init events. Reference: schReader.py/TimeLine.__init__
        yms = TimeLine.getYearMonths(
            (self.timeline.dt_start.year, self.timeline.dt_start.month),
            (self.timeline.dt_end.year, self.timeline.dt_end.month))
        for ym in yms:
            for ev in self.lf.getLogsM(*ym):
                ev: LogInfo
                if ev.dt < self.timeline.dt_end:
                    sce = SchdEvent.fromLogInfo(ev)
                    if sce.dt_end > self.timeline.dt_start:
                        # add this event. Reference: EED.addEventCallback
                        self.addEventCallback(sce)
        pass

    def _get_dt_start_end_typ(self):
        "在生成新事件时的默认起止时间和默认类别"
        if len(self.schds) == 0:
            start = self.timeline.dt_start + \
                datetime.timedelta(hours=random.random()*4)
            end = self.timeline.dt_start + \
                datetime.timedelta(hours=7+random.random()*4)
            typ = EventType.SLEEP
        elif len(self.schds) < 3:
            start = self.timeline.dt_end - \
                datetime.timedelta(hours=4+12*random.random())
            end = start+datetime.timedelta(hours=0.5+random.random())
            typ = EventType.MEAL
        else:
            start = self.timeline.dt_end +\
                datetime.timedelta(seconds=2) - \
                datetime.timedelta(hours=random.randint(6, 16))
            end = start+datetime.timedelta(hours=1.5)
            typ = EventType.CLASS
        start = datetime.datetime(
            year=start.year, month=start.month, day=start.day,
            hour=start.hour, minute=(start.minute)//15*15, second=0)
        end = datetime.datetime(
            year=end.year, month=end.month, day=end.day,
            hour=end.hour, minute=(end.minute)//20*20, second=0)
        return start, end, typ

    def addEventCallback(self, _schd: SchdEvent | None = None):
        # print("add an event")
        new_container = ScrollerWidget(self.scroller, 240)
        if _schd is None:
            dt_start, dt_end, typ = self._get_dt_start_end_typ()
            schd = SchdEvent(dt_start, dt_end, typ, [], "")
        else:
            dt_start = _schd.dt_start
            dt_end = _schd.dt_end
            typ = _schd.typ
            schd = _schd

        def _get_on_typ_set(i):
            def _func():
                print("type change to {}".format(EventType._member_names_[i]))
                self.lf.removeLog(schd.toLogInfo())
                schd.typ = EventType._member_map_[EventType._member_names_[i]]
                self.lf.addLog(schd.toLogInfo())
                self.onRefresh(schd)
            return _func

        new_container.widgets.append(TKMultiSelect(
            new_container.root, 110, 30, 20, 20,
            [TKPrompt.text2im(eventTypeTranslator[
                EventType._member_names_[i]], "simkai.ttf")
             for i in range(len(EventType._member_names_))],
            optFuncs=[_get_on_typ_set(i) for i in range(
                len(EventType._member_names_))],
            optColors=[event2color(EventType._member_map_[EventType._member_names_[i]])
                       for i in range(len(EventType._member_names_))],
            defaultIndex=EventType._member_names_.index(typ.name)
        ))
        new_container.widgets.append(TKButton(
            new_container.root, 110, 30, 20, 60,
            TKPrompt.text2im("Remove"),
            onclick=lambda: self.removeSchd(schd),
            bgColor=WINDOW_BG_CLR, bgColor2='red'
        ))

        # dt_start editor
        def _set_dtStart():
            try:
                dt_start_setter
            except NameError:
                return
            if dt_start_setter.dt >= dt_end_setter.dt:
                print("Cannot set starttime later than endtime")
            print("dt_start change to {}".format(dt_start_setter.dt))
            self.lf.removeLog(schd.toLogInfo())
            schd.dt_start = dt_start_setter.dt
            schd.dt_end = dt_end_setter.dt
            self.lf.addLog(schd.toLogInfo())
            self.onRefresh(schd)
        dt_start_setter = TimeSetter(
            new_container.root, 150, 20, schd.dt_start, _set_dtStart)
        new_container.widgets.append(dt_start_setter)

        # dt_end editor
        def _set_dtEnd():
            try:
                dt_end_setter
            except NameError:
                return
            if dt_end_setter.dt <= dt_start_setter.dt:
                print("Cannot set endtime earlier than starttime")
                return
            print("dt_end change to {}".format(dt_end_setter.dt))
            self.lf.removeLog(schd.toLogInfo())
            schd.dt_start = dt_start_setter.dt
            schd.dt_end = dt_end_setter.dt
            self.lf.addLog(schd.toLogInfo())
            self.onRefresh(schd)
        dt_end_setter = TimeSetter(
            new_container.root, 150, 80, schd.dt_end, _set_dtEnd)
        new_container.widgets.append(dt_end_setter)

        # labels selector
        def _onCheck(_name):
            lb = LabelType._member_map_[_name]
            if lb not in schd.labl:
                self.lf.removeLog(schd.toLogInfo())
                schd.labl = schd.labl.union({lb})
                self.lf.addLog(schd.toLogInfo())
                self.onRefresh(schd)

        def _onUncheck(_name):
            lb = LabelType._member_map_[_name]
            if lb in schd.labl:
                self.lf.removeLog(schd.toLogInfo())
                schd.labl = schd.labl.difference({lb})
                self.lf.addLog(schd.toLogInfo())
                self.onRefresh(schd)
        label_editor = LabelSelectorDisplay(
            new_container.root, _onCheck, _onUncheck, 
            x=20, y=140, initLabels=schd.labl)
        new_container.widgets.append(label_editor)

        # ps writter
        ...

        self.schds.append(schd)
        self.scroller.appendWidget(new_container)
        if _schd is None:
            self.lf.addLog(schd.toLogInfo())
            # focus this event
            self.onRefresh(schd)
            self.onHighLight(schd)

    def onRefresh(self, schd: SchdEvent):
        self.timeline.onRefresh()
        # i = self.schds.index(schd)
        # self.scroller._widgets[i]
        print(self.lf.getLogsA())
        return

    def removeSchd(self, schd: SchdEvent):
        i = self.schds.index(schd)
        self.scroller.removeWidget(self.scroller._widgets[i+1])
        self.schds.pop(i)
        self.lf.removeLog(schd.toLogInfo())
        self.onRefresh(schd)
        return

    def onHighLight(self, schd: SchdEvent):
        if schd is None:
            return
        i = self.schds.index(schd)
        tgt_off = self.scroller._widgets[i].root.winfo_y()
        self.scroller.scroll_offset = tgt_off
        return

    def manualDeletion(self, checkSaved=True):
        if checkSaved and not self.testSaved():
            # raise RuntimeError("Not Time to Close")
            return
        for a in self.timeline.components:
            a.manualDeletion()
        self.scroller.manualDeletion()

    def testSaved(self, popup=True):
        if not self.lf.saved:
            if popup:
                # pop up a window whether to save or not
                window = TKWindow(200, 100, False, "SAVE?")

                def _save():
                    self.save()
                    self.manualDeletion()
                    window.destroy()

                def _notSave():
                    self.manualDeletion(False)
                    window.destroy()
                button1 = TKButton(
                    window.root, 60, 30, 20, 40,
                    TKPrompt.text2im("Save"), _save)
                window.widgets.append(button1)
                button2 = TKButton(
                    window.root, 100, 30, 90, 40,
                    TKPrompt.text2im("Don't Save"), _notSave)
                window.widgets.append(button2)
            return False
        return True

    def save(self):
        self.lf.save()
        TKPrompt("Records saved!")

    def extract(self):
        self.lf.extract()
        # TKPrompt("Records extracted to {}".format(
        #     os.path.abspath('./sch0_ext')))
        TKPrompt("Records extracted to ./sch0_ext")

    def __del__(self):
        if not self.testSaved(popup=False):
            print("Warning: destroy before saving!")


class EventEditorWindow:
    def __init__(self, date=None, logfile=None) -> None:
        self.tkwindow = TKWindow(720, 560, rooted=False, title="EVENT EDITOR")
        if logfile is None:
            self.logfile = LogFile("logfile.dat.xz")
        elif isinstance(logfile, LogFile):
            self.logfile = logfile
        else:
            raise ValueError
        if date is None:
            self._date = datetime.date.today()
        elif isinstance(date, datetime.date):
            self._date = date
        else:
            raise ValueError

        self.timeline = TimeLineDisplay(
            lf=self.logfile, mst=self.tkwindow.root,
            date=self._date, y=90)
        self.eventEditor = EventEditorDisplay(
            self.timeline, y=140)

        self.button_yesterday = TKButton(
            self.tkwindow.root, 30, 30, 20, 40,
            TKPrompt.text2im("<"), self.callback_DateM1)
        self.button_tomorrow = TKButton(
            self.tkwindow.root, 30, 30, 230, 40,
            TKPrompt.text2im(">"), self.callback_DateP1)
        self.button_dateShow = TKButton(
            self.tkwindow.root, 160, 30, 60, 40,
            TKPrompt.text2im("{:04d}年{:02d}月{:02d}日".format(
                self._date.year, self._date.month, self._date.day), "simkai.ttf"),
            bgColor=WINDOW_BG_CLR, bgColor2=WINDOW_BG_CLR)
        # self.button_showCalendar = TKButton()
        self.button_save = TKButton(
            self.tkwindow.root, 80, 30, 270, 40,
            TKPrompt.text2im("SAVE"), self.eventEditor.save)
        self.button_extract = TKButton(
            self.tkwindow.root, 120, 30, 360, 40,
            TKPrompt.text2im("EXTRACT"), self.eventEditor.extract)

        self.tkwindow.widgets.append(self)

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, _new_date):
        if not isinstance(_new_date, datetime.date):
            raise TypeError
        if self._date != _new_date:
            self._date = _new_date
            self.timeline = TimeLineDisplay(
                lf=self.logfile, mst=self.tkwindow.root,
                date=self._date, y=90)
            self.eventEditor.manualDeletion(False)
            self.eventEditor = EventEditorDisplay(self.timeline, y=140)
            self.button_dateShow.manualDeletion()
            self.button_dateShow = TKButton(
                self.tkwindow.root, 160, 30, 60, 40,
                TKPrompt.text2im("{:04d}年{:02d}月{:02d}日".format(
                    self._date.year, self._date.month, self._date.day), "simkai.ttf"),
                bgColor=WINDOW_BG_CLR, bgColor2=WINDOW_BG_CLR)

    def callback_DateM1(self):
        self.date -= datetime.timedelta(days=1)

    def callback_DateP1(self):
        self.date += datetime.timedelta(days=1)

    def manualDeletion(self):
        for _name in dir(self):
            if _name.startswith('__'):
                continue
            try:
                getattr(self, _name).manualDeletion()
            except AttributeError:
                pass
            try:
                delattr(self, _name)
            except AttributeError:
                pass


if __name__ == "__main__":
    def main():
        r = TKWindow(150, 60, rooted=True)
        # w = TKWindow(720, 520, rooted=False)
        # f = LogFile("logfile.dat.xz")
        # tld = TimeLineDisplay(f, w.root, x=20, y=40)
        # tle = EventEditorDisplay(tld)
        # w.widgets.append(tld)
        # w.widgets.append(tle)
        s = EventEditorWindow()
        tk.mainloop()
        return
    try:
        main()
    except Exception as exc:
        import traceback
        traceback.print_exc()
        input("...")
