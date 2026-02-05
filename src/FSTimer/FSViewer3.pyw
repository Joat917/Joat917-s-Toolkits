from math import ceil
from PIL import Image as Im, ImageDraw as Imd, ImageFont as Imf
import pygame as pg
from time import time
from sys import argv
from filepathpatch import DataPath

FPS_CODE = 200
FPS_DISPLAY = 25
DEFAULT_SCREEN_SIZE = (960, 540)
_FONT_STR = 'simkai.ttf'
FILENAME = 'TimerRecord.txt'

FONT = Imf.truetype(_FONT_STR, size=20)
LFONT = Imf.truetype(_FONT_STR, size=60)
_FPS_TIMES = FPS_CODE//FPS_DISPLAY

KEY_SHIFT_MAP = {
    "`1234567890-=[]\\;',./"[i]: "~!@#$%^&*()_+{}|:\"<>?"[i]
    for i in range(21)
}

WORK = 1
REST = 2
GAP = 0
TITLE = -1
COLORS = {WORK: (255, 127, 127, 255),
          REST: (127, 255, 0, 255),
          GAP: (127, 127, 127, 255),
          TITLE: (255, 255, 255, 255)}

screen_size = None
background_im = None
root = None
main = None
refresh = True


def im2pg(im: Im.Image):
    return pg.image.frombuffer(im.tobytes(), im.size, im.mode)


def init():
    global root, screen_size, background_im
    pg.init()
    root = pg.display.set_mode(DEFAULT_SCREEN_SIZE, flags=pg.RESIZABLE)
    screen_size = pg.display.get_window_size()
    background_im = im2pg(Im.new('RGBA', screen_size, (0, 0, 0, 255)))
    pg.display.set_caption("FSViewer3(beta)")


def to_time(x: float) -> str:
    if type(x) == str:
        return x
    elif x < 0:
        raise ValueError(
            f"TimeInterval less than 0. In function\"to_time\",x={x}")
    hr, _mnSc = divmod(x, 3600)
    mn, sc = divmod(_mnSc, 60)
    out = ""

    hr = round(hr)
    if hr == 0:
        out += "00"
    elif hr < 10:
        out += f"0{hr}"
    elif hr < 100:
        out += f"{hr}"
    elif hr < 1000:
        out += f"{hr//100}H"
    elif hr < 10000:
        out += f"{hr//1000}K"
    else:
        out += f"++"

    out += f":{int(mn)//10}{int(mn)%10}"
    out += f":{int(sc)//10}{int(sc)%10}.{int(sc*10)%10}{int(sc*100)%10}"
    return out


def restore_v2(content: bytes):
    OFFSET = 1689153536
    if content[:4] != b'FST\x02':
        raise RuntimeError("Invalid file type")
    content = content[4:]
    # 还原i2和i3
    l3 = content[0]
    content = content[1:]
    i3 = int.from_bytes(content[:l3], 'big')
    i2 = int.from_bytes(content[l3:], 'big')

    # 提取出i2(十二进制)和i3(三进制)
    dc2 = '0123456789.,'
    tx2 = ''
    while i2:
        tx2 = dc2[i2 % 12]+tx2
        i2 //= 12

    ls3 = []
    while i3:
        ls3.insert(0, i3 % 3)
        i3 //= 3

    # 还原ls2
    ls2 = eval(f"[{tx2}]")

    # ls3的开头很有可能是0，因此需要补0
    while len(ls2)-len(ls3) > 1:
        ls3.insert(0, 0)

    # 还原tm和ls
    tm = ls2[0]+OFFSET
    ls = [(0, 0, 0)]
    for i in range(len(ls2)-1):
        ls.append((ls[-1][0]+ls2[i+1], ls2[i+1], ls3[i]))

    # 还原原文件
    return tm, ls


class BaseObject:
    def __init__(self, rect: pg.Rect, objects=[], parent=None, pic=Im.new('RGBA', (1, 1))) -> None:
        self.rect = pg.Rect(rect)  # 定义了元素的相对位置和大小
        self.objects = objects  # 自己内部包含的子元素
        self.parent = parent  # 自己的父元素，便于判断绝对位置
        self.pic = pic  # 图片，打开refresh开关(global)刷新渲染
        self.image = None
        self._buffer_relpos = None
        self._buffer_abspos = None
        self._buffer_parent_pos = None
        for obj in self.objects:
            obj.parent = self

    def handleEvent(self, event: pg.event.Event):
        "处理事件，返回True停止事件传播"
        for obj in self.objects:
            if obj.handleEvent(event):
                return True
        return False

    def tick(self):
        "更新状态，返回True表示发生状态更新"
        out = False
        for obj in self.objects:
            out |= bool(obj.tick())
        return out

    def refresh(self):
        "从pic属性读取图片并且刷新包括所有子元素的显示。需要专门调用"
        global refresh
        out = False
        if refresh:
            self.image = im2pg(self.pic)
            out = True
            for obj in self.objects:
                out |= obj.refresh()
        return out

    def show(self):
        for obj in self.objects:
            obj.show()
        if self.image is None:
            self.image = im2pg(self.pic)
        root.blit(self.image, self.get_abspos())

    def append(self, obj):
        "加入子元素"
        obj.parent = self
        self.objects.append(obj)

    def remove(self, obj):
        "移除子元素"
        self.objects.remove(obj)

    def get_abspos(self):
        "得到自己在屏幕上的绝对位置"
        if self._buffer_abspos is None or self._buffer_relpos != (self.rect.left, self.rect.top):
            self._buffer_relpos = (self.rect.left, self.rect.top)
            if self.parent is None:
                self._buffer_abspos = self.rect.left, self.rect.top
                return self._buffer_abspos
            else:
                self._buffer_parent_pos = self.parent.get_abspos()
                self._buffer_abspos = self._buffer_parent_pos[0] + \
                    self.rect.left, self._buffer_parent_pos[1]+self.rect.top
                return self._buffer_abspos
        elif self.parent is not None and self.parent.get_abspos() != self._buffer_parent_pos:
            self._buffer_parent_pos = self.parent.get_abspos()
            self._buffer_abspos = self._buffer_parent_pos[0] + \
                self.rect.left, self._buffer_parent_pos[1]+self.rect.top
            return self._buffer_abspos
        else:
            return self._buffer_abspos

    def __contains__(self, __o):
        "判断一个坐标或者一个元素是否在自己里面"
        if type(__o) == tuple:
            if len(__o) == 2:
                abs_pos = self.get_abspos()
                return abs_pos[0] < __o[0] < abs_pos[0]+self.rect.width\
                    and abs_pos[1] < __o[1] < abs_pos[1]+self.rect.height
            else:
                raise ValueError(f"attempt to get ({__o} in BaseObject)")
        else:
            return __o in self.objects


class Scroller(BaseObject):
    def __init__(self, objects=[], pic=Im.new('RGBA', (1, 1))) -> None:
        "一个横向的滚动条"
        super().__init__(pg.Rect(0, 0, *screen_size), objects, None)
        self.offset = 0
        self.dragged = False
        self.mousespeed = 0  # 鼠标拖动的速度
        self.key = None  # 按下的按键向哪个方向，None|0|-1|1
        self._old_mouse_rel = None  # 最后一次mousemotion的rel

    def setOffset(self, _o):
        self.offset = _o
        self.rect.left = self.offset
        if self.offset < -self.rect.width:
            self.offset = -self.rect.width
        elif self.offset > screen_size[0]:
            self.offset = screen_size[0]

    def _altOffset(self, _d):
        # print(f"offset:{self.offset}")
        global refresh
        self.offset += _d
        self.offset = round(self.offset, 1)
        if self.offset < -self.rect.width:
            self.offset = -self.rect.width
        elif self.offset > screen_size[0]:
            self.offset = screen_size[0]
        self.rect.left = self.offset
        refresh = True

    def altOffset(self, _d):
        if self.dragged:
            self._altOffset(_d)
        else:
            self.mousespeed += _d

    def handleEvent(self, event: pg.event.Event):
        if super().handleEvent(event):
            return True
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.dragged = True
            elif event.button == 4:
                self.altOffset(2)
            elif event.button == 5:
                self.altOffset(-2)
        elif event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragged = False
                if self._old_mouse_rel is not None:
                    self.altOffset(self._old_mouse_rel)
                    self._old_mouse_rel = None
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_LEFT:
                self._altOffset(10)
                if self.key is None:
                    self.key = 1
                elif self.key == -1:
                    self.key = 0
            elif event.key == pg.K_RIGHT:
                self._altOffset(-10)
                if self.key is None:
                    self.key = -1
                elif self.key == 1:
                    self.key = 0
        elif event.type == pg.KEYUP:
            if event.key == pg.K_LEFT:
                if self.key == 1:
                    self.key = None
                    self.mousespeed = 10
                elif self.key == 0:
                    self.key = -1
            elif event.key == pg.K_RIGHT:
                if self.key == -1:
                    self.key = None
                    self.mousespeed = -10
                elif self.key == 0:
                    self.key = 1
        elif self.dragged and event.type == pg.MOUSEMOTION:
            self.mousespeed = 0
            self._altOffset(event.rel[0])
            self._old_mouse_rel = event.rel[0]

    def tick(self):
        out = super().tick()
        self._old_mouse_rel = None
        if self.key:
            self.altOffset(self.key*5)
            out = True
        if not self.dragged and self.mousespeed:
            self._altOffset(self.mousespeed)
            out = True
            if self.mousespeed:
                if abs(self.mousespeed) <= 1:
                    self.mousespeed = 0
                else:
                    self.mousespeed *= 0.8
        return out

    def manage(self, size=(360, 25)):
        "调整自身所有元素的位置"
        rowheight = size[1]
        colwidth = size[0]+20
        maxrows = screen_size[1]//size[1]
        if maxrows < 2:
            maxrows = 2
        needcols = ceil(len(self.objects)/maxrows)
        self.rect.width = colwidth*(1+needcols)-20
        for i in range(len(self.objects)):
            self.objects[i].rect.left = colwidth*(i//maxrows)
            self.objects[i].rect.top = rowheight*(i % maxrows)
        global refresh
        refresh = True


class RecordBar(BaseObject):
    SIZE = (360, 25)

    def __init__(self, index: str, totaltime: float, interval: float, timetype: int, parent=None) -> None:
        _pic = Im.new('RGBA', self.SIZE)
        if timetype in [GAP, REST]:
            index = '--'
        index = str(index)
        if len(index) < 2:
            index = '0'+index
        Imd.Draw(_pic).text(
            (0, 0), f"{index}    {to_time(totaltime)}    {to_time(interval)}", fill=COLORS[timetype], font=FONT)
        super().__init__(pg.Rect(0, 0, *self.SIZE), [], parent, _pic)

    def tick(self):
        return False

    def handleEvent(self, event):
        return False


class MyTimer(BaseObject):
    def __init__(self, scroller: Scroller, defaultFile=None) -> None:
        super().__init__(pg.Rect(0, 0, 1, 1))
        self.scroller = scroller
        self.records = []  # Format: (alltime, duration, timetype)
        self.next_index = 1  # 下一条工作记录的序号是多少
        self._element_extend = None  # 作为拓展暂时存在records中的那个

        record_get = False
        if defaultFile:
            try:
                with open(DataPath/defaultFile, 'r') as file:
                    self.begintime, self.records = eval(file.read())
                record_get = True
            except FileNotFoundError:
                pass
            except:
                try:
                    with open(DataPath/defaultFile, 'rb') as file:
                        self.begintime, self.records = restore_v2(file.read())
                    record_get = True
                except:
                    pass
        if not record_get and len(argv) > 1:
            for f in argv[1:]:
                try:
                    with open(DataPath/f, 'r') as file:
                        self.begintime, self.records = eval(file.read())
                    record_get = True
                    break
                except FileNotFoundError:
                    continue
                except:
                    try:
                        with open(DataPath/f, 'rb') as file:
                            self.begintime, self.records = restore_v2(
                                file.read())
                        record_get = True
                        break
                    except:
                        pass
        if not record_get:
            try:
                with open(DataPath/FILENAME, 'r') as file:
                    self.begintime, self.records = eval(file.read())
            except:
                self.begintime = time()
                self.records.append((0, 0, 0))
                self.records.append(('找不到记录时间的文件~', '', 1))

        self.type = GAP

        ###
        for i in range(len(self.records)):
            if i:
                self.scroller.append(
                    RecordBar(self.next_index, self.records[i][0], self.records[i][1], self.records[i][2]))
                if self.records[i][2] == WORK:
                    self.next_index += 1
            else:
                self.scroller.append(
                    RecordBar('序号', ' 累计   ', '   间隔  ', TITLE))
        self.scroller.manage()

    def refresh(self):
        if refresh:
            self.image = im2pg(self.pic)
            return True
        return False


class Main:
    def __init__(self) -> None:
        global main
        if main is not None:
            raise RuntimeError("Double main attempt")
        main = self
        init()
        self.clock = pg.time.Clock()
        self.scroller = Scroller()
        self.timer = MyTimer(self.scroller)
        self.objects = [self.scroller, self.timer]
        pass

    def mainloop(self):
        global screen_size, refresh, background_im
        while True:
            for _t in range(_FPS_TIMES):
                self.clock.tick(FPS_CODE)
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        pg.quit()
                        exit()
                    else:
                        if event.type == pg.WINDOWRESIZED:
                            screen_size = root.get_size()
                            if screen_size[0] > background_im.get_size()[0] or screen_size[1] > background_im.get_size()[1]:
                                background_im = im2pg(
                                    Im.new('RGBA', screen_size, (0, 0, 0, 255)))
                            self.scroller.manage()
                        if event.type == pg.KEYDOWN:
                            if event.key in [pg.K_f, pg.K_ESCAPE, pg.K_F11]:
                                if root.get_flags() & pg.FULLSCREEN:
                                    pg.display.set_mode(
                                        DEFAULT_SCREEN_SIZE, pg.RESIZABLE)
                                    screen_size = root.get_size()
                                    self.scroller.manage()
                                elif event.key not in [pg.K_ESCAPE]:
                                    pg.display.set_mode(
                                        (0, 0), pg.FULLSCREEN | pg.RESIZABLE)
                                    screen_size = root.get_size()
                                    self.scroller.manage()
                            elif event.key in [pg.K_q]:
                                pg.quit()
                                exit()
                        if event.type == pg.DROPFILE:
                            assert event.type == pg.DROPFILE
                            self.scroller.objects.clear()
                            self.timer.__init__(self.scroller, event.file)
                        for obj in self.objects[::-1]:
                            if obj.handleEvent(event):
                                break
                    pass
            for obj in self.objects:
                obj.tick()
            for obj in self.objects:
                obj.refresh()
            if refresh:
                root.blit(background_im, (0, 0))
                for obj in self.objects:
                    obj.show()
                pg.display.flip()
                refresh = False


Main().mainloop()
