from PIL import Image as Im, ImageDraw as Imd, ImageFont as Imf
from random import randint, shuffle
import os, sys
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame as pg
from math import sqrt
from time import time
from traceback import format_exc
from mswlib import MineFieldNoLosing, MineFieldAdvisor

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
FPS = 60
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_WIDTH)

MF_DEBUG = False
RECHECK_CHEAT = True # 如果打开此选项，自动建议将通过作弊的方式检查是否正确。因为打开此选项后不会误触雷区，所以可以极大提高爽感。
DENSE_ANALYSIS = False # 如果打开此选项，将试图完整求解所有解以评估每个格子的概率。会略微降低性能，关闭以提高爽感。

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
NUMBERS = "123456789abcdefghijklmnopqrstuvwxyz"

FONT_TITLE = Imf.truetype('simkai.ttf', 72)
FONT_TEXT = Imf.truetype('simkai.ttf', 32)
FONT_EMOJI = Imf.truetype('seguiemj.ttf', 32)

# colors
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
TRANSPARENT = (0, 0, 0, 0)
NUMBER_COLOR = {
    1: (0, 0, 255, 255),
    2: (0, 128, 0, 255),
    3: (255, 0, 0, 255),
    4: (0, 0, 128, 255),
    5: (128, 0, 0, 255),
    6: (0, 128, 128, 255),
    7: (0, 0, 0, 255),
    8: (128, 128, 128, 255),
}
FLAG_BGCOLOR = (153, 217, 234, 255)
MINE_BGCOLOR = (255, 128, 128, 255)
COLOR_HAZARD = (255, 128, 168, 255)
COLOR_SAFE = (181, 231, 29, 255)
BGCOLOR = (255, 180, 128, 255)
TEXTCOLOR_L = (34, 177, 76, 255)
TEXTCOLOR_M = (255, 127, 39, 255)
TEXTCOLOR_H = (237, 28, 36, 255)

evolution_alpha=0.5


def init():
    global root
    pg.init()
    pg.display.set_caption("Minesweeper 8")
    _ROOT = os.path.abspath(os.path.dirname(__file__))
    while 'src' not in os.listdir(_ROOT):
        _ROOT = os.path.dirname(_ROOT)
        if os.path.dirname(_ROOT) == _ROOT:
            raise FileNotFoundError("Cannot find 'src' directory.")
    pg.display.set_icon(pg.image.load(os.path.join(_ROOT, 'assets', 'icon.png')))
    root = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    return root


def quitgame():
    pg.quit()
    raise SystemExit


def im2pg(im: Im.Image):
    return pg.image.frombuffer(im.convert('RGBA').tobytes(), im.size, 'RGBA')


def clr(color) -> tuple:
    if type(color) == tuple:
        if len(color) == 3:
            return color+(255,)
        elif len(color) == 4:
            return color
        else:
            raise ValueError
    else:
        try:
            return color.convert('RGBA')
        except:
            Error_Notice("TypeError: color neither tuple nor image").mainloop()
            raise TypeError


class GameExit(RuntimeError):
    pass


class MinefieldWrapped:
    "用于对接旧逻辑接口的扫雷类"
    def __init__(self, cols: int, rows: int, mines: int, first_click=None) -> None:
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.minefield = MineFieldNoLosing(rows=rows, cols=cols, mines=mines, first_click_pos=(first_click[1]-1, first_click[0]-1) if (first_click is not None) else None)
        self.advisor = MineFieldAdvisor(self.minefield, dense_analysis=DENSE_ANALYSIS)
        self._buffer_suggestion = [[mines/(rows*cols) for _ in range(self.cols+2)] for _ in range(self.rows+2)]

    def dig(self, col: int, row: int):
        if MF_DEBUG:
            print(f"Dig: %i,%i" % (col, row))
        ret_val = m.run_dense_task(lambda:self.minefield.dig((row-1, col-1)), text=f"挖开({col},{row})...")
        if MF_DEBUG:
            print(self.minefield)
        return ret_val

    def sweep(self, col: int, row: int):
        """挖开一圈"""
        if MF_DEBUG:
            print(f"Sweep: %i,%i" % (col, row))
        ret_val = m.run_dense_task(lambda:self.minefield.digaround((row-1, col-1)), f"挖开({col},{row})周围...")
        if MF_DEBUG:
            print(self.minefield)
        return ret_val

    def flag(self, col: int, row: int):
        "插上或拔去旗子"
        if MF_DEBUG:
            print("Flag: %i,%i" % (col, row))
        ret_val = self.minefield.flag((row-1, col-1))
        if MF_DEBUG:
            print(self.minefield)
        return ret_val

    def fullflag(self, col: int, row: int):
        """插完一圈旗子"""
        return self.minefield.flagaround((row-1, col-1))
    
    def digall(self):
        for pos in self.minefield.all_places():
            if self.minefield.is_mine(pos):
                continue
            if self.minefield.is_flag(pos):
                self.minefield.flag(pos)
            m.run_dense_task(lambda:self.minefield.dig(pos), text=f"挖开({pos[1]+1},{pos[0]+1})...")
        return

    def safety(self):
        return not self.minefield.is_dead()

    def is_victory(self):
        return self.minefield.is_safe()

    def get_suggestion(self):
        if self.advisor._needs_recalculation():
            # self.advisor.analyze()
            m.run_dense_task(self.advisor.analyze, text="分析中...")
            for pos in self.minefield.all_places():
                row,col=pos
                if self.minefield.is_exposed(pos) or self.minefield.is_flag(pos):
                    self._buffer_suggestion[row+1][col+1] = None
                elif self.advisor.confident_suggestions[pos]==1:
                    self._buffer_suggestion[row+1][col+1] = 0
                elif self.advisor.confident_suggestions[pos]==2:
                    self._buffer_suggestion[row+1][col+1] = 1
                elif self.advisor.probability_suggestions[pos]!=-1:
                    self._buffer_suggestion[row+1][col+1] = self.advisor.probability_suggestions[pos]
                else:
                    self._buffer_suggestion[row+1][col+1] = None

    def conduct_suggestion(self):
        self.get_suggestion()
        if self.advisor.conflicting_positions:
            positions_string = '; '.join(f"{col+1},{row+1}" for row,col in self.advisor.conflicting_positions)
            Error_Notice(f"发现以下位置的数字无法得到满足：{positions_string}", "警告").mainloop()
            return
        changed = False
        for pos in self.minefield.all_places():
            if self.advisor.confident_suggestions[pos]==2:
                changed |= self.minefield.flag(pos)
            elif self.advisor.confident_suggestions[pos]==1:
                changed |= m.run_dense_task(lambda:self.minefield.dig(pos), text=f"挖开({pos[1]+1},{pos[0]+1})...")
        if changed:
            return
        
        import numpy as np
        # for action_threshold in np.arange(0.01, 1+1e-7, 0.01):
        #     if (self.advisor.probabilities_max>=0).any():
        #         min_of_max_probabilities = self.advisor.probabilities_max[self.advisor.probabilities_max>=0].min()
        #         if min_of_max_probabilities <= action_threshold:
        #             for pos in self.minefield.all_places():
        #                 if self.advisor.probability_suggestions[pos] != -1 and self.advisor.probabilities_min[pos]==min_of_max_probabilities:
        #                     # if RECHECK_DEBUG and self.minefield.is_mine(pos):
        #                     #     Error_Notice(f"想要挖去({pos[1]+1},{pos[0]+1})，但是发现这个地方有雷。", "警告").mainloop()
        #                     #     return
        #                     if not self.minefield.is_mine(pos):
        #                         changed |= m.run_dense_task(lambda:self.minefield.dig(pos), text=f"挖开({pos[1]+1},{pos[0]+1})")
        #                     if changed:
        #                         return
        #     if (self.advisor.probabilities_min>=0).any():
        #         max_of_min_probabilities = self.advisor.probabilities_min[self.advisor.probabilities_min>=0].max()
        #         if max_of_min_probabilities >= 1-action_threshold:
        #             for pos in self.minefield.all_places():
        #                 if self.advisor.probability_suggestions[pos] != -1 and self.advisor.probabilities_max[pos]==max_of_min_probabilities:
        #                     # if RECHECK_DEBUG and not self.minefield.is_mine(pos):
        #                     #     Error_Notice(f"想要插旗({pos[1]+1},{pos[0]+1})，但是发现这个地方没有雷。", "警告").mainloop()
        #                     #     return
        #                     if self.minefield.is_mine(pos):
        #                         changed |= self.minefield.flag(pos)
        #                     if changed:
        #                         return
        probabilities_ref = self.advisor.probability_suggestions.copy()
        probabilities_ref = np.where((probabilities_ref>=0) & (probabilities_ref<=1), probabilities_ref, np.nan)
        for _ in range(1000):
            try:
                pos_with_max_prob = np.unravel_index(np.nanargmax(probabilities_ref), probabilities_ref.shape)
            except ValueError:
                pos_with_max_prob = None
            try:
                pos_with_min_prob = np.unravel_index(np.nanargmin(probabilities_ref), probabilities_ref.shape)
            except ValueError:
                pos_with_min_prob = None
            if pos_with_max_prob is not None and pos_with_min_prob is not None:
                if probabilities_ref[pos_with_max_prob]+probabilities_ref[pos_with_min_prob]>1:
                    if not RECHECK_CHEAT or self.minefield.is_mine(pos_with_max_prob):
                        changed|= self.minefield.flag(pos_with_max_prob)
                    else:
                        probabilities_ref[pos_with_max_prob] = np.nan
                else:
                    if not RECHECK_CHEAT or not self.minefield.is_mine(pos_with_min_prob):
                        changed|= m.run_dense_task(lambda:self.minefield.dig(pos_with_min_prob), text=f"挖开({pos_with_min_prob[1]+1},{pos_with_min_prob[0]+1})...")
                    else:
                        probabilities_ref[pos_with_min_prob] = np.nan
            elif pos_with_max_prob is not None:
                if not RECHECK_CHEAT or self.minefield.is_mine(pos_with_max_prob):
                    changed|= self.minefield.flag(pos_with_max_prob)
                else:
                    probabilities_ref[pos_with_max_prob] = np.nan
            elif pos_with_min_prob is not None:
                if not RECHECK_CHEAT or not self.minefield.is_mine(pos_with_min_prob):
                    changed|= m.run_dense_task(lambda:self.minefield.dig(pos_with_min_prob), text=f"挖开({pos_with_min_prob[1]+1},{pos_with_min_prob[0]+1})...")
                else:
                    probabilities_ref[pos_with_min_prob] = np.nan
            else:
                break
            if changed:
                return
        
        Confirm_Notice("无事可做力（悲", "提醒", ["やりますね"]).mainloop()

    def is_cover(self, col, row):
        return self.minefield.is_covered((row-1, col-1))
    
    def is_suspected(self, col, row):
        return False
    
    def is_flag(self, col, row):
        return self.minefield.is_flag((row-1, col-1))
    
    def is_exposed(self, col, row):
        return self.minefield.is_exposed((row-1, col-1))

    def get_exposed_number(self, col, row):
        return self.minefield.get_exposed_number((row-1, col-1))
    
    def __iter__(self):
        for row in range(1,self.rows+1):
            for col in range(1,self.cols+1):
                yield col,row

    def __str__(self):
        return str(self.minefield)
    
    @property
    def suggestion(self):
        self.get_suggestion()
        return self._buffer_suggestion


class BaseObject:
    def __init__(self, main, position: tuple, size: tuple, color=None, window=None, objects=None) -> None:
        self.rect = pg.Rect(*position, *size)
        self.main = main
        self.window = window
        if self.window is None:
            self.window = root
        else:
            self.window = window

        if objects is None:
            self.objects = []
        else:
            self.objects = objects

        for obj in self.objects:
            obj.window = self

        if color is not None:
            self.color = clr(color)
            if type(self.color) == tuple:
                self.picture = Im.new('RGBA', self.rect.size, self.color)
            else:
                self.picture = self.color.resize(self.rect.size)
            self.image = im2pg(self.picture)
        else:
            self.image = None

    def handleEvent(self, event: pg.event.Event):
        if event.type == pg.QUIT:
            quitgame()
        flag = False
        for obj in self.objects[::-1]:
            if obj.handleEvent(event):
                flag = True
        return flag

    def tick(self):
        for obj in self.objects:
            obj.tick()
        pass

    def refresh(self):
        self.image = im2pg(self.picture)
        for obj in self.objects:
            obj.show()

    def show(self, *args):
        self.window.blit(self.image, self.rect)

    def blit(self, im: pg.Surface, dest: pg.Rect):
        return self.image.blit(im, dest)

    def _get_abspos(self):
        if self.window == root:
            return self.rect.left, self.rect.top
        else:
            _pr = self.window._get_abspos()
            return _pr[0]+self.rect.left, _pr[1]+self.rect.top

    def __contains__(self, o):
        if type(o) == tuple:
            if len(o) == 2:
                pos = self._get_abspos()
                return pos[0] <= o[0] < pos[0]+self.rect.width and pos[1] <= o[1] < pos[1]+self.rect.height
            else:
                raise ValueError
        else:
            return o in self.objects

    def append(self, obj):
        obj.window = self
        self.objects.append(obj)
        self.refresh()


class Button(BaseObject):
    def __init__(self, main, position: tuple, size: tuple, color=None, window=None, func=lambda: None) -> None:
        super().__init__(main, position, size, color, window)
        self.func = func
        self.pressed = False
        self.cover0 = self.image.copy()
        self.cover1 = self.image.copy()
        self.cover1.blit(im2pg(Im.new('RGBA', self.rect.size, (0, 0, 0, 20))), (0, 0)) # darker
        self.__old_pressed = None

    def handleEvent(self, event: pg.event.Event):
        if super().handleEvent(event):
            return True
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1 and pg.mouse.get_pos() in self:
                self.pressed = True
                self.refresh()
                return True
        elif event.type == pg.MOUSEMOTION:
            if self.pressed and pg.mouse.get_pos() not in self:
                self.pressed = False
                self.refresh()
        elif event.type == pg.MOUSEBUTTONUP:
            if self.pressed:
                self.pressed = False
                self.refresh()
                self.func()

    def refresh(self):
        if self.__old_pressed != self.pressed:
            self.__old_pressed = self.pressed
            if self.pressed:
                self.image = self.cover1.copy()
            else:
                self.image = self.cover0.copy()
            for obj in self.objects:
                obj.show()


def gettextpic(text: str,  textcolor=WHITE, textfont=FONT_TEXT, maxcanavas=SCREEN_SIZE):
    im = Im.new('RGBA', maxcanavas)
    Imd.Draw(im).text((0, 0), text, textcolor, textfont)
    im2 = im.getchannel('A')
    box = [*maxcanavas, 0, 0]
    for _w in range(im2.width):
        for _h in range(im2.height):
            if im2.getpixel((_w, _h)) >= 16:
                box[0] = min(box[0], _w)
                box[1] = min(box[1], _h)
                box[2] = max(box[2], _w)
                box[3] = max(box[3], _h)
    box[2] += 1
    box[3] += 1

    try:
        return im.crop(box)
    except Exception as e:
        Error_Notice(f"{str(type(e))[8:-2]}: {e}").mainloop()
        return Im.new('RGBA', (1, 1))


class PureText(BaseObject):
    LEFT = 'left'
    CENTER = 'center'
    RIGHT = 'right'

    def __init__(self, main, position: tuple, size: tuple, text: str, textcolor=WHITE, textfont=FONT_TEXT, window=None, align=CENTER) -> None:
        super().__init__(main, position, size, TRANSPARENT, window, [])
        self.text = text
        self.textcolor = textcolor
        self.textfont = textfont
        self.align = align

        self.textpic = gettextpic(
            self.text, self.textcolor, self.textfont, self.rect.size)
        if self.align == self.CENTER:
            pos = (round((self.rect.width-self.textpic.size[0])/2),
                   round((self.rect.height-self.textpic.size[1])/2))
        elif self.align == self.LEFT:
            pos = (0, round((self.rect.height-self.textpic.size[1])/2))
        elif self.align == self.RIGHT:
            pos = (round((self.rect.width-self.textpic.size[0])),
                   round((self.rect.height-self.textpic.size[1])/2))
        else:
            raise ValueError(f"align cannot be {self.align}")
        self.picture.paste(self.textpic, pos)
        self.image = im2pg(self.picture)


class _Button_Pressed(GameExit):
    def __init__(self, sth) -> None:
        super().__init__(
            f"a button has been pressed, who wants to return {sth}")
        self.sth = sth

    def __call__(self):
        return self.sth


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
    im = _PureText(source, WHITE, font, (widthlimit+50, 200))()
    if im.width <= widthlimit:
        return source
    i_min = 2
    i_max = len(source)
    while i_max-i_min > 1:
        i = (i_max+i_min)//2
        im = _PureText(source[:i], WHITE, font, (widthlimit+50, 200))()
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


class _Button(BaseObject):
    "一个按钮，阉割版。纯色填充。"

    def __init__(self, window: pg.Surface, pos: tuple, size: tuple, color: _Color,
                 text: _PureText, callfunc=lambda *args: None) -> None:
        self.pos = pos
        self.size = size
        self.rect = pg.Rect(*self.pos, *self.size)
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
        "用于判断按钮是否被按下，并在鼠标抬起的时候激活按钮。\n返回：这个event是否引起了动作"
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = pg.mouse.get_pos()
                if mouse_pos in self:
                    self.pressed = True
                    return True
        elif event.type == pg.MOUSEBUTTONUP:
            if self.pressed:
                self.pressed = False
                self.callfunc()
        elif self.pressed:
            mouse_pos = pg.mouse.get_pos()
            if mouse_pos not in self:
                self.pressed = False

    def show(self, window: pg.Surface = None, pos: tuple = None):
        "显示这个按钮，并刷新自己的位置。\n参数列表：window, pos"
        if self.pressed:
            self.image = self.cover1
        else:
            self.image = self.cover0
        super().show(window, pos)


class Confirm_Notice:
    def __init__(self, text: str, title="请确认", opts=["是", "否"], optdict={0: True, 1: False},
                 width=round(SCREEN_SIZE[0]*0.618), height=round(SCREEN_SIZE[1]*0.4)):
        "call mainloop to return optdict[opts.index(<Your choice>)]"
        self.text = text
        self.title = title
        self.opts = opts
        self.optdict = optdict
        self.objects = []
        self.width = width
        self.height = height
        self.offset = (SCREEN_SIZE[0]//2-width//2, SCREEN_SIZE[1]//2-height)

        self.objects.append(_Button(root, self.offset, (self.width, 100),
                                    (255, 200, 0), _PureText(self.title, (0, 0, 0, 255), FONT_TITLE)))
        self.objects.append(_Button(root, (self.offset[0], self.offset[1]+100), (self.width, self.height-160),
                                    (255, 255, 160), _PureText(text, (0, 0, 0, 255), FONT_TEXT)))

        def _button_return(sth):
            def _func():
                raise _Button_Pressed(sth)
            return _func

        _l = len(self.opts)
        if _l == 1:
            self.objects.append(_Button(root, (self.offset[0]+self.width//4, self.offset[1]+height-55),
                                        (self.width//2, 50), (0, 180,
                                                              0), _PureText(self.opts[0], (255,)*4, FONT_TEXT),
                                        _button_return(self.optdict[0])))
        else:
            _w = (width-20*(_l+1))//_l
            for _i in range(_l):
                self.objects.append(_Button(root, (self.offset[0]+20*(_i+1)+_w*_i, self.offset[1]+height-55),
                                            (_w, 50), (round(180*_i/(_l-1)),
                                                       round(180*(_l-_i-1)/(_l-1)), 0),
                                            _PureText(self.opts[_i], (255,)*4, FONT_TEXT), _button_return(self.optdict[_i])))

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
    def __init__(self, text: str, title="错误",
                 width=round(SCREEN_SIZE[0]*0.9), height=round(SCREEN_SIZE[1]*0.5)):
        "call mainloop to return True"
        self.text = text
        print(text)
        self.title = title
        self.objects = []
        self.width = width
        self.height = height
        self.offset = (SCREEN_SIZE[0]//2-width//2,
                       SCREEN_SIZE[1]//2-height)

        self.objects.append(_Button(root, self.offset, (self.width, 100),
                                    (255, 100, 100), _PureText(self.title, (0, 0, 0, 255), FONT_TITLE)))
        self.objects.append(_Button(root, (self.offset[0], self.offset[1]+100), (self.width, self.height-160),
                                    (255, 200, 200), _PureText(text, (0, 0, 0, 255), FONT_TEXT)))

        def _func():
            raise _Button_Pressed(True)

        self.objects.append(_Button(root, (self.offset[0]+self.width//4, self.offset[1]+height-55),
                                    (self.width//2, 50), (255, 174, 201, 255),
                                    _PureText("彳亍", (255,)*4, FONT_TEXT), _func))

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
    def __init__(self, text: str, title="消息",
                 width=round(SCREEN_SIZE[0]*0.618), height=round(SCREEN_SIZE[1]*0.4)):
        "call mainloop to return True"
        self.text = text
        self.title = title
        self.objects = []
        self.width = width
        self.height = height
        self.offset = (SCREEN_SIZE[0]//2-width//2, SCREEN_SIZE[1]//2-height)

        self.objects.append(_Button(root, self.offset, (self.width, 100),
                                    (80, 80, 255), _PureText(self.title, (255,)*4, FONT_TITLE)))
        self.objects.append(_Button(root, (self.offset[0], self.offset[1]+100), (self.width, self.height-160),
                                    (200, 200, 255), _PureText(text, (0, 0, 0, 255), FONT_TEXT)))

        def _func():
            raise _Button_Pressed(True)

        self.objects.append(_Button(root, (self.offset[0]+self.width//4, self.offset[1]+height-55),
                                    (self.width//2, 50), (255, 200, 255, 255),
                                    _PureText("女子白勺", (0, 0, 0, 255), FONT_TEXT), _func))

    def mainloop(self):
        root.blit(im2pg(Im.new('RGBA', SCREEN_SIZE, (0, 0, 0, 100))), (0, 0))
        clock = pg.time.Clock()
        try:
            while True:
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        pg.quit()
                        raise SystemExit
                    if event.type == pg.KEYDOWN and event.key ==pg.K_RETURN:
                        raise _Button_Pressed(True)
                    for obj in self.objects[::-1]:
                        if obj.handleEvent(event):
                            break
                for obj in self.objects:
                    obj.show()
                pg.display.flip()
                clock.tick(FPS)
        except _Button_Pressed as exc:
            return exc()


class Game(BaseObject):
    def __init__(self, main, cols, rows, mines, *args) -> None:
        super().__init__(main, (0, 0), SCREEN_SIZE)
        self.window = main.window
        self.picture = Im.new('RGBA', (1, 1), TRANSPARENT)
        self.minefield = MinefieldWrapped(cols, rows, mines)
        self.background = BaseObject(main, (0,0), SCREEN_SIZE, BGCOLOR)
        self.objects.append(self.background)
        # 分配到块：
        # 计算它们分别的位置！
        side_block = min(SCREEN_HEIGHT//self.minefield.rows,
                         SCREEN_WIDTH//self.minefield.cols)
        L_leftover = (SCREEN_WIDTH-self.minefield.cols*side_block)//2
        T_leftover = (SCREEN_HEIGHT-self.minefield.rows*side_block)//2

        Block.preload(side_block)
        for col, row in self.minefield:
            self.objects.append(Block(self.main, self,
                                      int(L_leftover+(col-1/2)*side_block), int(
                                          T_leftover+(row-1/2)*side_block), side_block,
                                      col, row))
        self.going = True  # 是否能够继续进行
        self.first_click = True  # 第一次点击
        self.clock = pg.time.Clock()
        self._conducted = False
        pass

    def handleEvent(self, event: pg.event.Event):
        if super().handleEvent(event):
            return True
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                raise GameExit("Quit Game")
        if any(pg.key.get_pressed()[key_code] for key_code in [pg.K_RETURN, pg.K_SPACE]+list(range(48, 58))+list(range(97, 123))):
            if not self._conducted:
                self._conducted = True
                self.minefield.conduct_suggestion()
                self.main._refresh = True

    def tick(self):
        self._conducted = False
        self.minefield.get_suggestion()
        super().tick()
        self.whether()
        if self.going == False:
            raise GameExit("Game Over")

    def refresh(self):
        if MF_DEBUG:
            print("Refresh of game called")
        return super().refresh()

    def whether(self):
        """判断是否胜利或者爆炸"""
        if not self.minefield.safety():
            print(1, round(time() % 100, 3))
            self.lose()
        if self.minefield.is_victory():
            self.victory()

    def lose(self):
        # 提示游戏结束
        # 显示所有雷
        print(2, round(time() % 100, 3))
        self.minefield.digall()
        print(3, round(time() % 100, 3))
        self.refresh()
        print(4, round(time() % 100, 3))
        super().tick()
        print(5, round(time() % 100, 3))
        for _t in range(2*FPS):
            self.show()
            pg.display.flip()
            print(6+_t, round(time() % 100, 3))
            self.main.clock.tick(FPS)
        Info_Notice("你输力（恼").mainloop()
        raise GameExit("lose")

    def victory(self):
        # 提示游戏结束
        print(2, round(time() % 100, 3))
        self.refresh()
        print(3, round(time() % 100, 3))
        super().tick()
        print(4, round(time() % 100, 3))
        for _t in range(FPS):
            self.show()
            pg.display.flip()
            print(6+_t, round(time() % 100, 3))
            self.main.clock.tick(FPS)
        Info_Notice("你赢力（喜").mainloop()
        raise GameExit("win")


# 为了显示扫雷的信息，我们还需要一些别的东西

# 以及最重要的一块
class Block(BaseObject):
    @classmethod
    def preload(cls, side):
        cls.pic = []
        cls.images = []  # 0~8,norm; 9,flagged; 10,quest; 11,blank; 12,gameover

        cls.pic.append(Im.new('RGBA', (50, 50), WHITE))
        for i in range(1, 9):
            _pic = cls.pic[0].copy()
            _cover = _PureText(str(i), NUMBER_COLOR[i], FONT_TEXT, (50, 50))()
            _pic.paste(_cover, ((_pic.width-_cover.width)//2,
                       (_pic.height-_cover.height)//2), _cover.getchannel('A'))
            cls.pic.append(_pic)

        _pic = Im.new('RGBA', (50, 50), FLAG_BGCOLOR)
        _cover = _PureText('🚩', BLACK, FONT_EMOJI, (50, 50))()
        _pic.paste(_cover, ((_pic.width-_cover.width)//2,
                   (_pic.height-_cover.height)//2), _cover.getchannel('A'))
        cls.pic.append(_pic)

        _pic = Im.new('RGBA', (50, 50), TRANSPARENT)
        _cover = _PureText('❓', BLACK, FONT_EMOJI, (50, 50))()
        _pic.paste(_cover, ((_pic.width-_cover.width)//2,
                   (_pic.height-_cover.height)//2), _cover.getchannel('A'))
        cls.pic.append(_pic)

        cls.pic.append(Im.new('RGBA', (50, 50), FLAG_BGCOLOR))

        _pic = Im.new('RGBA', (50, 50), MINE_BGCOLOR)
        _cover = _PureText('💣', BLACK, FONT_EMOJI, (50, 50))()
        _pic.paste(_cover, ((_pic.width-_cover.width)//2,
                   (_pic.height-_cover.height)//2), _cover.getchannel('A'))
        cls.pic.append(_pic)

        for i in range(len(cls.pic)):
            cls.pic[i] = cls.pic[i].resize((side, side))

    @staticmethod
    def get_color(possibility: float):
        if possibility <= 0:
            return COLOR_SAFE
        elif possibility >= 1:
            return COLOR_HAZARD
        else:
            return (
                round(sqrt((1-possibility)*COLOR_SAFE[0]**2 + possibility*COLOR_HAZARD[0]**2)),
                round(sqrt((1-possibility)*COLOR_SAFE[1]**2 + possibility*COLOR_HAZARD[1]**2)),
                round(sqrt((1-possibility)*COLOR_SAFE[2]**2 + possibility*COLOR_HAZARD[2]**2)),
                255
            )

    def __init__(self, main, game: Game, xc, yc, side, xi, yi) -> None:
        super().__init__(main, (xc-side//2, yc-side//2), (side, side))
        self.picture = Block.pic[0]

        self.game = game
        self.just_clicked = 0  # 为了双击设置的
        self.showing = 0

        self.col = xi
        self.row = yi
        self._buffer_showing = -3
        self._buffer_suggestion = None

    def tick(self):
        if self.just_clicked:
            self.just_clicked -= 1/FPS

        # showing
        if self.game.minefield.is_cover(self.col, self.row):
            self.showing = 11
        elif self.game.minefield.is_flag(self.col, self.row):
            self.showing = 9
        elif self.game.minefield.is_suspected(self.col, self.row):
            self.showing = 10
        elif self.game.minefield.is_exposed(self.col, self.row):
            self.showing = self.game.minefield.get_exposed_number(self.col, self.row)
            if self.showing >= 9:
                self.showing = 12
        else:
            raise ValueError("cover value incorrect")
        
        if self._buffer_showing != self.showing or self._buffer_suggestion!=self.game.minefield.suggestion[self.row][self.col]:
            self._buffer_showing = self.showing
            self._buffer_suggestion = self.game.minefield.suggestion[self.row][self.col]
            if self.showing>=9 and self._buffer_suggestion is not None:
                self.picture = Im.new('RGBA', Block.pic[0].size, self.get_color(self._buffer_suggestion))
                if self.picture.height >= 20:
                    Imd.Draw(self.picture).text((0, 0), "%i%%" % round(100*self._buffer_suggestion), BLACK)
                if self.game.minefield.is_suspected(self.col, self.row):
                    self.picture.paste(Block.pic[10], (0, 0), Block.pic[10].getchannel('A'))
                elif self.game.minefield.is_flag(self.col, self.row):
                    self.picture.paste(Block.pic[9], (0, 0), Block.pic[9].getchannel('A'))
            else:
                self.picture = Block.pic[self.showing]
            self.refresh()

    def handleEvent(self, event: pg.event.Event):
        if super().handleEvent(event):
            return True
        elif event.type == pg.MOUSEBUTTONDOWN:
            return self.pressed(event)

    def pressed(self, event):
        mouse_pos = pg.mouse.get_pos()
        button_mouse = event.button

        if mouse_pos in self:
            if MF_DEBUG:
                print(f"Block ({self.col}, {self.row}) pressed by button {button_mouse}")
            # first click
            if self.game.first_click:
                self.game.minefield = MinefieldWrapped(self.game.minefield.cols, self.game.minefield.rows, self.game.minefield.mines, (self.col, self.row))
                self.game.minefield.dig(self.col, self.row)
                self.game.first_click = False
                return True

            # Do the command
            if button_mouse == 1:
                if self.game.minefield.dig(self.col, self.row):
                    return True
            elif button_mouse == 3:
                if self.game.minefield.flag(self.col, self.row):
                    return True

            # double click
            if button_mouse == 1 and self.just_clicked > 0:
                if self.game.minefield.sweep(self.col, self.row):
                    return True
            else:
                self.just_clicked = 0.5


class MainMenu(BaseObject):
    def __init__(self) -> None:
        super().__init__(self, (0, 0), SCREEN_SIZE, BGCOLOR, init())

        self.objects = [
            PureText(self, (100, 0), (600, 80), "爽 雷",
                     textfont=FONT_TITLE, window=self),
            Button(self, (100, 100), (600, 70), _PureText("初级(9x9 m10)",
                   TEXTCOLOR_L, FONT_TEXT, (600, 70))(), self, self.start_game_L),
            Button(self, (100, 180), (600, 70), _PureText("中级(16x16 m40)",
                   TEXTCOLOR_M, FONT_TEXT, (600, 70))(), self, self.start_game_M),
            Button(self, (100, 260), (600, 70), _PureText("高级(30x16 m99)",
                   TEXTCOLOR_H, FONT_TEXT, (600, 70))(), self, self.start_game_H),
            Button(self, (100, 340), (600, 60), _PureText("疯狂(64x36 m999)",
                   (0,0,0,TEXTCOLOR_H[3]), FONT_TEXT, (600, 60))(), self, self.start_game_crazy),
            Button(self, (100, 430), (150, 60), _PureText("退出",
                                                          (177, 34, 76, 255), FONT_TEXT, (150, 60))(), self, quitgame),
            Button(self, (300, 430), (150, 60), _PureText("说明",
                                                          (163, 73, 164, 255), FONT_TEXT, (150, 60))(), self,
                   Info_Notice("点击对应的等级进入游戏棋盘。\n每个位置有雷的概率已经解出并标注。\n你可以像正常游戏那样进行操作，\n也可以按下任意键让电脑帮你操作。\n", "说明").mainloop)]

        self.clock = pg.time.Clock()
        self._refresh = True

    def run_dense_task(self, func, text='计算中...'):
        import threading
        completed = False
        result = None
        def _func():
            nonlocal completed, result
            self._refresh = True
            try:
                result = func()
            except Exception as e:
                Error_Notice(format_exc()).mainloop()
            self._refresh = True
            completed = True
        threading.Thread(target=_func, daemon=True).start()

        loading_im =Im.new('RGBA', (200, 80), (255, 255, 255, 100))
        Imd.Draw(loading_im).text((0, 0), text, (0, 0, 0), FONT_TEXT)
        root.blit(im2pg(loading_im), ((SCREEN_SIZE[0]-200)//2, (SCREEN_SIZE[1]-80)//2))
        pg.display.flip()

        while not completed:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    raise SystemExit
            self.clock.tick(FPS)

        return result

    def start_game(self, cols, rows, mines):
        g = Game(self, cols, rows, mines)
        self._refresh = True
        try:
            while True:
                for event in pg.event.get():
                    if g.handleEvent(event):
                        self._refresh = True
                g.tick()

                if self._refresh:
                    g.refresh()
                    self._refresh = False
                    g.show()
                    pg.display.flip()
                self.clock.tick(FPS)
        except GameExit:
            pass
        except Exception as e:
            Error_Notice(format_exc()).mainloop()

    def start_game_L(self):
        return self.start_game(9, 9, 10)

    def start_game_M(self):
        return self.start_game(16, 16, 40)

    def start_game_H(self):
        return self.start_game(30, 16, 99)
    
    def start_game_crazy(self):
        return self.start_game(64, 36, 999)

    def mainloop(self):
        while True:
            try:
                while True:
                    for event in pg.event.get():
                        if self.handleEvent(event):
                            self._refresh = True
                    self.tick()
                    if self._refresh:
                        self.refresh()
                        self._refresh = False
                    self.show()
                    pg.display.update()
                    self.clock.tick(FPS)
            except GameExit:
                self._refresh = True
            except Exception as e:
                # Error_Notice(f"{str(type(e))[8:-2]}: {e}").mainloop()
                Error_Notice(format_exc()).mainloop()


if __name__ == "__main__":
    m = MainMenu()
    m.mainloop()
