"""
这个文件新增了HUB，包含：\
按钮Button、文本Text、火把Torch、扳手Wrench、地雷LandMine、障碍Barrier\
物品栏ItemBar、血条HPBar、摇杆Rocker（还没做）、提示文本Prompt。
"""

from BaseImport import *
from Sword import Sword
from Rocker import Rocker
from HelpPage import helppage as _helppage


def helppage(window: pg.Surface, background: pg.Surface):
    try:
        _helppage(window, background)
    except:
        window.blit(MEDIA.im2pg(
            Im.new('RGBA', SCREEN_SIZE, (0, 0, 0, 127))), (0, 0))
        return


class Media:
    def __init__(self) -> None:
        # self.background = Im.open("2222.jpg")\
        #     .convert('RGBA').resize(SCREEN_SIZE)
        # self.backgroundcover = Media.im2pg(self.background)
        self.font = Imf.truetype('arial.ttf', FONTSIZE)
        self.button_pause = [Im.open(MediaPath/"Button_Pause.png").convert('RGBA'),
                             Im.open(MediaPath/"Button_Pause_Pressed.png").convert('RGBA')]
        self.button_quit = [Im.open(MediaPath/"Button_Quit.png").convert('RGBA'),
                            Im.open(MediaPath/"Button_Quit_Pressed.png").convert('RGBA')]
        self.button_leave = [Im.open(MediaPath/"Button_Leave.png").convert('RGBA'),
                             Im.open(MediaPath/"Button_Leave_Pressed.png").convert('RGBA')]
        self.button_helppage = [Im.open(MediaPath/"Button_HelpPage.png").convert('RGBA'),
                                Im.open(MediaPath/"Button_HelpPage_Pressed.png").convert('RGBA')]
        self.torch = Im.open(MediaPath/"Torch.png").convert('RGBA')
        self.wrench = Im.open(MediaPath/"Wrench.png").convert('RGBA')
        self.itembar = [Im.open(MediaPath/"ItemBar_type0.png").convert('RGBA').
                        resize(ITEMBAR_SIZE[1]),
                        Im.open(MediaPath/"ItemBar_type1.png").convert('RGBA').
                        resize(ITEMBAR_SIZE[1]),
                        Im.open(MediaPath/"ItemBar_type2.png").convert('RGBA').
                        resize(ITEMBAR_SIZE[1])]
        self.itembar_base = Im.open(MediaPath/"ItemBar.png").\
            resize(ITEMBAR_SIZE[0])
        self.itembar_mask = self.itembar[0].getchannel('A').\
            resize(ITEMBAR_SIZE[1])

        self.hpbar = [Im.open(MediaPath/"HPBar_type1.png").convert('RGBA'),
                      Im.open(MediaPath/"HPBar_type2.png").convert('RGBA')]
        self.hpbar_heart = Im.open(MediaPath/"HPBar_heart.png").convert('RGBA')
        self.hpbar_armor = Im.open(MediaPath/"HPBar_armor.png").convert('RGBA')
        self.landmine = Im.open(MediaPath/"LandMine.png").convert('RGBA')
        self.barrier = Im.open(MediaPath/"Barrier.png").convert('RGBA')

    @staticmethod
    def im2pg(im: Im.Image, format='RGBA'):
        return pg.image.frombuffer(im.tobytes(), im.size, format)


MEDIA = Media()


class Button:
    def __init__(self, position: tuple, size: tuple, func, image: list, * func_args, **func_kwargs) -> None:
        self.position = position  # TL corner
        self.size = size
        self.func = lambda: func(*func_args, **func_kwargs)

        self.img = [im.resize(size) for im in image]
        self.cover = Media.im2pg(self.img[0]), Media.im2pg(self.img[1])

        self.mousedown = False
        self.mousepos = None
        pass

    def dealevent(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.mousepos = pg.mouse.get_pos()
                if self.position[0] < self.mousepos[0] < self.position[0]+self.size[0]\
                        and self.position[1] < self.mousepos[1] < self.position[1]+self.size[1]:
                    self.mousedown = True
        if event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                if self.mousedown:
                    self.func()
                self.mousedown = False

    def show(self, window: pg.Surface):
        if self.mousedown:
            window.blit(self.cover[1], self.position)
            self.mousepos = pg.mouse.get_pos()
            if not (self.position[0] < self.mousepos[0] < self.position[0]+self.size[0]
                    and self.position[1] < self.mousepos[1] < self.position[1]+self.size[1]):
                self.mousedown = False
        else:
            window.blit(self.cover[0], self.position)


class Text:
    def __init__(self, text: str, place: tuple, color=(255, 255, 255, 255)) -> None:
        self.text = text
        self.lines_count = self.text.count('\n')+1
        self.place = place
        self.image = Im.new('RGBA', (SCREEN_SIZE[0], 50*self.lines_count))
        Imd.Draw(self.image).text((0, 0), self.text, color, MEDIA.font)
        self.cover = Media.im2pg(self.image)
        pass

    def show(self, window: pg.Surface):
        window.blit(self.cover, self.place)


class Torch:
    def __init__(self, main, maze) -> None:
        self.main = main
        self.maze = maze
        self.torches = {}
        for point in self.maze:
            if self.maze.visit(*point) == 3:
                self.place(*point, prompt=False)

    def place(self, x: int, y: int, z: int, /, prompt=True):
        "Place a torch in the grid; if succeed, return True"
        if (x, y, z) in self.torches and self.torches[(x, y, z)]:
            return False
        self.torches[(x, y, z)] = 1
        self.maze.setpoint(x, y, z, 3)
        self.main.zooming = True
        if prompt:
            Prompt("Torch Placed!")
        return True

    def remove(self, x: int, y: int, z: int):
        "Remove a torch from the grid; if succeed, return True"
        if (x, y, z) not in self.torches or not self.torches[(x, y, z)]:
            return False
        self.torches.pop((x, y, z))
        self.maze.setpoint(x, y, z, 1)
        self.main.zooming = True
        Prompt("Torch Removed!")
        return True

    def get_torch_pos(self):
        return [self.main.mc.map2screen(*p3) for p3 in self.torches.keys()]

    @classmethod
    def geticon(cls):
        try:
            return cls.icon
        except:
            _t = MEDIA.torch.resize((16, 42))
            cls.icon = Im.new('RGBA', ITEMBAR_SIZE[1])
            cls.icon.paste(_t, (20, 10), _t.getchannel('A'))
            return cls.icon

    @classmethod
    def use(cls, main):
        _p = main.role.position
        _t = main.maze.visit(*_p)
        if _t == 1:
            main.torch.place(*main.role.position)
        elif _t == 3:
            main.torch.remove(*main.role.position)


class LandMine:
    def __init__(self, main, maze) -> None:
        self.main = main
        self.maze = maze
        self.landmines = {}
        for point in self.maze:
            if self.maze.visit(*point) == 5:
                self.place(*point, prompt=False)

    def place(self, x: int, y: int, z: int, /, prompt=True):
        "Place a landmine in the grid; if succeed, return True"
        if (x, y, z) in self.landmines and self.landmines[(x, y, z)]:
            return False
        self.landmines[(x, y, z)] = 1
        self.maze.setpoint(x, y, z, 5)
        self.main.zooming = True
        if prompt:
            Prompt("Landmine Placed!")
        return True

    def remove(self, x: int, y: int, z: int, prompt=True):
        "Remove a landmine from the grid; if succeed, return True"
        if (x, y, z) not in self.landmines or not self.landmines[(x, y, z)]:
            return False
        self.landmines.pop((x, y, z))
        self.maze.setpoint(x, y, z, 1)
        self.main.zooming = True
        if prompt:
            Prompt("Landmine Removed!")
        return True

    def get_landmine_pos(self):
        return [self.main.mc.map2screen(*p3) for p3 in self.landmines.keys()]

    @classmethod
    def geticon(cls):
        try:
            return cls.icon
        except:
            _t = MEDIA.landmine.resize((38, 38))
            cls.icon = Im.new('RGBA', ITEMBAR_SIZE[1])
            cls.icon.paste(_t, (10, 12), _t.getchannel('A'))
            return cls.icon

    @classmethod
    def use(cls, main):
        if main.maze.visit(*main.role.position) == 1:
            main.landmine.place(*main.role.position)
            # main.hub.itembar.selected = 1
            main.hub.itembar.refresh()


class Barrier:
    def __init__(self, main, maze) -> None:
        self.main = main
        self.maze = maze
        self.barriers = {}
        for point in self.maze:
            if self.maze.visit(*point) == 4:
                self.place(*point, prompt=False)

    def place(self, x: int, y: int, z: int, /, prompt=True):
        "Place a barrier in the grid; if succeed, return True"
        if (x, y, z) in self.barriers and self.barriers[(x, y, z)]:
            return False
        self.barriers[(x, y, z)] = 1
        self.maze.setpoint(x, y, z, 4)
        self.main.zooming = True
        if prompt:
            Prompt("barrier Placed!")
        return True

    def remove(self, x: int, y: int, z: int, prompt=True):
        "Remove a barrier from the grid; if succeed, return True"
        if (x, y, z) not in self.barriers or not self.barriers[(x, y, z)]:
            return False
        self.barriers.pop((x, y, z))
        self.maze.setpoint(x, y, z, 1)
        self.main.zooming = True
        if prompt:
            Prompt("barrier Removed!")
        return True

    def get_barrier_pos(self):
        return [self.main.mc.map2screen(*p3) for p3 in self.barriers.keys()]

    @classmethod
    def geticon(cls):
        try:
            return cls.icon
        except:
            _t = MEDIA.barrier.resize((38, 38))
            cls.icon = Im.new('RGBA', ITEMBAR_SIZE[1])
            cls.icon.paste(_t, (10, 12), _t.getchannel('A'))
            return cls.icon

    @classmethod
    def use(cls, main):
        _p = main.role.position
        _t = main.maze.visit(*_p)
        if _t == 1:
            main.barrier.place(*main.role.position)
        elif _t == 4:
            main.barrier.remove(*main.role.position)


class Prompt:
    prompts = []

    def __init__(self, text: str, duration=3, color=(0, 255, 255, 255)) -> None:
        Prompt.prompts.append(self)
        if '\n' in text:
            self.text = text[:text.index('\n')]
            Prompt(text[text.index('\n')+1:])
        else:
            self.text = text
        self.color = color
        self.tick_left = duration*FPS
        self.image = Im.new('RGBA', (SCREEN_SIZE[0], 30), color=(0, 0, 0, 0))
        Imd.Draw(self.image).text((0, 0), self.text, self.color, MEDIA.font)
        self.cover = Media.im2pg(self.image)

    def _show(self, window: pg.Surface, y):
        if self.tick_left <= 0:
            self.prompts.remove(self)
            del self
            return False
        self.tick_left -= 1
        window.blit(self.cover, (5, y))
        return True

    @classmethod
    def show(cls, window: pg.Surface):
        i = 0
        while i < len(cls.prompts):
            if cls.prompts[i]._show(window, 150+24*i):
                i += 1


class Wrench:
    waittime_fixArmor = 0
    fixingArmor = False
    armor_enduring = 0

    waittime_defuseMine = 0
    defusalTarget = None

    waittime_breakBarrier = 0
    breakingTarget = None

    def __init__(self, item: type) -> None:
        pass

    @classmethod
    def geticon(cls):
        try:
            return cls.icon
        except:
            _t = MEDIA.wrench.resize((38, 38))
            cls.icon = Im.new('RGBA', ITEMBAR_SIZE[1])
            cls.icon.paste(_t, (10, 12), _t.getchannel('A'))
            return cls.icon

    @classmethod
    def use(cls, main):
        pos = main.role.position
        floortype = main.maze.visit(*pos)
# defuse landmine
        if cls.waittime_defuseMine > 0:
            main.landmine.remove(*cls.defusalTarget, prompt=False)
            Prompt("Mine defused!")
            cls.waittime_defuseMine = 0
            return
        elif floortype == 5:
            Prompt("Press again to defuse the mine...")
            cls.defusalTarget = pos
            cls.waittime_defuseMine = 3*FPS
            return

        for pot in main.maze.neighbors(*pos):
            if main.maze.visit(*pot) == 5:
                Prompt("Press again to defuse the mine...")
                cls.defusalTarget = pot
                cls.waittime_defuseMine = 3*FPS
                return
# break barrier
        if cls.waittime_breakBarrier > 0:
            main.barrier.remove(*cls.breakingTarget, prompt=False)
            Prompt("Barrier clear!")
            main.zooming = True
            cls.waittime_breakBarrier = 0
            return
        elif floortype == 4:
            Prompt("Press again to break the barrier...")
            cls.breakingTarget = pos
            cls.waittime_breakBarrier = 3*FPS
            return

        for pot in main.maze.neighbors(*pos):
            if main.maze.visit(*pot) == 4:
                if cls.waittime_breakBarrier <= 0:
                    Prompt("Press again to break the barrier...")
                    cls.breakingTarget = pot
                    cls.waittime_breakBarrier = 3*FPS
                    return

        if cls.fixingArmor:
            cls.fixingArmor = False
            main.role.armor = cls.armor_enduring
            cls.waittime_fixArmor = 0
        else:
            if cls.waittime_fixArmor <= 0:
                Prompt("Press again to fix the Armor...")
                cls.waittime_fixArmor = 3*FPS
            elif main.role.armor < 100:
                cls.fixingArmor = True
                cls.armor_enduring = main.role.armor
                main.role.armor = 0
                Prompt("Fixing Armor: %i%%" % cls.armor_enduring, 8/FPS)
            else:
                Prompt("You don't need to fix the armor.")
                cls.waittime_fixArmor = 0

    @classmethod
    def show(cls, main):
        if (cls.fixingArmor and cls.armor_enduring) >= 100:
            cls.fixingArmor = False
            cls.waittime_fixArmor = 0
            main.role.armor = 100
            Prompt("Armor Fixed!")
            return
        if (cls.fixingArmor and main.hub.itembar.selected != 1):
            cls.fixingArmor = False
            cls.waittime_fixArmor = 0
            main.role.armor = cls.armor_enduring
            Prompt("Armor Fixing interrupted!")
            return
        if cls.waittime_fixArmor >= 0:
            cls.waittime_fixArmor -= 1
        elif cls.fixingArmor:
            cls.armor_enduring += 1
            cls.waittime_fixArmor = FPS//4
            Prompt("Fixing Armor: %i%%" % cls.armor_enduring, 8/FPS)
        if cls.waittime_breakBarrier > 0:
            cls.waittime_breakBarrier -= 1
        if cls.waittime_defuseMine > 0:
            cls.waittime_defuseMine -= 1


class ItemBar:
    def __init__(self, hub, position) -> None:
        self.hub = hub
        self.position = position
        self.items = [Wrench, Torch, LandMine, Barrier, Sword]
        self.selected = 1

        self.image = MEDIA.itembar_base
        for i in range(1, 10):
            if i == self.selected:
                self.image.paste(MEDIA.itembar[2],
                                 (79*i-65, 12), MEDIA.itembar_mask)
                _img = self.items[i-1].geticon()
                self.image.paste(_img, (79*i-65, 12), _img.getchannel('A'))
            elif i > len(self.items):
                self.image.paste(MEDIA.itembar[1],
                                 (79*i-65, 12), MEDIA.itembar_mask)
            else:
                self.image.paste(MEDIA.itembar[0],
                                 (79*i-65, 12), MEDIA.itembar_mask)
                _img = self.items[i-1].geticon()
                self.image.paste(_img, (79*i-65, 12), _img.getchannel('A'))
        self.cover = MEDIA.im2pg(self.image)
        self.changing = True

        self.buttons = []
        __im = Im.new('RGBA', (1, 1))
        for j in range(len(self.items)):
            def __c(i):
                if self.selected == i:
                    self.items[self.selected-1].use(self.hub.main)
                    return
                self.selected = i
                self.changing = True

            self.buttons.append(Button(
                (79*j+14+self.position[0], 12+self.position[1]),
                ITEMBAR_SIZE[1], __c, [__im, __im], j+1))
        if True:
            self.buttons.append(Button(
                (79*9+14+self.position[0], 12+self.position[1]),
                ITEMBAR_SIZE[1], self.hub.main.save, [__im, __im]))

    def refresh(self):
        self.image = MEDIA.itembar_base
        for i in range(1, 10):
            if i == self.selected:
                self.image.paste(MEDIA.itembar[2],
                                 (79*i-65, 12), MEDIA.itembar_mask)
                _img = self.items[i-1].geticon()
                self.image.paste(_img, (79*i-65, 12), _img.getchannel('A'))
            elif i > len(self.items):
                self.image.paste(MEDIA.itembar[1],
                                 (79*i-65, 12), MEDIA.itembar_mask)
            else:
                self.image.paste(MEDIA.itembar[0],
                                 (79*i-65, 12), MEDIA.itembar_mask)
                _img = self.items[i-1].geticon()
                self.image.paste(_img, (79*i-65, 12), _img.getchannel('A'))
        self.cover = MEDIA.im2pg(self.image)

    def dealevent(self, event):
        if event.type == pg.KEYDOWN:
            if 48 <= event.key < 58:
                if event.key == 48:
                    self.hub.main.save()
                else:
                    if event.key-48 <= len(self.items):
                        if self.selected == event.key-48:
                            self.items[self.selected-1].use(self.hub.main)
                        else:
                            self.selected = event.key-48
                            self.changing = True
            elif event.key in [pg.K_SPACE]:
                # self.items[self.selected-1].use(self.hub.main)
                self.items[self.selected-1].use(self.hub.main)

        elif event.type == pg.MOUSEBUTTONDOWN:
            ...
        for b in self.buttons:
            b.dealevent(event)

    def show(self, window: pg.Surface):
        if self.changing:
            self.refresh()
            self.changing = False
        for b in self.buttons:
            b.show(window)
        window.blit(self.cover, self.position)


class HPBar:
    def __init__(self, hub, position, be_armor=False) -> None:
        self.hub = hub
        self.position = position
        self.imageposition = self.position[0]+HPBAR_SIZE[0][0]//2, \
            self.position[1]+(HPBAR_SIZE[0][1]-HPBAR_SIZE[1][1])//2
        self.percentage = 100

        if be_armor:
            self.icon = MEDIA.hpbar_armor.resize(HPBAR_SIZE[0])
            self.image = MEDIA.hpbar[1].resize(HPBAR_SIZE[1])
        else:
            self.icon = MEDIA.hpbar_heart.resize(HPBAR_SIZE[0])
            self.image = MEDIA.hpbar[0].resize(HPBAR_SIZE[1])
        self.iconcover = MEDIA.im2pg(self.icon)
        self.imagecover = MEDIA.im2pg(self.image)

        self.text = Text(f"{self.percentage}%",
                         (self.imageposition[0]+HPBAR_SIZE[1][0], self.imageposition[1]))

    def change_percentage(self, percentage: int):
        if percentage == self.percentage:
            return
        elif percentage <= 0:
            self.percentage = 0
            self.image = self.image = self.image.resize((3, HPBAR_SIZE[1][1]))
            self.imagecover = MEDIA.im2pg(self.image)
            self.text.__init__("0%", self.imageposition)
            return
        self.percentage = percentage
        self.image = self.image.resize(
            (round(HPBAR_SIZE[1][0]*(self.percentage+10)/110), HPBAR_SIZE[1][1]))
        self.imagecover = MEDIA.im2pg(self.image)
        self.text.__init__(f"{self.percentage}%",
                           (self.imageposition[0]+round(HPBAR_SIZE[1][0]*(self.percentage+10)/110),
                            self.imageposition[1]))

    def show(self, window: pg.Surface):
        window.blit(self.imagecover, self.imageposition)
        window.blit(self.iconcover, self.position)
        self.text.show(window)
        pass


class SpaceButton(Button):
    def __init__(self, position: tuple, size: tuple, func, image: list, *func_args, **func_kwargs) -> None:
        image = []
        image.append(Im.new('RGBA', (2*ROCKER_RADIUS+2, 2*ROCKER_RADIUS+2)))

        super().__init__(position, size, func, image, *func_args, **func_kwargs)
        self.spacebuttondown = False

    def dealevent(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.mousepos = pg.mouse.get_pos()
                if self.position[0] < self.mousepos[0] < self.position[0]+self.size[0]\
                        and self.position[1] < self.mousepos[1] < self.position[1]+self.size[1]:
                    self.mousedown = True
        elif event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                if self.mousedown:
                    self.func()
                self.mousedown = False
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE:
                self.spacebuttondown = True
        elif event.type == pg.KEYUP:
            if event.button == pg.K_SPACE:
                self.spacebuttondown = False


class HUB:
    def __init__(self, main) -> None:
        self.main = main
        self.button_pause_main = Button((SCREEN_SIZE[0]-60, 10), (50, 50),
                                        self.pause, MEDIA.button_pause)
        self.button_pause_loop = Button((SCREEN_SIZE[0]//2-120, SCREEN_SIZE[1]//2-120),
                                        (100, 100), self._resume, MEDIA.button_pause)
        self.button_quit = Button((SCREEN_SIZE[0]//2-120, SCREEN_SIZE[1]//2+20),
                                  (100, 100), self._quit, MEDIA.button_quit)
        self.button_leave = Button((SCREEN_SIZE[0]//2+20, SCREEN_SIZE[1]//2-120),
                                   (100, 100), self._leave, MEDIA.button_leave)
        self.button_helppage = Button((SCREEN_SIZE[0]//2+20, SCREEN_SIZE[1]//2+20),
                                      (100, 100), helppage, MEDIA.button_helppage, self.main.window, self.main.media.backgroundcover)

        self.hpbar = HPBar(self, (20, 20))
        self.shbar = HPBar(self, (20, 70), True)
        self.itembar = ItemBar(
            self, (SCREEN_SIZE[0]-ITEMBAR_SIZE[0][0]-10, SCREEN_SIZE[1]-ITEMBAR_SIZE[0][1]-10))

        self.rocker = Rocker(self.main, 100+ROCKER_RADIUS,
                             SCREEN_SIZE[1]-ROCKER_HANDLE_RADIUS-150)

    def _resume(self):
        self.pause_loop = False

    def _quit(self):
        raise GameExit

    def _leave(self):
        pg.quit()
        exit(0)

    def pause(self):
        self.pause_loop = True
        tick = 0
        self.main.window.blit(MEDIA.im2pg(
            Im.new('RGBA', SCREEN_SIZE, (0, 0, 0, 127))), (0, 0))
        while self.pause_loop:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self._quit()
                self.button_pause_loop.dealevent(event)
                self.button_helppage.dealevent(event)
                self.button_quit.dealevent(event)
                self.button_leave.dealevent(event)

            self.button_pause_loop.show(self.main.window)
            self.button_helppage.show(self.main.window)
            self.button_quit.show(self.main.window)
            self.button_leave.show(self.main.window)
            tick += 1

            pg.display.update()
            self.main.clock.tick(FPS)

    def dealevent(self, event):
        self.button_pause_main.dealevent(event)
        self.itembar.dealevent(event)
        self.rocker.dealevent(event)

    def show(self):
        self.hpbar.show(self.main.window)
        self.shbar.show(self.main.window)
        self.itembar.show(self.main.window)
        self.button_pause_main.show(self.main.window)
        self.rocker.show()


"""
class Role:
    def __init__(self, main) -> None:
        self.main = main
        self.position = self.main.start
        self.keydown = {pg.K_w: 0, pg.K_e: 0, pg.K_d: 0,
                        pg.K_x: 0, pg.K_z: 0, pg.K_a: 0, pg.K_s: 0,
                        pg.K_i: 0, pg.K_o: 0, pg.K_l: 0,
                        pg.K_COMMA: 0, pg.K_m: 0, pg.K_j: 0, pg.K_k: 0}
        self.cooltime = {pg.K_w: 0, pg.K_e: 0, pg.K_d: 0,
                         pg.K_x: 0, pg.K_z: 0, pg.K_a: 0, pg.K_s: 0,
                         pg.K_i: 0, pg.K_o: 0, pg.K_l: 0,
                         pg.K_COMMA: 0, pg.K_m: 0, pg.K_j: 0, pg.K_k: 0}
        self.direction = {pg.K_w: BL, pg.K_e: BR, pg.K_d: R,
                          pg.K_x: TR, pg.K_z: TL, pg.K_a: L, pg.K_s: 0,
                          pg.K_i: BL, pg.K_o: BR, pg.K_l: R,
                          pg.K_COMMA: TR, pg.K_m: TL, pg.K_j: L, pg.K_k: 0}
        self.rolecover = None

    def dealevent(self, event):
        if event.type == pg.KEYDOWN:
            if event.key in self.keydown:
                self.keydown[event.key] = 1
                self.cooltime[event.key] = 0
        elif event.type == pg.KEYUP:
            if event.key in self.keydown:
                self.keydown[event.key] = 0
                self.cooltime[event.key] = 0

    def show(self):
        for d in self.keydown:
            if self.keydown[d]:
                if self.cooltime[d] > 0:
                    self.cooltime[d] -= 1/FPS
                else:
                    self.cooltime[d] = 0.12
"""
