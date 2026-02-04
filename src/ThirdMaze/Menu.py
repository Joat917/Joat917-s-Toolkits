from BaseImport import *
from ErrorNotice import *


class BaseObject:
    def __init__(self, pos: tuple, size: tuple):
        self.pos = pos
        self.size = size
        self.rect = pg.rect.Rect(*self.pos, *self.size)
        self.image = pg.Surface(self.size).convert_alpha()
        pass

    def handleEvent(self, event: pg.event.Event):
        return False

    def show(self, window: pg.Surface = None, pos: tuple = None):
        if window is not None:
            self.window = window
        if pos is not None:
            self.pos = pos
        self.rect = pg.rect.Rect(*self.pos, *self.size)
        self.window.blit(self.image, self.rect)
        return

    def touchmouse(self):
        "固连在主屏幕上的按钮"
        mousepos = pg.mouse.get_pos()
        return self.pos[0] < mousepos[0] < self.pos[0]+self.size[0] \
            and self.pos[1] < mousepos[1] < self.pos[1]+self.size[1]

    def touchmouse_offset(self):
        "连在选项卡上的按钮"
        mousepos = pg.mouse.get_pos()
        mousepos = mousepos[0]-self.row.pos[0] - \
            self.sw.pos[0], mousepos[1]-self.row.pos[1]-self.sw.pos[1]
        return self.pos[0] < mousepos[0] < self.pos[0]+self.size[0] \
            and self.pos[1] < mousepos[1] < self.pos[1]+self.size[1]


class PureText:
    "纯文字生成器。生成一个充满了给定文字的透明背景的图片，直接调用对象即可获得。"

    def __init__(self, text: str, color: tuple,
                 *, font=Imf.truetype('arial.ttf', 32), maxcanavassize=(540, 360)) -> None:
        "参数列表：text, color文字颜色, font, maxcanavassize最大画布大小（生成图片的尺寸不超过它）"
        self.text = text
        self.color = color
        self.font = font
        self.maxcanavassize = maxcanavassize

    def _check(self, x, y):
        if self.image.getpixel((x, y))[3] > 16:
            self._max_r = max(self._max_r, x)
            self._max_b = max(self._max_b, y)
            self._min_l = min(self._min_l, x)
            self._min_t = min(self._min_t, y)

    def __call__(self):
        self.image = Im.new("RGBA", self.maxcanavassize)
        Imd.Draw(self.image).text((0, 0), self.text, self.color, self.font)

        self._max_r = 0
        self._max_b = 0
        self._min_l = self.image.width
        self._min_t = self.image.height
        for y in range(self.image.size[1]):
            for x in range(self.image.size[0]):
                self._check(x, y)
        self._max_r += 1
        self._max_b += 1
        self.result = self.image.crop(
            (self._min_l, self._min_t, self._max_r, self._max_b))
        return self.result


class Color:
    "综合了颜色和图片的小模块，方便从纯色填充到图片填充的更新换代。"
    MODE_COLOR = 0
    MODE_PICTURE = 1

    def __init__(self, color):
        if type(color) == Color:
            self.mode = color.mode
            self.property = color.property
        elif type(color) == int:
            self.mode = self.MODE_COLOR
            self.property = (color, color, color, 255)
        elif type(color) == tuple:
            self.mode = self.MODE_COLOR
            if len(color) == 1:
                self.property = (color[0], color[0], color[0], 255)
            elif len(color) == 3:
                self.property = (color[0], color[1], color[2], 255)
            elif len(color) == 4:
                self.property = color
            else:
                raise ValueError("length of color not recognizable")
        elif type(color) == Im.Image:
            self.mode = self.MODE_PICTURE
            self.property = color.convert('RGBA')
        else:
            raise TypeError(f"inappropriate argument type: {type(color)}")

    def toImage(self, size: tuple):
        "生成一个图片"
        if self.mode == self.MODE_COLOR:
            return Im.new('RGBA', size, self.property)
        else:
            zoom = max(size[0]/self.property.size[0],
                       size[1]/self.property.size[1])
            im = Im.Image.resize(self.property, (round(zoom*self.property.size[0]),
                                                 round(zoom*self.property.size[1])), Im.Resampling.NEAREST)
            return im.crop((0, 0, *size))

    def blacken(self, size: tuple):
        "生成一个黑化的图片，用于按下的按钮"
        if self.mode == self.MODE_COLOR:
            color = self.property[:3]+(255-self.property[3],)
            color = tuple(round(sqrt(i*i+2500)-50) for i in color)
            color = color[:3]+(255-color[3],)
            return Im.new('RGBA', size, color)
        else:
            zoom = max(size[0]/self.property.size[0],
                       size[1]/self.property.size[1])
            im = Im.Image.resize(self.property, (round(zoom*self.property.size[0]),
                                                 round(zoom*self.property.size[1])), Im.Resampling.NEAREST)
            im = im.crop((0, 0, *size))
            im.paste((0, 0, 0, 255), (0, 0, *size), Im.new('L', size, 50))
            return im

    def fillsurface(self, surface: pg.Surface):
        "把给的surface染上图片的颜色"
        surface.fill((0, 0, 0, 0))
        return surface.blit(im2pg(self.toImage(surface.get_size())), (0, 0))

    def __repr__(self):
        if self.mode == self.MODE_COLOR:
            return f"Color({self.property})"
        else:
            return f"Color{self.property}"


class Button(BaseObject):
    "一个按钮，每次显示的时候可以改变自己的位置。纯色填充。"

    def __init__(self, window: pg.Surface, pos: tuple, size: tuple, color: Color,
                 text: str, textcolor: tuple = (255, 255, 255, 255),
                 callfunc=lambda *args: None, row=None,  args=(), kwargs={}, reporterr=True) -> None:
        """参数列表：
window：想要把按钮附着的pygame对象；
pos：位置(x,y)；size：大小(x,y)；color按钮本身的颜色(r,g,b,a)；
text：显示的文字；textcolor文字的颜色(r,g,b,a)；
callfunc，点击按钮的时候会调用的函数；
row，选项卡，用于判断是否点击；
*args, **kwargs：调用函数的时候传入的参数"""
        super().__init__(pos, size)
        self.window = window
        self.color = Color(color)
        self.text = text
        self.textcolor = textcolor
        self.callfunc = callfunc
        self.row = row
        self.args = args
        self.kwargs = kwargs
        self.reporterr = reporterr
        self.pressed = False

        self.textimg = PureText(self.text, self.textcolor,
                                maxcanavassize=self.size)()

        self.image0 = self.color.toImage(self.size)
        self.image1 = self.color.blacken(self.size)

        self.image0.paste(self.textimg, ((self.image0.size[0]-self.textimg.size[0])//2,
                                         (self.image0.size[1]-self.textimg.size[1])//2), self.textimg.getchannel('A'))
        self.image1.paste(self.textimg, ((self.image1.size[0]-self.textimg.size[0])//2,
                                         (self.image1.size[1]-self.textimg.size[1])//2), self.textimg.getchannel('A'))

        self.cover0 = im2pg(self.image0)
        self.cover1 = im2pg(self.image1)

    def handleEvent(self, event: pg.event.Event):
        "用于判断按钮是否被按下，并在鼠标抬起的时候激活按钮。\n\
返回：这个event是否引起了动作"
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = pg.mouse.get_pos()
                if (self.touchmouse() if self.row is None else self.touchmouse_offset()):
                    self.pressed = True
                    return True
        elif event.type == pg.MOUSEBUTTONUP:
            if self.pressed:
                self.pressed = False
                if self.reporterr:
                    try:
                        self.callfunc(*self.args, **self.kwargs)
                    except GameExit or SystemExit as exc:
                        raise exc
                    except Exception as exc:
                        print_exc()
                        Error_Notice(f"{str(type(exc))[8:-2]}: \n{exc}").mainloop()
                else:
                    self.callfunc(*self.args, **self.kwargs)
        elif self.pressed:
            # mouse_pos = pg.mouse.get_pos()
            if not (self.touchmouse() if self.row is None else self.touchmouse_offset()):
                self.pressed = False

    def show(self, window: pg.Surface = None, pos: tuple = None):
        "显示这个按钮，并刷新自己的位置。\n参数列表：window, pos"
        if self.pressed:
            self.image = self.cover1
        else:
            self.image = self.cover0
        super().show(window, pos)


class Text(BaseObject):
    "一个文本框。y方向上自动文本居中，x方向上可以自由给定对齐方式。"
    LEFT = 'left'
    CENTER = 'center'
    RIGHT = 'right'

    def __init__(self, pos: tuple, size: tuple, text_info: PureText, align=CENTER) -> None:
        "参数列表：pos文本框位置；size文本框大小；text_info使用一个PureText对象打包所有对文字的要求；align对齐方式"
        super().__init__(pos, size)
        self.textimg = text_info()
        self.align = align
        self.textsurface = im2pg(self.textimg)

        self.surface = pg.Surface(self.size).convert_alpha()
        self.surface.fill((0, 0, 0, 0))
        y = (self.size[1]-self.textimg.size[1])//2
        if align == self.LEFT:
            x = 0
        elif align == self.RIGHT:
            x = self.size[0]-self.textimg.size[0]
        elif align == self.CENTER:
            x = (self.size[0]-self.textimg.size[0])//2
        else:
            raise ValueError(f"align unrecognizable: {self.align}")
        self.surface.blit(self.textsurface, (x, y))

    def show(self, window: pg.Surface, pos: tuple = None):
        self.image = self.surface
        super().show(window, pos)


class Row(BaseObject):
    "选项卡，必须和滚动窗口一起使用。可以放一些文本和按钮进去。"

    def __init__(self, pos: tuple, size: tuple,  backgroundcolor: Color, objects: list = []):
        """参数列表：
pos相对主页面的位置；size一个长条的大小；
backgroundcolor：未涂色处的颜色
objects：所有要放入的object，使用相对滑动条的位置。
        """

        super().__init__(pos, size)
        self.backgroundcolor = Color(backgroundcolor)
        self.objects = objects
        for obj in self.objects:
            obj.row = self

        self.surface = pg.Surface(self.size).convert_alpha()
        self.surface.fill((0, 0, 0, 0))
        pass

    def handleEvent(self, event: pg.event.Event):
        for obj in self.objects[::-1]:
            if obj.handleEvent(event):
                return True

    def show(self, window: pg.Surface = None, pos: tuple = None):
        self.image = self.surface
        self.backgroundcolor.fillsurface(self.surface)
        for obj in self.objects:
            obj.show(window=self.surface)
        super().show(window, pos)


class ScrollWindow(BaseObject):
    "滚动窗口，把选项卡放进去，所有的东西必须经过选项卡再放入。"

    def __init__(self, pos: tuple, size: tuple, rows: list, backgroundcolor: Color, gap: int = 5):
        super().__init__(pos, size)
        self.window = None
        self.rows = rows
        for row in self.rows:
            row.sw = self
            for obj in row.objects:
                obj.sw = self
        self.backgroundcolor = Color(backgroundcolor)
        self.gap = gap

        self.surface = pg.Surface(self.size).convert_alpha()
        self.surface.fill((0, 0, 0, 0))

        self.scolllimit = sum([row.size[1] for row in self.rows])\
            + self.gap*(len(self.rows)+1)-self.size[1]
        if self.scolllimit < 0:
            self.scolllimit = 0

        self.scrollindex = 0
        self.index_mouse_sum = None

    def handleEvent(self, event: pg.event.Event):
        for row in self.rows:
            if row.handleEvent(event):
                return True
        if self.scolllimit:
            if event.type == pg.MOUSEBUTTONDOWN:
                mouse_pos = pg.mouse.get_pos()
                if self.touchmouse():
                    if event.button == 4:
                        self.scrollindex -= 25
                        return True
                    elif event.button == 5:
                        self.scrollindex += 25
                        return True
                    elif event.button in [1, 3]:
                        self.index_mouse_sum = self.scrollindex + mouse_pos[1]
                        return True
            elif event.type == pg.MOUSEBUTTONUP:
                self.index_mouse_sum = None

    def show(self, window: pg.Surface = None, pos: tuple = None):
        if self.scolllimit:
            if self.index_mouse_sum is not None:
                self.scrollindex = self.index_mouse_sum-pg.mouse.get_pos()[1]
            if self.scrollindex < 0:
                self.scrollindex = 0
            elif self.scrollindex > self.scolllimit:
                self.scrollindex = self.scolllimit

        self.backgroundcolor.fillsurface(self.surface)
        y_current = self.gap-self.scrollindex
        for i in range(len(self.rows)):
            row = self.rows[i]
            if y_current+self.gap+row.size[1] < 0:
                y_current += self.gap+row.size[1]
                continue
            else:
                row.show(self.surface, (self.gap, y_current))
                y_current += self.gap+row.size[1]
            if y_current >= self.size[1]:
                break

        self.image = self.surface
        super().show(window, pos)


class InputBox(BaseObject):
    "InputBox"

    def __init__(self, pos: tuple, size: tuple, default_text: str = "Input Something...", callback=lambda: None):
        super().__init__(pos, size)
        self.default_text = default_text
        self.callback = callback
        self.result = ''
        self._text_old = ''
        self.cover0 = im2pg(Im.new('RGBA', self.size, (255, 255, 255, 64)))
        self.cover1 = im2pg(Im.new('RGBA', self.size, (255, 255, 255, 216)))
        self.text = Text((0, 0), self.size, PureText(
            default_text, (127, 127, 127, 216)), Text.LEFT)

        self.pressed = False
        self.activated = False
        self.lshift_down = False
        self.rshift_down = False
        self.tick = 0
        self.__tick_show_cycle = 0

        self.SHIFT_DICT = {("`1234567890-=[]\;',./"+''.join([chr(j) for j in range(97, 123)]))[i]: (
            '~!@#$%^&*()_+{}|:"<>?'+''.join([chr(j) for j in range(65, 91)]))[i] for i in range(47)}

    def _get_text(self):
        if self.result:
            self.__tick_show_cycle += 1/FPS
            if self.__tick_show_cycle < 0.5:
                return self.result[:self.tick]+"I"+self.result[self.tick:]
            elif 0.5 < self.__tick_show_cycle < 1:
                return self.result[:self.tick]+" "+self.result[self.tick:]
            else:
                self.__tick_show_cycle = 0
                return self.result[:self.tick]+"I"+self.result[self.tick:]
        else:
            return self.default_text

    def handleEvent(self, event: pg.event.Event):
        "用于判断按钮是否被按下，并在鼠标抬起的时候激活按钮。\n\
返回：这个event是否引起了动作"
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                if (self.touchmouse() if self.row is None else self.touchmouse_offset()):
                    self.pressed = True
                    return True
                elif self.activated:
                    self.activated = False
                    return True
        elif event.type == pg.MOUSEBUTTONUP:
            if self.pressed:
                self.pressed = False
                self.activated = True
        elif event.type == pg.MOUSEMOTION:
            if self.pressed:
                if not (self.touchmouse() if self.row is None else self.touchmouse_offset()):
                    self.pressed = False
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_LSHIFT:
                self.lshift_down = True
            elif event.key == pg.K_RSHIFT:
                self.rshift_down = True
            if self.activated:
                if event.key in range(32, 126):
                    if self.lshift_down or self.rshift_down:
                        self.result = self.result[:self.tick] +\
                            self.SHIFT_DICT[chr(event.key)] +\
                            self.result[self.tick:]
                    else:
                        self.result = self.result[:self.tick] +\
                            chr(event.key)+self.result[self.tick:]
                    self.tick += 1
                    return True
                elif event.key == pg.K_BACKSPACE:
                    if self.tick <= 0:
                        self.tick = 0
                    else:
                        self.result = self.result[:self.tick-1] +\
                            self.result[self.tick:]
                        self.tick -= 1
                    return True
                elif event.key == pg.K_DELETE:
                    self.result = self.result[:self.tick] +\
                        self.result[self.tick+1:]
                    return True
                elif event.key == pg.K_HOME:
                    self.tick = 0
                    return True
                elif event.key == pg.K_END:
                    self.tick = len(self.result)
                    return True
                elif event.key == pg.K_LEFT:
                    if self.tick > 0:
                        self.tick -= 1
                    else:
                        self.tick = 0
                    return True
                elif event.key == pg.K_RIGHT:
                    if self.tick < len(self.result):
                        self.tick += 1
                    else:
                        self.tick = len(self.result)
                    return True
                elif event.key == pg.K_RETURN:
                    self.activated = False
                    try:
                        self.callback()
                    except GameExit or SystemExit as exc:
                        raise exc
                    except Exception as exc:
                        print_exc()
                        Error_Notice(f"{str(type(exc))[8:-2]}: \n{exc}").mainloop()
                    return True
        elif event.type == pg.KEYUP:
            if event.key == pg.K_LSHIFT:
                self.lshift_down = False
            elif event.key == pg.K_RSHIFT:
                self.rshift_down = False
    
    def get_result(self):
        if self.result:
            return self.result
        else:
            return self.default_text

    def show(self, window: pg.Surface = None, pos: tuple = None):
        if self.activated:
            self.image = self.cover1.copy()
        else:
            self.image = self.cover0.copy()
        if self._get_text() != self._text_old:
            self._text_old = self._get_text()
            if self.result == '':
                self.text.__init__((0, 0), self.text.size, PureText(
                    self._text_old, (127, 127, 127, 216)), Text.LEFT)
            else:
                self.text.__init__((0, 0), self.text.size, PureText(
                    self._text_old, (0, 0, 0, 216)), Text.LEFT)
        self.text.show(self.image, pos)
        return super().show(window, pos)

