from math import ceil
from PIL import Image as Im, ImageDraw as Imd, ImageFont as Imf
import pygame as pg
from time import time
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
focused = None
main = None
refresh = True


def im2pg(im: Im.Image):
    return pg.image.frombuffer(im.tobytes(), im.size, im.mode)


def init():
    global root, screen_size, background_im
    pg.init()
    root = pg.display.set_mode(flags=pg.FULLSCREEN | pg.RESIZABLE)
    screen_size = pg.display.get_desktop_sizes()[0]
    background_im = im2pg(Im.new('RGBA', screen_size, (0, 0, 0, 255)))
    pg.display.set_caption("FSTimer3(beta)")


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
        if focused is None and event.type == pg.MOUSEBUTTONDOWN:
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
        elif focused is None and event.type == pg.KEYDOWN:
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
    def __init__(self, scroller: Scroller) -> None:
        super().__init__(pg.Rect(0, 0, 1, 1))
        self.scroller = scroller
        self.records = []  # Format: (alltime, duration, timetype)
        self.next_index = 1  # 下一条工作记录的序号是多少
        self._element_extend = None  # 作为拓展暂时存在records中的那个

        try:
            with open(DataPath/FILENAME, 'r') as file:
                self.begintime, self.records = eval(file.read())
        except:
            self.begintime = time()
            self.records.append((0, 0, 0))

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
        self._extend()

    def record(self, timetype):
        global refresh
        refresh = True
        now = time()
        self.records.append((now-self.begintime,
                             now-self.begintime-self.records[-1][0], timetype))
        self.scroller.remove(self._element_extend)
        self._element_extend = None
        self.scroller.append(RecordBar(
            self.next_index, self.records[-1][0], self.records[-1][1], self.records[-1][2]
        ))
        if self.records[-1][2] == WORK:
            self.next_index += 1

        with open(DataPath/FILENAME, 'w') as file:
            file.write(f"{self.begintime}, {self.records}")

    def _extend(self):
        if self._element_extend is not None:
            raise RuntimeError("extend element has not been removed")
        self._element_extend = RecordBar(self.next_index, '', '', self.type)
        self.scroller.append(self._element_extend)
        self.scroller.manage()

    def handleEvent(self, event):
        if event.type == pg.KEYDOWN:
            if event.key in [pg.K_SPACE, pg.K_RETURN]:
                self.record(self.type)
                if self.type == WORK:
                    self.type = REST
                elif self.type == REST:
                    self.type = WORK
                else:
                    self.type = WORK
                self._extend()

    def refresh(self):
        if refresh:
            self.image = im2pg(self.pic)
            return True
        return False


class MyTicker(BaseObject):
    def __init__(self, timer: MyTimer):
        super().__init__(pg.Rect(720, 420, 320, 80),  [])
        self.timer = timer
        self.time = 0
        self.updown = False
        self.downdown = False
        self.leftdown = False
        self.rightdown = False
        self.text = ""
        self.mousedown = False
        self.mousespeed = [0, 0]  # 鼠标拖动的速度
        self._micro_refresh = False
        self._old_rel = [0, 0]

    def handleEvent(self, event):
        global focused
        super().handleEvent(event)
        if event.type == pg.KEYDOWN:
            if focused is self:
                if event.key == pg.K_UP:
                    self.updown = True
                    if self.downdown:
                        self.mousespeed[1] = 0
                    else:
                        self.mousespeed[1] = -10
                    return True
                elif event.key == pg.K_DOWN:
                    self.downdown = True
                    if self.updown:
                        self.mousespeed[1] = 0
                    else:
                        self.mousespeed[1] = 10
                    return True
                elif event.key == pg.K_LEFT:
                    self.leftdown = True
                    if self.rightdown:
                        self.mousespeed[0] = 0
                    else:
                        self.mousespeed[0] = -10
                    return True
                elif event.key == pg.K_RIGHT:
                    self.rightdown = True
                    if self.leftdown:
                        self.mousespeed[0] = 0
                    else:
                        self.mousespeed[0] = 10
                    return True
            if event.key in [pg.K_f, pg.K_ESCAPE, pg.K_F11]:
                if self.rect.right > screen_size[0]:
                    self.rect.right = screen_size[0]
                elif self.rect.bottom > screen_size[1]:
                    self.rect.bottom = screen_size[1]
        elif event.type == pg.KEYUP:
            if event.key == pg.K_UP:
                if self.updown is True and self.downdown is False:
                    self.mousespeed[1] = -10
                self.updown = False
            elif event.key == pg.K_DOWN:
                if self.downdown is True and self.updown is False:
                    self.mousespeed[1] = 10
                self.downdown = False
            elif event.key == pg.K_LEFT:
                if self.leftdown is True and self.rightdown is False:
                    self.mousespeed[0] = -10
                self.leftdown = False
            elif event.key == pg.K_RIGHT:
                if self.rightdown is True and self.leftdown is False:
                    self.mousespeed[0] = 10
                self.rightdown = False
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            # print(f"mouse in self: {pg.mouse.get_pos() in self}")
            if pg.mouse.get_pos() in self:
                self.mousedown = True
                focused = self
                return True
            else:
                focused = None
                return False
        elif event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                if self.mousedown:
                    self.mousespeed = [i*2 for i in self._old_rel]
                    self._old_rel = [0, 0]
                    if self.rect.right > screen_size[0]:
                        self.rect.right = screen_size[0]
                    elif self.rect.bottom > screen_size[1]:
                        self.rect.bottom = screen_size[1]
            self.mousedown = False
        elif event.type == pg.WINDOWLEAVE:
            if self.mousedown:
                self.mousespeed = [i*2 for i in self._old_rel]
                self._old_rel = [0, 0]
                if self.rect.right > screen_size[0]:
                    self.rect.right = screen_size[0]
                elif self.rect.bottom > screen_size[1]:
                    self.rect.bottom = screen_size[1]
            self.mousedown = False
        elif self.mousedown and event.type == pg.MOUSEMOTION:
            self._old_rel = list(event.rel)
            self.rect.left += event.rel[0]
            self.rect.top += event.rel[1]
            global refresh
            refresh = True
            return True
        elif event.type == pg.WINDOWRESIZED:
            if self.rect.right > screen_size[0]:
                self.rect.right = screen_size[0]
            elif self.rect.bottom > screen_size[1]:
                self.rect.bottom = screen_size[1]

    def tick(self):
        global refresh
        super().tick()
        # print(f"\rmousedown:{self.mousedown}; mousespeed:{[round(i,2) for i in self.mousespeed]}", end='\t')
        if not self.mousedown and any(self.mousespeed):
            self.rect.left += round(self.mousespeed[0])
            self.rect.top += round(self.mousespeed[1])
            if abs(self.mousespeed[0]) < 0.7:
                self.mousespeed[0] = 0
            if abs(self.mousespeed[1]) < 0.7:
                self.mousespeed[1] = 0
            if not self.leftdown and not self.rightdown:
                self.mousespeed[0] *= 0.8
            if not self.updown and not self.downdown:
                self.mousespeed[1] *= 0.8
            refresh = True
            # 边缘碰撞检测
            if self.rect.right > screen_size[0]:
                self.rect.right = screen_size[0]
                if self.rightdown:
                    self.mousespeed[0] = 0
                elif self.mousespeed[0] > 0:
                    self.mousespeed[0] *= -0.9
            elif self.rect.bottom > screen_size[1]:
                self.rect.bottom = screen_size[1]
                if self.downdown:
                    self.mousespeed[1] = 0
                elif self.mousespeed[1] > 0:
                    self.mousespeed[1] *= -0.9
            elif self.rect.left < 0:
                self.rect.left = 0
                if self.leftdown:
                    self.mousespeed[0] = 0
                elif self.mousespeed[0] < 0:
                    self.mousespeed[0] *= -0.9
            elif self.rect.top < 0:
                self.rect.top = 0
                if self.updown:
                    self.mousespeed[1] = 0
                elif self.mousespeed[1] < 0:
                    self.mousespeed[1] *= -0.9

        self.time = time()-self.timer.begintime-self.timer.records[-1][0]
        new_text = to_time(self.time)[:-1]
        if self.text != new_text:
            if not refresh:
                self._micro_refresh = True
            self.text = new_text
            self.pic = Im.new("RGBA", self.rect.size, (153, 217, 234, 64))
            Imd.Draw(self.pic).text((10, 10), self.text,
                                    COLORS[self.timer.type], LFONT)

    def refresh(self):
        out = super().refresh()
        if out:
            self._micro_refresh = False
        if self._micro_refresh:
            self.image = im2pg(self.pic)
            return False
        return out


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
        self.ticker = MyTicker(self.timer)
        self.objects = [self.scroller, self.timer, self.ticker]
        self.demaximize = False
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
                        if event.type == pg.WINDOWMAXIMIZED:
                            if not self.demaximize:
                                pg.display.set_mode(
                                    (0, 0), pg.FULLSCREEN | pg.RESIZABLE)
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
                                    self.demaximize = True
                                elif event.key not in [pg.K_ESCAPE]:
                                    pg.display.set_mode(
                                        (0, 0), pg.FULLSCREEN | pg.RESIZABLE)
                                    screen_size = root.get_size()
                                    self.scroller.manage()
                            elif event.key in [pg.K_q]:
                                pg.quit()
                                exit()
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
            elif self.ticker._micro_refresh:
                root.blit(background_im, self.ticker.rect)
                for obj in self.objects:
                    obj.show()
                pg.display.update(self.ticker.rect)
                self.ticker._micro_refresh = False
            self.demaximize = False


if __name__ == "__main__":
    Main().mainloop()
