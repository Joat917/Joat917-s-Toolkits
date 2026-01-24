import os, sys
from random import randint, choice
from PIL import Image as Im, ImageDraw as Imd, ImageFont as Imf
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame as pg

refresh_all = True  # 重新渲染全部元素
screen_size = (640, 640)
root = pg.display.set_mode(screen_size, pg.RESIZABLE)
clock = pg.time.Clock()

POINTS_COORD = {(0, 0): (52, 370), (0, 1): (54, 330), (0, 2): (54, 286), (0, 3): (70, 238), (0, 4): (118, 222), (0, 5): (160, 224), (0, 6): (206, 238), (0, 7): (240, 206), (0, 8): (224, 160), (0, 9): (224, 118), (0, 10): (238, 70), (0, 11): (288, 54), (0, 12): (330, 54), (0, 13): (374, 54), (0, 14): (414, 54), (0, 15): (458, 54), (0, 16): (506, 70), (0, 17): (522, 118), (0, 18): (522, 160), (0, 19): (506, 206), (0, 20): (538, 242), (0, 21): (584, 226), (0, 22): (626, 224), (0, 23): (674, 240), (0, 24): (690, 288), (0, 25): (690, 330), (0, 26): (690, 372), (0, 27): (690, 414), (0, 28): (690, 458), (0, 29): (674, 506), (0, 30): (626, 522), (0, 31): (584, 520), (0, 32): (538, 506), (0, 33): (504, 538), (0, 34): (520, 584), (0, 35): (522, 626), (0, 36): (504, 674), (0, 37): (456, 690), (0, 38): (414, 688), (0, 39): (372, 690), (0, 40): (330, 690), (0, 41): (286, 690), (0, 42): (238, 674), (0, 43): (224, 626), (0, 44): (224, 582), (0, 45): (238, 538), (0, 46): (206, 502), (0, 47): (
    160, 520), (0, 48): (118, 520), (0, 49): (72, 504), (0, 50): (54, 456), (0, 51): (56, 414), (1, 0): (136, 60), (1, 4): (58, 60), (1, 8): (136, 130), (1, 12): (58, 130), (1, 1): (684, 136), (1, 5): (684, 58), (1, 9): (614, 136), (1, 13): (614, 60), (1, 2): (610, 682), (1, 6): (686, 682), (1, 10): (610, 614), (1, 14): (686, 614), (1, 3): (62, 608), (1, 7): (62, 684), (1, 11): (130, 608), (1, 15): (130, 684), (2, 0): (120, 372), (2, 4): (164, 372), (2, 8): (206, 372), (2, 12): (250, 372), (2, 16): (292, 372), (2, 20): (336, 372), (2, 1): (374, 120), (2, 5): (374, 164), (2, 9): (374, 206), (2, 13): (374, 250), (2, 17): (374, 294), (2, 21): (374, 338), (2, 2): (624, 374), (2, 6): (582, 374), (2, 10): (538, 374), (2, 14): (496, 374), (2, 18): (452, 374), (2, 22): (408, 374), (2, 3): (372, 624), (2, 7): (372, 580), (2, 11): (372, 536), (2, 15): (372, 492), (2, 19): (372, 450), (2, 23): (372, 406), (3, 0): (36, 202), (3, 1): (542, 36), (3, 2): (708, 540), (3, 3): (204, 704)}
R = 18

AIRWAY = 0
APRON = 1
FINAL = 2
RUNWAY = 3
STRING_METHODS = ['Airway', 'Apron', 'Final', 'Runway']

RED = 0
YELLOW = 1
BLUE = 2
GREEN = 3
STRING_COLORS = ['Red', 'Yellow', 'Blue', 'Green']
FPS = 20

IMG_ROOT = os.path.abspath('../../assets/flightchess/')
FLIGHT_PICS = [Im.open(os.path.join(IMG_ROOT, f"icon_{clr}.png")) for clr in ['red', 'yellow', 'blue', 'green']]

ANIMATION_DURATION1 = 0.2
ANIMATION_DURATION2 = 0.5

# 刷新方式 仅限屏幕一小块地方还是全部地方
FULLSCREEN = pg.FULLSCREEN
REGIONAL = pg.RESIZABLE
STAY_IDLE = 0
refresh_mode = [FULLSCREEN, []]

# 是否机器操作
MANUAL = 0  # 人工操作
AUTO = 1
ALWAYS_FIRST = 2  # 总是选择最前面那一个
ALWAYS_LAST = 4  # 总是选择最后面那一个
ALWAYS_FIGHT = 8  # 总是选择先击落敌方。没有飞机可以击落的情况下优先起飞，否则总是选择最后那个
ALWAYS_RANDOM = 16  # 随机选择
AUTO_ALWAYS_FIRST = 3
AUTO_ALWAYS_LAST = 5
AUTO_ALWAYS_FIGHT = 9
AUTO_ALWAYS_RANDOM = 17
operation_mode = [AUTO_ALWAYS_FIGHT, AUTO_ALWAYS_FIRST, AUTO_ALWAYS_LAST, AUTO_ALWAYS_RANDOM]

# 选择时候的半黑屏
DARK_COVERS = [Im.new('RGBA', (780, 780), (100, 0, 0, 100)),
               Im.new('RGBA', (780, 780), (50, 50, 0, 100)),
               Im.new('RGBA', (780, 780), (0, 0, 100, 100)),
               Im.new('RGBA', (780, 780), (0, 100, 0, 100))]

# 已经赢力
victory = [0, 0, 0, 0]


def im2pg(im: Im.Image):
    return pg.image.frombuffer(im.tobytes(), im.size, im.mode)


class Scaling:
    def __init__(self, prop=0.82):
        self.prop = prop

    def refresh(self, new_prop=None):
        global refresh_all, refresh_mode
        if new_prop is not None and new_prop != self.prop:
            refresh_all = True
            refresh_mode = [FULLSCREEN, []]
            self.prop = new_prop

    def __call__(self, thing):
        if type(thing) in [int, float]:
            return type(thing)(thing*self.prop)
        elif type(thing) in [tuple, list]:
            return type(thing)([type(i)(i*self.prop) for i in thing])
        else:
            return thing.resize(self(thing.size))


class Dice:
    def __init__(self) -> None:
        self.round = 0
        self.current = 0
        self._last_result = None
        self.planechoice = None
        self.refresh()

    def __call__(self):
        self.round += 1
        self.planechoice = None
        if all(victory):
            print(victory)
            raise RuntimeError('GameOver')
        if self._last_result != 6:
            self.current = (self.current-1) & 3
            while victory[self.current]:
                self.current = (self.current-1) & 3
        self._last_result = randint(1, 6)
        self.refresh()
        return self._last_result

    def refresh(self):
        im = Im.new('RGBA', (30, 60))
        Imd.Draw(im).text((0, 0), str((self._last_result if self._last_result is not None else '-')),
                          STRING_COLORS[self.current], Imf.truetype('arial.ttf', 32))
        self.picture = Picture(im, scaling, (470, 300))
        self.picture.refresh(im)
        if refresh_mode[0] != FULLSCREEN:
            refresh_mode[0] = REGIONAL
            refresh_mode[1].append((*self.picture.pos, self.picture.pos[0]+self.picture.scaling(im.width),
                                    self.picture.pos[1]+self.picture.scaling(im.height)))

    def show(self):
        self.picture.show()


class Place:
    places = {}

    @staticmethod
    def init():
        for (typex, data) in POINTS_COORD.keys():
            Place(typex, data)

    def __init__(self, typex: int, data: int) -> None:
        self.typex = typex
        self.data = data
        self.color = data & 3
        self.position0 = POINTS_COORD[(self.typex, self.data)]
        self.pos = None
        self.places[(self.typex, self.data)] = self
        pass

    def refresh(self, scaling: Scaling):
        self.pos = scaling(self.pos)


class Picture:
    def __init__(self, pic0: Im.Image, scaling: Scaling, position0: tuple) -> None:
        self.pic0 = pic0
        self.scaling = scaling
        self.position0 = position0
        self.refresh()

    def change_pos0(self, new_pos0: tuple):
        old_pos = self.scaling(self.position0)
        self.position0 = new_pos0
        new_pos = self.scaling(new_pos0)
        self.pos = self.scaling(self.position0)
        global refresh_mode
        if refresh_mode[0] != FULLSCREEN:
            refresh_mode[0] = REGIONAL
            refresh_mode[1].append(
                (min(old_pos[0], new_pos[0]), min(old_pos[1], new_pos[1]),
                 self.scaling(self.pic0.width)+max(old_pos[0], new_pos[0]),
                 self.scaling(self.pic0.height)+max(old_pos[1], new_pos[1])))

    def refresh(self, new_pic0=None):
        if new_pic0 is not None:
            self.pic0 = new_pic0
        self.pic = self.scaling(self.pic0)
        self.image = im2pg(self.pic)
        self.pos = self.scaling(self.position0)

    def show(self):
        root.blit(self.image, self.pos)

    def get_rect(self):
        return pg.Rect(*self.pos, *self.pic.size)


class Flight:
    flights = []

    @classmethod
    def init(cls, scaling: Scaling):
        for data in range(16):
            cls.flights.append(Flight(data, scaling))

    @classmethod
    def get_flights(cls, place: tuple):
        return [f for f in cls.flights if (f.place.typex, f.place.data) == place]

    def __init__(self, data: int, scaling: Scaling):
        self.color = data % 4
        self.index = data//4
        self.apron = Place.places[(APRON, data)]
        self.place = self.apron
        self.skipped = False  # 是否已经跳过。每轮刷新。
        self.arrival = False  # 是否已经抵达终点。
        self.animations = []  # [[tick,(duration, p0, p1)], ...]
        self.picture = Picture(
            FLIGHT_PICS[self.color], scaling, self.place.position0)
        pass

    @staticmethod
    def _get_place(color: int, current_place: tuple, addition: int):
        "返回位置(,,)，途径[(,,)]（包括起点终点）"
        if addition < 0:
            raise ValueError
        if addition == 0:
            return current_place, [current_place]
        color &= 3
        if current_place[0] == APRON and current_place[1] & 3 == color:
            return (RUNWAY, color), [current_place, (RUNWAY, color)]
        elif current_place[0] == RUNWAY and current_place[1] == color:
            return (AIRWAY, addition+2+13*color), [current_place]+[(AIRWAY, i+2+13*color) for i in range(1, addition+1)]
        elif current_place[0] == AIRWAY:
            data = current_place[1]
            if data == 13*color:
                last = Flight._get_place(color, (FINAL, color), addition-1)
            else:
                last = Flight._get_place(
                    color, (AIRWAY, (data+1) % 52), addition-1)
            return last[0], [current_place]+last[1]
        elif current_place[0] == FINAL and current_place[1] & 3 == color:
            step = current_place[1] >> 2
            step += addition
            return (FINAL, ((5-abs(((current_place[1] >> 2)+addition)-5)) << 2)+color), \
                [(FINAL, ((5-abs(((current_place[1] >> 2)+i)-5)) << 2)+color)
                 for i in range(addition+1)]
        else:
            raise ValueError

    @staticmethod
    def mix(p1, p2, β):
        "返回p1*(1-β)+p2*β"
        return p1[0]*(1-β)+p2[0]*β, p1[1]*(1-β)+p2[1]*β

    def _move2(self, place: tuple, duration=ANIMATION_DURATION1):
        "一次性地飞到place的地方。"
        self.animations.append(
            [0, (duration, self.place.position0, Place.places[place].position0)])
        self.place = Place.places[place]

    def tick(self):
        if self.animations:
            tick, info = self.animations[0]
            if tick >= info[0]:
                self.animations.pop(0)
                self.picture.change_pos0(info[2])
            else:
                self.picture.change_pos0(
                    self.mix(info[1], info[2], tick/info[0]))
                self.animations[0][0] += 1/FPS
            # print(refresh_mode)
        if self.place.typex == FINAL and self.place.data >> 2 == 5:
            self.arrival = True
            self._move2((self.apron.typex, self.apron.data),
                        ANIMATION_DURATION2)

    def refresh(self):
        self.picture.refresh()

    def show(self):
        self.picture.show()

    def evaluate(self, point: int):
        "把点数告诉自己，看看自己能不能做点什么"
        if self.arrival:
            return False
        if self.place.typex == APRON:
            return point in [5, 6]
        return True

    def get_progress(self):
        "返回一个数字，表征自己自从出发已经走过了多少格子。"
        if self.arrival:
            return 200
        if self.place.typex == APRON:
            return 0
        elif self.place.typex == RUNWAY:
            return 1
        elif self.place.typex == AIRWAY:
            return 2+(self.place.data-2-13*self.color) % 52
        elif self.place.typex == FINAL:
            return 60+(self.place.data >> 2)
        else:
            raise RuntimeError('can\'t know where the flight is')

    def fightback(self):
        "被击落力"
        self._move2((self.apron.typex, self.apron.data), ANIMATION_DURATION2)

    def _check_fightback(self, dest: tuple):
        "检查并击落其它飞机"
        # print(f"check:{dest[1]}")
        other_flights = self.get_flights(dest)
        while self in other_flights:
            other_flights.remove(self)
        if other_flights and other_flights[0].color != self.color:
            # print(f"checked:{dest[1]}, flight_clr:{other_flights[0].color}")
            if len(other_flights) == 1:
                other_flights[0].fightback()
            else:
                for f in other_flights:
                    f.fightback()
                    self.fightback()

    def move(self, point: int):
        if not self.evaluate(point):
            raise RuntimeError(
                'attempt to move something that cannot be moved')
        dest, waypoints = self._get_place(
            self.color, (self.place.typex, self.place.data), point)
        for w in waypoints[1:]:
            self._move2(w)
        self._check_fightback(dest)
        if not self.skipped and self.place.typex == AIRWAY and self.place.color == self.color:
            if self.place.data % 13 == 0:
                pass
            elif self.place.data % 13 == 7:
                self._check_fightback((AIRWAY, (self.place.data+12) % 52))
                self._move2((AIRWAY, (self.place.data+12) %
                            52), ANIMATION_DURATION2)
                if not self.skipped:
                    self.skipped = True
                    self._check_fightback((AIRWAY, (self.place.data+4) % 52))
                    self._move2((AIRWAY, (self.place.data+4) % 52))
            else:
                self.skipped = True
                self._check_fightback((AIRWAY, (self.place.data+4) % 52))
                self._move2((AIRWAY, (self.place.data+4) % 52))
                if self.place.data % 13 == 7:
                    self._check_fightback((AIRWAY, (self.place.data+12) % 52))
                    self._move2((AIRWAY, (self.place.data+12) %
                                52), ANIMATION_DURATION2)

    def clicksin(self, pos: tuple):
        "传入鼠标坐标，返回是否点到"
        r = self.picture.scaling(18)
        ref = self.picture.pos
        # print(pos, ref, ((pos[0]-ref[0])**2 + (pos[1]-ref[1])**2)**0.5, r)
        return (pos[0]-ref[0]-r)**2 + (pos[1]-ref[1]-r)**2 <= r**2

    def _will_fight(self, point: int):
        "返回这次行动是否能够击落飞机"
        if not self.evaluate(point):
            raise RuntimeError(
                'attempt to move something that cannot be moved')
        dest, waypoints = self._get_place(
            self.color, (self.place.typex, self.place.data), point)
        checks = [dest]
        if not self.skipped and self.place.typex == AIRWAY and self.place.color == self.color:
            skipped = False
            if self.place.data % 13 == 0:
                pass
            elif self.place.data % 13 == 7:
                checks.append((AIRWAY, (self.place.data+12) % 52))
                if not skipped:
                    skipped = True
                    checks.append((AIRWAY, (self.place.data+4) % 52))
            else:
                skipped = True
                checks.append((AIRWAY, (self.place.data+4) % 52))
                if self.place.data % 13 == 7:
                    checks.append((AIRWAY, (self.place.data+12) % 52))
        for _d in checks:
            _l = self.get_flights(_d)
            if _l and _l[0].color != self.color:
                return True
        return False


def requiry_plane(choices: list, color=None):
    if len(choices) == 0:
        raise ValueError
    elif len(choices) == 1:
        return choices[0]
    if color is None:
        color = choices[0].color
    if operation_mode[color] & AUTO:
        if operation_mode[color] & ALWAYS_FIRST:
            return choices[0]
        elif operation_mode[color] & ALWAYS_LAST:
            _chosen = choices[0]
            _min_record = _chosen.get_progress()
            for _c in choices[1:]:
                _r = _c.get_progress()
                if _r < _min_record:
                    _min_record = _r
                    _chosen = _c
            return _chosen
        elif operation_mode[color] & ALWAYS_FIGHT:
            for _c in choices:
                if _c._will_fight(dice._last_result):
                    return _c
            for _c in choices:
                if _c.place.typex == FINAL and (_c.place.data >> 2)+dice._last_result == 5:
                    return _c
            for _c in choices:
                if _c.place.typex == AIRWAY and _c.place.data % 13 == 0 and _c.place.data & 3 == color:
                    return _c
            for _c in choices:
                if _c.place.typex == AIRWAY and (_c.place.data+dice._last_result) & 3 == color:
                    return _c
            for _c in choices:
                if _c.place.typex == APRON:
                    return _c
            
            _chosen = None
            _min_record = 1000
            for _c in choices:
                if _c.place.typex==AIRWAY:
                    _r = _c.get_progress()
                    if _r < _min_record:
                        _min_record = _r
                        _chosen = _c
            if _chosen is not None:
                return _chosen

            for _c in choices:
                if _c.place.typex == FINAL and (_c.place.data >> 2) <= 2:
                    return _c
            for _c in choices:
                if _c.place.typex==RUNWAY:
                    return _c
            return choices[0]
        elif operation_mode[color] & ALWAYS_RANDOM:
            return choice(choices)
        else:
            raise RuntimeError('Unspecified auto')
    else:
        global refresh_all, refresh_mode
        refresh_all = True
        refresh_mode = [FULLSCREEN, []]
        cov = Picture(DARK_COVERS[color], scaling, (0, 0))
        cov.show()
        dice.refresh()
        for f in choices:
            f.show()
        dice.show()
        pg.display.flip()
        while True:
            clock.tick(FPS)

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    print(victory)
                    pg.quit()
                    exit()
                elif event.type == pg.WINDOWRESIZED:
                    new_screensize = root.get_size()
                    screen_size = min(new_screensize), min(new_screensize)
                    if new_screensize != screen_size:
                        pg.display.set_mode(screen_size, pg.RESIZABLE)
                        scaling.refresh(screen_size[0]/780)
                        background.refresh()
                        cov.refresh()
                        for f in Flight.flights:
                            f.refresh()
                        background.show()
                        for f in Flight.flights:
                            f.show()
                        cov.show()
                        for f in choices:
                            f.show()
                        dice.show()
                        ...
                        pg.display.flip()
                        refresh_mode[1].clear()
                elif event.type == pg.MOUSEBUTTONDOWN:
                    mouse_pos = pg.mouse.get_pos()
                    for f in choices:
                        if f.clicksin(mouse_pos):
                            return f


def manipulate(dice: Dice):
    for f in Flight.flights:
        if f.animations:
            return
    point = dice()
    choices = []
    for i in range(4):
        if Flight.flights[(i << 2)+dice.current].evaluate(point):
            choices.append(Flight.flights[(i << 2)+dice.current])

    # print(point, dice.current)
    if choices:
        chosen_plane = requiry_plane(choices)
        chosen_plane.move(point)

    for f in Flight.flights:
        f.skipped = False
    # 判断是否有人赢了
    for color in range(4):
        if not victory[color]:
            if all([Flight.flights[(i << 2)+color].arrival for i in range(4)]):
                victory[color] = [bool(_i) for _i in victory].count(True)+1


scaling = Scaling()
background = Picture(Im.open(os.path.join(IMG_ROOT, 'board.png')), scaling, (0, 0))
dice = Dice()
Place.init()
Flight.init(scaling)

autoround = False
cooldown = 0


def mainloop():
    global refresh_all, refresh_mode, autoround, cooldown
    while True:
        clock.tick(FPS)
        if refresh_all:
            scaling.refresh()
            background.refresh()
            for f in Flight.flights:
                f.refresh()
            dice.refresh()
            ...
            refresh_all = False
            pass

        if refresh_mode[0] == FULLSCREEN:
            background.show()
            for f in Flight.flights:
                f.show()
            dice.show()
            ...
            pg.display.flip()
            refresh_mode[1].clear()
            refresh_mode[0] = STAY_IDLE
        elif refresh_mode[0] == REGIONAL:
            background.show()
            for f in Flight.flights:
                f.show()
            dice.show()
            ...
            for r in refresh_mode[1]:
                pg.display.update(
                    pg.Rect(r[0]-1, r[1]-1,  r[2]-r[0]+2, r[3]-r[1]+2))
            refresh_mode[1].clear()
            refresh_mode[0] = STAY_IDLE

        for event in pg.event.get():
            if event.type == pg.QUIT:
                print(victory)
                pg.quit()
                exit()
            elif event.type == pg.WINDOWRESIZED:
                new_screensize = root.get_size()
                screen_size = min(new_screensize), min(new_screensize)
                if new_screensize != screen_size:
                    pg.display.set_mode(screen_size, pg.RESIZABLE)
                    scaling.refresh(screen_size[0]/780)
            elif event.type == pg.KEYDOWN or event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                cooldown = 1
                manipulate(dice)
                autoround = True
        for f in Flight.flights:
            f.tick()
        if cooldown <= 0:
            cooldown = 0
        else:
            cooldown -= 1/FPS
        if autoround and not cooldown:
            if operation_mode[(dice.current-1) & 3] & 1 != 0 or dice._last_result == 6 or victory[(dice.current-1) & 3]:
                for f in Flight.flights:
                    if f.animations:
                        break
                else:
                    manipulate(dice)
                    cooldown = 1
            else:
                autoround = False
                im = Im.new('RGBA', (30, 60))
                Imd.Draw(im).text((0, 0), '?',
                                  STRING_COLORS[(dice.current-1) & 3], Imf.truetype('arial.ttf', 32))
                dice.picture = Picture(im, scaling, (470, 300))
                if refresh_mode[0] != FULLSCREEN:
                    refresh_mode[0] = REGIONAL
                    refresh_mode[1].append((*dice.picture.pos, dice.picture.pos[0]+dice.picture.scaling(im.width),
                                            dice.picture.pos[1]+dice.picture.scaling(im.height)))

if __name__ == '__main__':
    mainloop()
