"""
周报生成器。根据给定文字生成满足要求的背景和相应的文字板块。
"""

from PIL import Image as Im, ImageDraw as Imd, ImageFont as Imfn, ImageFilter as Imfl, ImageColor as Imclr
from math import cos, pi, sqrt, exp
import numpy as np

WIDTH_CANVAS = 1000  # 整张图片的宽度
CONTENT_PADDING = 30  # 内容之间的间隔
GRAD_OFFSET = 200  # 不同部分之间的渐变宽度


class BackGroundBase:
    def __init__(self, height: int) -> None:
        self.canvas = Im.new('RGBA', (WIDTH_CANVAS, height))
        self.offset = height  # 决定下一张图贴的位置
        self.layer = 0  # 图层高度，越低越接近底部

    def __add__(self, other):
        if not isinstance(other, BackGroundBase):
            raise TypeError
        new_height = max(self.offset+other.canvas.height, self.canvas.height)
        new_background = BackGroundBase(new_height)
        new_background.offset = self.offset+other.offset
        new_background.layer = other.layer
        new_canvas = new_background.canvas
        if self.layer <= other.layer:
            new_canvas.paste(self.canvas, (0, 0), self.canvas.getchannel('A'))
            new_canvas.paste(other.canvas, (0, self.offset),
                             other.canvas.getchannel('A'))
        else:
            new_canvas.paste(other.canvas, (0, self.offset),
                             other.canvas.getchannel('A'))
            new_canvas.paste(self.canvas, (0, 0), self.canvas.getchannel('A'))
        return new_background


class Sun(BackGroundBase):
    def __init__(self, content_height: int) -> None:
        self.content_height = content_height
        self.addition_height = GRAD_OFFSET
        super().__init__(self.content_height+self.addition_height)
        self.layer = 8
        self.offset = max(round(
            sqrt((self.content_height+WIDTH_CANVAS*2)**2-WIDTH_CANVAS**2/4)-WIDTH_CANVAS*2), 0)
        radius_center = (WIDTH_CANVAS//2, -WIDTH_CANVAS*2)
        draw = Imd.Draw(self.canvas)
        for i in range(64):
            radius = content_height+self.addition_height * \
                (1-i/64)-radius_center[1]
            draw.ellipse((radius_center[0]-radius, radius_center[1]-radius,
                          radius_center[0]+radius, radius_center[1]+radius),
                         fill=(255, 192+i, 48+3*i, round(255*self.smooth(i/63))))
        self.canvas = self.canvas.filter(Imfl.BLUR())

    @staticmethod
    def smooth(x):
        "从(0,0)到(1,1)的光滑曲线，两端斜率为0"
        if x <= 0:
            return 0
        elif x >= 1:
            return 1
        else:
            return (1-cos(pi*x))/2

    @staticmethod
    def mixColor(beta: float, a: tuple, b: tuple):
        "混合颜色a和b, 0=>a, 1=>b"
        return tuple(round(sqrt(beta*j**2+(1-beta)*i**2)) for i, j in zip(a, b))


class Universe(BackGroundBase):
    def __init__(self, height: int) -> None:
        super().__init__(height)
        self.scatter(0.1)
        new_canvas = Im.new('RGBA', self.canvas.size,
                            (np.random.randint(2, 16), 2,
                             np.random.randint(2, 16), 255))
        new_canvas.paste(self.canvas, mask=self.canvas.getchannel('A'))
        self.canvas = new_canvas
        self.offset -= GRAD_OFFSET
        self.layer = 1

    def scatter(self, density: float):
        star_count = np.random.poisson(density*self.canvas.height)
        draw = Imd.Draw(self.canvas)
        for _ in range(star_count):
            radius_center = (np.random.randint(0, WIDTH_CANVAS),
                             np.random.randint(0, self.canvas.height))
            radius_topmost = np.random.poisson(5)+1
            radius_bottommost = np.random.randint(radius_topmost)
            if np.random.random() > 0.5:
                d = np.random.randint(128, 255)
                color = (255, d, d)
            else:
                d = np.random.randint(128, 255)
                color = (d, d, 255)
            for radius in range(radius_topmost, radius_bottommost, -1):
                draw.ellipse((radius_center[0]-radius, radius_center[1]-radius,
                              radius_center[0]+radius, radius_center[1]+radius),
                             fill=(*color, round(255*Sun.smooth((radius_topmost-radius)/(radius_topmost-radius_bottommost)))))


class Sky(BackGroundBase):
    def __init__(self, height: int, dusk=False, school=True, fence=True) -> None:
        super().__init__(height)
        self.layer = 2
        if dusk:
            self.color1 = (255, 120, 30)
            self.color2 = (255, 160, 30)
        else:
            self.color1 = (0, 120, 255)
            self.color2 = (0, 255, 255)

        def _func_smooth(x):
            "返回一个数，从0渐渐逼近1"
            if abs(x) < 1/6:
                return 0.
            return exp(-1/x/x)

        self.mix = Sun.mixColor
        draw = Imd.Draw(self.canvas)
        for h in range(self.canvas.height):
            alpha = round(Sun.smooth(h/GRAD_OFFSET)*255)
            draw.rectangle((0, h, WIDTH_CANVAS, h),
                           self.mix(_func_smooth(h/height*2),
                                    self.color1+(alpha,), self.color2+(alpha,)))
        if school:
            self.school(main_building=False)
        if fence:
            self.fence()
        return

    def school(self, main_building=True, building_width_mean=200,
               building_count=16, building_height_mean=300):
        # (width, height, center_x, color)
        params = np.zeros((4, building_count), np.int32)

        params[0, :] = np.random.poisson(building_width_mean, building_count)
        params[1, :] = np.random.poisson(building_height_mean, building_count)
        params[2, :] = np.random.randint(0, WIDTH_CANVAS, building_count)
        params[3, :] = np.random.randint(0x22, 0x66, building_count)

        draw = Imd.Draw(self.canvas)

        for i in range(building_count):
            draw.rectangle(
                (params[2, i]-params[0, i]//2, self.canvas.height-params[1, i],
                 params[2, i]+params[0, i]//2, self.canvas.height), (params[3, i],)*3)

        if main_building:
            raise NotImplementedError
        return
    
    def fence(self):
        raise NotImplementedError


class Road(BackGroundBase):
    WIDTH_TRACK = 60
    WIDTH_LINE = 10
    LENGTH_LINE = 100
    COLOR_TRACK = '#444444'
    COLOR_LINE_1 = '#dddddd'
    COLOR_LINE_2 = '#cccc22'

    def __init__(self, trackCount=(2, 2), lineStyle='--',
                 sepLineStyle='=', pavement_width=WIDTH_TRACK, grass=False):
        components = []
        _randint_lenline = np.random.randint(0, self.LENGTH_LINE)

        # pavement
        _im_pav = Im.new(
            'RGBA', (WIDTH_CANVAS, pavement_width), self.COLOR_TRACK)
        _im_solid = Im.new(
            'RGBA', (WIDTH_CANVAS, self.WIDTH_LINE), self.COLOR_LINE_1)
        components.append(_im_pav)
        if trackCount[0]:
            components.append(_im_solid)

        # get ready for tracks and lines
        _im_track = Im.new(
            'RGBA', (WIDTH_CANVAS, self.WIDTH_TRACK), self.COLOR_TRACK)

        if lineStyle == '-':
            _im_line = _im_solid
        elif lineStyle == '--':
            _im_temp = Im.new(
                'RGBA', (self.LENGTH_LINE, self.WIDTH_LINE), self.COLOR_LINE_1)
            _im_line = Im.new(
                'RGBA', (WIDTH_CANVAS, self.WIDTH_LINE), self.COLOR_TRACK)
            for _w in range(-_randint_lenline, WIDTH_CANVAS, 2*self.LENGTH_LINE):
                _im_line.paste(_im_temp, (_w, 0))
        elif lineStyle == '=':
            _im_line = Im.new(
                'RGBA', (WIDTH_CANVAS, self.WIDTH_LINE*3), self.COLOR_TRACK)
            _im_line.paste(_im_solid, (0, 0))
            _im_line.paste(_im_solid, (0, self.WIDTH_LINE*2))
        else:
            raise ValueError('lineStyle cannot be recognized')

        # road #1
        for i in range(trackCount[0]):
            if i:
                components.append(_im_line)
            components.append(_im_track)

        # seperator
        if sepLineStyle == '-':
            _im_sep = Im.new(
                'RGBA', (WIDTH_CANVAS, self.WIDTH_LINE), self.COLOR_LINE_2)
        elif sepLineStyle == '--':
            _im_temp = Im.new(
                'RGBA', (self.LENGTH_LINE, self.WIDTH_LINE), self.COLOR_LINE_2)
            _im_sep = Im.new(
                'RGBA', (WIDTH_CANVAS, self.WIDTH_LINE), self.COLOR_TRACK)
            for _w in range(-_randint_lenline, WIDTH_CANVAS, 2*self.LENGTH_LINE):
                _im_sep.paste(_im_temp, (_w, 0))
        elif sepLineStyle == '=':
            _im_temp = Im.new(
                'RGBA', (WIDTH_CANVAS, self.WIDTH_LINE), self.COLOR_LINE_2)
            _im_sep = Im.new(
                'RGBA', (WIDTH_CANVAS, self.WIDTH_LINE*3), self.COLOR_TRACK)
            _im_sep.paste(_im_temp, (0, 0))
            _im_sep.paste(_im_temp, (0, self.WIDTH_LINE*2))
        elif sepLineStyle == '==':
            _im_temp = Im.new(
                'RGBA', (self.LENGTH_LINE, self.WIDTH_LINE), self.COLOR_LINE_2)
            _im_sep = Im.new(
                'RGBA', (WIDTH_CANVAS, self.WIDTH_LINE*3), self.COLOR_TRACK)
            for _w in range(-_randint_lenline, WIDTH_CANVAS, 2*self.LENGTH_LINE):
                _im_sep.paste(_im_temp, (_w, 0))
                _im_sep.paste(_im_temp, (_w, self.WIDTH_LINE*2))
        else:
            raise ValueError('sepLineStyle cannot be recognized')
        components.append(_im_sep)

        # road #2
        for i in range(trackCount[0]):
            if i:
                components.append(_im_line)
            components.append(_im_track)

        # pavement
        if trackCount[1]:
            components.append(_im_solid)
        components.append(_im_pav)

        super().__init__(height=sum(map(lambda im: im.height, components)))
        _h = 0
        for _c in components:
            self.canvas.paste(_c, (0, _h))
            _h += _c.height

        if grass:
            raise NotImplementedError
        return


class Earth(BackGroundBase):
    COLOR1 = Imclr.getrgb('#8e403a')
    COLOR2 = Imclr.getrgb('#3a0603')

    def __init__(self, height: int, fillGap=3):
        super().__init__(height)
        draw = Imd.Draw(self.canvas)

        for _h in range(0, height+fillGap-1, fillGap):
            draw.rectangle(
                (0, _h, WIDTH_CANVAS, _h+fillGap),
                Sun.mixColor(_h/height, self.COLOR1, self.COLOR2))

        return


class BackGround:
    ...


class Texts:
    def __init__(self, text: str, textColor='white', textFontPath='simkai.ttf', textSize=21):
        ...
    ...


class SegmentBase:
    def __init__(self, height: int, darkmode=False):
        ...


class MainTitle(SegmentBase):
    ...


class DateDisplay(SegmentBase):
    ...


class AchvDisplay(SegmentBase):
    ...


class PiePlot(SegmentBase):
    ...


if __name__ == "__main__":
    (Sun(400)+Universe(1800)+Sky(1200)+Road()+Earth(800)).canvas.save('test.png')
