from BaseImport import *

_font_title = Imf.truetype('arial.ttf', 72)
_font_text = Imf.truetype('arial.ttf', 32)


class _Button_Pressed(RuntimeError):
    def __init__(self, sth) -> None:
        super().__init__(
            f"a button has been pressed, who wants to return {sth}")
        self.sth = sth

    def __call__(self):
        return self.sth


class _BaseObject:
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


class _PureText:
    "纯文字生成器。生成一个充满了给定文字的透明背景的图片，直接调用对象即可获得。"

    def __init__(self, text: str, color: tuple,
                 font, maxcanavassize=(540, 360)) -> None:
        "参数列表：text, color文字颜色, font, maxcanavassize最大画布大小（生成图片的尺寸不超过它）"
        self.text = str(text)
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
        if self._min_l >= self._max_r or self._min_t >= self._max_b:
            input("!!!")
            return Im.new('RGBA', (1, 1))
        self.result = self.image.crop(
            (self._min_l, self._min_t, self._max_r, self._max_b))
        return self.result


def _sep_text(source: str, widthlimit: int, font: Imf.FreeTypeFont, *, rootrecursion=True):
    "根据宽度限制给文本分段"
    im = _PureText(source, (255,)*4, font, (widthlimit+50, 200))()
    if im.width <= widthlimit:
        return source
    i_min = 2
    i_max = len(source)
    while i_max-i_min > 1:
        i = (i_max+i_min)//2
        im = _PureText(source[:i], (255,)*4, font, (widthlimit+50, 200))()
        if im.width <= widthlimit:
            i_min = i
        else:
            i_max = i
    return source[:i_min]+'\n'+_sep_text(source[i_min:], widthlimit, font, rootrecursion=False)


class _Color:
    "综合了颜色和图片的小模块，方便从纯色填充到图片填充的更新换代。"
    MODE_COLOR = 0
    MODE_PICTURE = 1

    def __init__(self, color):
        if type(color) == _Color:
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
            return f"_Color({self.property})"
        else:
            return f"_Color{self.property}"


class _Button(_BaseObject):
    "一个按钮，阉割版。纯色填充。"

    def __init__(self, window: pg.Surface, pos: tuple, size: tuple, color: _Color,
                 text: _PureText, callfunc=lambda *args: None) -> None:
        self.pos = pos
        self.size = size
        self.window = window
        self.color = _Color(color)
        self.text = text
        self.callfunc = callfunc
        self.pressed = False

        _pt = _PureText(_sep_text(
            self.text.text, self.size[0]-20, self.text.font), self.text.color, self.text.font, self.size)
        self.textimg = _pt()
        del _pt

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
                if self.touchmouse():
                    self.pressed = True
                    return True
        elif event.type == pg.MOUSEBUTTONUP:
            if self.pressed:
                self.pressed = False
                self.callfunc()
        elif self.pressed:
            # mouse_pos = pg.mouse.get_pos()
            if not self.touchmouse():
                self.pressed = False

    def show(self, window: pg.Surface = None, pos: tuple = None):
        "显示这个按钮，并刷新自己的位置。\n参数列表：window, pos"
        if self.pressed:
            self.image = self.cover1
        else:
            self.image = self.cover0
        super().show(window, pos)


class Confirm_Notice:
    def __init__(self, text: str, title="Notice", opts=["Yes", "No"], optdict={0: True, 1: False},
                 width=round(SCREEN_SIZE[0]*0.618), height=round(SCREEN_SIZE[1]*0.618)):
        "call mainloop to return optdict[opts.index(<Your choice>)]"
        self.text = text
        self.title = title
        self.opts = opts
        self.optdict = optdict
        self.objects = []
        self.width = width
        self.height = height
        self.offset = (SCREEN_SIZE[0]//2-width//2, SCREEN_SIZE[1]//2-height//2)

        self.objects.append(_Button(root, self.offset, (self.width, 100),
                                    (255, 200, 0), _PureText(self.title, (0, 0, 0, 255), _font_title)))
        self.objects.append(_Button(root, (self.offset[0], self.offset[1]+100), (self.width, self.height-160),
                                    (255, 255, 160), _PureText(text, (0, 0, 0, 255), _font_text)))

        def _button_return(sth):
            def _func():
                raise _Button_Pressed(sth)
            return _func

        _l = len(self.opts)
        if _l == 1:
            self.objects.append(_Button(root, (self.offset[0]+self.width//4, self.offset[1]+height-55),
                                        (self.width//2, 50), (0, 180,
                                                              0), _PureText(self.opts[0], (255,)*4, _font_text),
                                        _button_return(self.optdict[0])))
        else:
            _w = (width-20*(_l+1))//_l
            for _i in range(_l):
                self.objects.append(_Button(root, (self.offset[0]+20*(_i+1)+_w*_i, self.offset[1]+height-55),
                                            (_w, 50), (round(180*_i/(_l-1)),
                                                       round(180*(_l-_i-1)/(_l-1)), 0),
                                            _PureText(self.opts[_i], (255,)*4, _font_text), _button_return(self.optdict[_i])))

    def mainloop(self):
        root.blit(im2pg(Im.new('RGBA', SCREEN_SIZE, (0, 0, 0, 100))), (0, 0))
        clock = pg.time.Clock()
        try:
            while True:
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        pg.quit()
                        raise SystemExit
                    for obj in self.objects[::-1]:
                        if obj.handleEvent(event):
                            break
                for obj in self.objects:
                    obj.show()
                pg.display.flip()
                clock.tick(FPS)
        except _Button_Pressed as exc:
            return exc()


class Error_Notice:
    def __init__(self, text: str, title="Error",
                 width=round(SCREEN_SIZE[0]*0.618), height=round(SCREEN_SIZE[1]*0.618)):
        "call mainloop to return True"
        self.text = text
        self.title = title
        self.objects = []
        self.width = width
        self.height = height
        self.offset = (SCREEN_SIZE[0]//2-width//2, SCREEN_SIZE[1]//2-height//2)

        self.objects.append(_Button(root, self.offset, (self.width, 100),
                                    (255, 100, 100), _PureText(self.title, (0, 0, 0, 255), _font_title)))
        self.objects.append(_Button(root, (self.offset[0], self.offset[1]+100), (self.width, self.height-160),
                                    (255, 200, 200), _PureText(text, (0, 0, 0, 255), _font_text)))

        def _func():
            raise _Button_Pressed(True)

        self.objects.append(_Button(root, (self.offset[0]+self.width//4, self.offset[1]+height-55),
                                    (self.width//2, 50), (255, 174, 201, 255),
                                    _PureText("OK", (255,)*4, _font_text), _func))

    def mainloop(self):
        root.blit(im2pg(Im.new('RGBA', SCREEN_SIZE, (0, 0, 0, 100))), (0, 0))
        clock = pg.time.Clock()
        try:
            while True:
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        pg.quit()
                        raise SystemExit
                    for obj in self.objects[::-1]:
                        if obj.handleEvent(event):
                            break
                for obj in self.objects:
                    obj.show()
                pg.display.flip()
                clock.tick(FPS)
        except _Button_Pressed as exc:
            return exc()


class Info_Notice:
    def __init__(self, text: str, title="Info",
                 width=round(SCREEN_SIZE[0]*0.618), height=round(SCREEN_SIZE[1]*0.618)):
        "call mainloop to return True"
        self.text = text
        self.title = title
        self.objects = []
        self.width = width
        self.height = height
        self.offset = (SCREEN_SIZE[0]//2-width//2, SCREEN_SIZE[1]//2-height//2)

        self.objects.append(_Button(root, self.offset, (self.width, 100),
                                    (80, 80, 255), _PureText(self.title, (255,)*4, _font_title)))
        self.objects.append(_Button(root, (self.offset[0], self.offset[1]+100), (self.width, self.height-160),
                                    (200, 200, 255), _PureText(text, (0, 0, 0, 255), _font_text)))

        def _func():
            raise _Button_Pressed(True)

        self.objects.append(_Button(root, (self.offset[0]+self.width//4, self.offset[1]+height-55),
                                    (self.width//2, 50), (255, 200, 255, 255),
                                    _PureText("Confirm", (0, 0, 0, 255), _font_text), _func))

    def mainloop(self):
        root.blit(im2pg(Im.new('RGBA', SCREEN_SIZE, (0, 0, 0, 100))), (0, 0))
        clock = pg.time.Clock()
        try:
            while True:
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        pg.quit()
                        raise SystemExit
                    for obj in self.objects[::-1]:
                        if obj.handleEvent(event):
                            break
                for obj in self.objects:
                    obj.show()
                pg.display.flip()
                clock.tick(FPS)
        except _Button_Pressed as exc:
            return exc()
