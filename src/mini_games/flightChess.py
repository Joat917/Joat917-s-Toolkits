import os, sys
from PIL import Image as Im, ImageDraw as Imd, ImageFont as Imf
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame as pg
from flightchesslib import Game, AnimatedPlane, PlayerBase, PlayerA1, Locations, Colors

refresh_all = True  # 重新渲染全部元素
screen_size = (640, 640)
root = pg.display.set_mode(screen_size, pg.RESIZABLE)
pg.display.set_caption('Flight Chess')
clock = pg.time.Clock()

FPS = 30

IMG_ROOT = os.path.abspath('../../assets/flightchess/')
FLIGHT_PICS = [Im.open(os.path.join(IMG_ROOT, f"icon_{clr}.png")) for clr in ['red', 'yellow', 'blue', 'green']]
FINAL_PICS = [im.copy().convert('LA').convert('RGBA') for im in FLIGHT_PICS]
pg.display.set_icon(pg.image.load(os.path.join(IMG_ROOT, 'icon_red.png')))

ANIMATION_DURATION = 0.3  # 飞机移动动画持续时间（秒）
STEP_GAP = 0.5

# 刷新方式 仅限屏幕一小块地方还是全部地方
FULLSCREEN = pg.FULLSCREEN
REGIONAL = pg.RESIZABLE
STAY_IDLE = 0
refresh_mode = [FULLSCREEN, []]

# 是否机器操作
MANUAL = 0  # 人工操作
AUTO = 1

operation_mode = [MANUAL, AUTO, AUTO, AUTO]

# 选择时候的半黑屏
DARK_COVERS = [Im.new('RGBA', (780, 780), (0, 0, 0, 180)),
               Im.new('RGBA', (780, 780), (0, 0, 0, 180)),
               Im.new('RGBA', (780, 780), (0, 0, 0, 180)),
               Im.new('RGBA', (780, 780), (0, 0, 0, 180))]


def im2pg(im: Im.Image):
    return pg.image.frombuffer(im.tobytes(), im.size, im.mode)


class Scaling:
    def __init__(self, prop=640/780):
        self.prop = prop

    def refresh(self, new_prop=None):
        global refresh_all, refresh_mode
        refresh_all = True
        refresh_mode = [FULLSCREEN, []]
        if new_prop is not None:
            self.prop = new_prop

    def __call__(self, thing):
        if type(thing) in [int, float]:
            return type(thing)(thing*self.prop)
        elif type(thing) in [tuple, list]:
            return type(thing)([type(i)(i*self.prop) for i in thing])
        else:
            return thing.resize(self(thing.size))


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


class Flight(AnimatedPlane):
    def __init__(self, color, idx, game):
        super().__init__(color, idx, game, ANIMATION_DURATION, FPS, 780)
        self.picture = Picture(FLIGHT_PICS[self.color.value], scaling, self.scale(self.location))

    def refresh(self):
        self.picture.refresh()
    
    def tick(self):
        new_position = super().tick()
        self.picture.change_pos0(new_position)
        self.refresh()
        return 

    def show(self):
        if self.arrival and not self.animations:
            self.picture=Picture(FINAL_PICS[self.color.value], scaling, self.picture.position0)
        self.picture.show()

    def clicksin(self, mouse_pos):
        return self.picture.get_rect().collidepoint(mouse_pos)

class HumanPlayer(PlayerBase):
    def choose_plane(self, movable_planes, dice_value):
        global refresh_all, refresh_mode
        refresh_all = True
        refresh_mode = [FULLSCREEN, []]
        cov = Picture(DARK_COVERS[self.color.value], scaling, (0, 0))
        cov.show()
        game.refresh()
        for f in movable_planes:
            f.show()
        game.show()
        pg.display.flip()
        while True:
            clock.tick(FPS)

            for event in pg.event.get():
                if event.type == pg.QUIT:
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
                        for f in self.game.planes:
                            f.refresh()
                        background.show()
                        for f in self.game.planes:
                            f.show()
                        cov.show()
                        for f in movable_planes:
                            f.show()
                        game.show()
                        pg.display.flip()
                        refresh_mode[1].clear()
                elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pg.mouse.get_pos()
                    for f in movable_planes:
                        if f.clicksin(mouse_pos):
                            return f

class GameDisplay(Game):
    def __init__(self, seed=None):
        players = {color:PlayerA1(color, self) if operation_mode[color.value] & AUTO else HumanPlayer(color, self) for color in Colors}
        super().__init__(players, seed, Flight, 4)

    def refresh(self):
        im = Im.new('RGBA', (30, 60))
        Imd.Draw(im).text((0, 0), 
            str((self.dice.current_value if self.dice.current_value is not None else '-')), 
            self.dice.current_player.name.lower() if self.dice.current_player is not None else 'gray', 
            Imf.truetype('arial.ttf', 32))
        self.picture = Picture(im, scaling, (470, 300))
        self.picture.refresh(im)
        if refresh_mode[0] != FULLSCREEN:
            refresh_mode[0] = REGIONAL
            refresh_mode[1].append((*self.picture.pos, self.picture.pos[0]+self.picture.scaling(im.width), self.picture.pos[1]+self.picture.scaling(im.height)))

    def show(self):
        self.picture.show()



scaling = Scaling()
background = Picture(Im.open(os.path.join(IMG_ROOT, 'board.png')), scaling, (0, 0))
game = GameDisplay()

autoround = False
cooldown = 0

def mainloop():
    global refresh_all, refresh_mode, autoround, cooldown
    while True:
        # 等待下一帧
        clock.tick(FPS)

        # 重新渲染需要更新的元素
        if refresh_all:
            scaling.refresh()
            background.refresh()
            for f in game.planes:
                f.refresh()
            game.refresh()
            # refresh_all = False
            pass

        if refresh_mode[0] == FULLSCREEN:
            background.show()
            for f in game.planes:
                f.show()
            game.show()
            pg.display.flip()
            refresh_mode[1].clear()
            refresh_mode[0] = STAY_IDLE
        elif refresh_mode[0] == REGIONAL:
            background.show()
            for f in game.planes:
                f.show()
            game.show()
            for r in refresh_mode[1]:
                pg.display.update(pg.Rect(r[0]-1, r[1]-1,  r[2]-r[0]+2, r[3]-r[1]+2))
            refresh_mode[1].clear()
            refresh_mode[0] = STAY_IDLE

        # 处理事件
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()
            elif event.type == pg.WINDOWRESIZED:
                new_screensize = root.get_size()
                screen_size = min(new_screensize), min(new_screensize)
                if new_screensize != screen_size:
                    pg.display.set_mode(screen_size, pg.RESIZABLE)
                    scaling.refresh(screen_size[0]/780)

        # 更新游戏状态
        for f in game.planes:
            f.tick()
        if cooldown <= 0:
            cooldown = 0
            game.step()
            cooldown = STEP_GAP
        else:
            cooldown -= 1/FPS

        # 自动进行下一步
        for f in game.planes:
            if f.animations:
                cooldown = STEP_GAP
                break

if __name__ == '__main__':
    mainloop()
