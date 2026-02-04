"""
加入了exit，游戏获得合适的玩法
修复了原地重生的bug
加入了胜利动画和烟花
使得Main类能够和上级兼容
新增主动生成迷宫的选项，并允许给定种子
防止exit被覆盖
加入帮助模块
增加保存提示：是否覆盖
"""


from BaseImport import *
import Maze
import shader as Shader
import Hub
import Enemies
import Fireshow
import ErrorNotice


class Media:
    def __init__(self) -> None:
        self.background = BACKGROUND
        self.backgroundcover = Media.im2pg(self.background)
        self.role = Im.new('RGBA', (16, 16))
        Imd.Draw(self.role).ellipse(
            (0, 0, 15, 15), fill=(0, 216, 0, 255))

    @staticmethod
    def im2pg(im: Im.Image, format='RGBA'):
        return pg.image.frombuffer(im.tobytes(), im.size, format)

    @staticmethod
    def get_shader(width: int, height: int, zoom: int, role_pos: tuple, torches_pos=[]):
        "pos: related to screen; return pg.Surface"
        out = Shader.get_shader(width, height, [(role_pos, zoom*ROLE_HORIZON)] +
                                [(pos, zoom*TORCH_RANGE) for pos in torches_pos])
        return Media.im2pg(out)

    def get_rolecover(self, zoom: int):
        return Media.im2pg(self.role.resize((zoom, zoom)))


class MotionControl:
    def __init__(self, main) -> None:
        self.main = main
        self.mousedown = False
        self.fixpoint = None
        # zoom in n out
        self.zoomrequest = {'-': 0, '+': 0}
        self.zoomwait = {'-': 0, '+': 0}
        self.tempzoom = self.main.zoom  # 临时存储的zoom值
        # move the maze itself
        self.keyspeed = {'up': 0, 'down': 0, 'left': 0, 'right': 0}
        self.direction = {'up': (0, -1), 'down': (0, 1),
                          'left': (-1, 0), 'right': (1, 0)}
        pass

    def dealevent(self, event: pg.event.Event):
        if event.type == pg.MOUSEBUTTONDOWN:
            mouse_pos = pg.mouse.get_pos()
            if event.button in [3]:
                self.mousedown = True
                self.fixpoint = self.screen2map(*mouse_pos)
            elif event.button == 4:
                fixpoint = self.screen2map(*mouse_pos)
                if self.tempzoom < ZOOMMAX:
                    self.tempzoom *= 1.1
                if round(self.tempzoom) != self.main.zoom:
                    self.main.zoom = round(self.tempzoom)
                    self.main.refreshMaze()
                    self.main.zooming = True
                    targetpoint = self.map2screen(*fixpoint)
                    self.main.offset = (self.main.offset[0]+mouse_pos[0]-targetpoint[0],
                                        self.main.offset[1]+mouse_pos[1]-targetpoint[1])
            elif event.button == 5:
                if self.tempzoom > 1:
                    fixpoint = self.screen2map(*mouse_pos)
                    self.tempzoom /= 1.1
                    if round(self.tempzoom) != self.main.zoom:
                        self.main.zoom = round(self.tempzoom)
                        self.main.refreshMaze()
                        self.main.zooming = True
                        targetpoint = self.map2screen(*fixpoint)
                        self.main.offset = (self.main.offset[0]+mouse_pos[0]-targetpoint[0],
                                            self.main.offset[1]+mouse_pos[1]-targetpoint[1])
        elif event.type == pg.MOUSEBUTTONUP:
            if event.button in [3]:
                self.mousedown = False
                self.fixpoint = None
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_UP:
                self.keyspeed['up'] = 1
            elif event.key == pg.K_DOWN:
                self.keyspeed['down'] = 1
            elif event.key == pg.K_LEFT:
                self.keyspeed['left'] = 1
            elif event.key == pg.K_RIGHT:
                self.keyspeed['right'] = 1
            elif event.key == pg.K_MINUS:
                self.zoomrequest['-'] = 1
            elif event.key == pg.K_EQUALS:
                self.zoomrequest['+'] = 1
        elif event.type == pg.KEYUP:
            if event.key == pg.K_UP:
                self.keyspeed['up'] = 0
            elif event.key == pg.K_DOWN:
                self.keyspeed['down'] = 0
            elif event.key == pg.K_LEFT:
                self.keyspeed['left'] = 0
            elif event.key == pg.K_RIGHT:
                self.keyspeed['right'] = 0
            elif event.key == pg.K_MINUS:
                self.zoomrequest['-'] = 0
                self.zoomwait['-'] = 0
            elif event.key == pg.K_EQUALS:
                self.zoomrequest['+'] = 0
                self.zoomwait['-'] = 0

    def show(self):
        if self.mousedown:
            mouse_pos = pg.mouse.get_pos()
            targetpoint = self.map2screen(*self.fixpoint)
            self.main.offset = (self.main.offset[0]+mouse_pos[0]-targetpoint[0],
                                self.main.offset[1]+mouse_pos[1]-targetpoint[1])
            self.main.moving = True

        for d in self.keyspeed:
            if self.keyspeed[d]:
                self.main.offset = (
                    self.main.offset[0]-self.direction[d][0]*self.keyspeed[d],
                    self.main.offset[1]-self.direction[d][1]*self.keyspeed[d])
                self.keyspeed[d] += 1
                self.main.moving = True

        if self.zoomwait['-'] > 0:
            self.zoomwait['-'] -= 1/FPS
        if self.zoomwait['+'] > 0:
            self.zoomwait['+'] -= 1/FPS

        if self.zoomrequest['-'] and not self.zoomrequest['+'] and self.zoomwait['-'] <= 0:
            self.zoomwait['-'] = 0.1
            rolepos = self.map2screen(*self.main.role.position)
            fixpoint = self.main.role.position
            if self.tempzoom > 1:
                self.tempzoom /= 1.1
                if round(self.tempzoom) != self.main.zoom:
                    self.main.zoom = round(self.tempzoom)
                    self.main.refreshMaze()
                    self.main.zooming = True
                    targetpoint = self.map2screen(*fixpoint)
                    self.main.offset = (self.main.offset[0]+rolepos[0]-targetpoint[0],
                                        self.main.offset[1]+rolepos[1]-targetpoint[1])

        elif self.zoomrequest['+'] and not self.zoomrequest['-'] and self.zoomwait['+'] <= 0:
            self.zoomwait['+'] = 0.1
            rolepos = self.map2screen(*self.main.role.position)
            fixpoint = self.main.role.position
            if self.tempzoom < ZOOMMAX:
                self.tempzoom *= 1.1
            if round(self.tempzoom) != self.main.zoom:
                self.main.zoom = round(self.tempzoom)
                self.main.refreshMaze()
                self.main.zooming = True
                targetpoint = self.map2screen(*fixpoint)
                self.main.offset = (self.main.offset[0]+rolepos[0]-targetpoint[0],
                                    self.main.offset[1]+rolepos[1]-targetpoint[1])

    def map2screen(self, x: int, y: int, z: int, offsetx=0.0, offsety=0.0):
        x0, y0 = self.main.maze.map2xy(
            x, y, z, self.main.zoom, offsetx, offsety)
        return x0+self.main.offset[0], y0+self.main.offset[1]

    def screen2map(self, x: int, y: int):
        x0, y0 = round((x-self.main.offset[0])),\
            round((y-self.main.offset[1]))
        return self.main.maze.xy2map(x0, y0, self.main.zoom)


class Role:
    direction = {pg.K_w: BL, pg.K_e: BR, pg.K_d: R,
                 pg.K_x: TR, pg.K_z: TL, pg.K_a: L, pg.K_s: 0,
                 pg.K_i: BL, pg.K_o: BR, pg.K_l: R,
                 pg.K_COMMA: TR, pg.K_m: TL, pg.K_j: L, pg.K_k: 0}

    def __init__(self, main) -> None:
        self.main = main
        self.position = self.main.start
        self.keydown = {pg.K_w: 0, pg.K_e: 0, pg.K_d: 0,
                        pg.K_x: 0, pg.K_z: 0, pg.K_a: 0, pg.K_s: 0,
                        pg.K_i: 0, pg.K_o: 0, pg.K_l: 0,
                        pg.K_COMMA: 0, pg.K_m: 0, pg.K_j: 0, pg.K_k: 0}
        self.cooltime = 0  # 移动的冷却时间
        self.rolecover = None
        self.health = 100
        self.armor = 100
        self.offset_target = None  # 移动offset的最终目标。它使得移动更加平滑。

        self.deaths = 0  # 死亡次数
        self.gaming_time = 0  # 游玩的时间

    def dealevent(self, event):
        if event.type == pg.KEYDOWN:
            if event.key in self.keydown:
                self.keydown[event.key] = 1
        elif event.type == pg.KEYUP:
            if event.key in self.keydown:
                self.keydown[event.key] = 0

    def hurt(self, points: int, raiseerror=False):
        if points <= 0:
            return
        elif points <= self.armor:
            self.armor -= points
        else:
            self.health -= points-self.armor
            self.armor = 0
            if self.health < 0:
                self.health = 0
        if self.health <= 0:
            self.death()
            if raiseerror:
                raise Death

    def death(self):
        self.deaths += 1
        bgd_im = Im.new('RGBA', SCREEN_SIZE, (128, 0, 0, 128))
        Imd.Draw(bgd_im).text((SCREEN_SIZE[0]//2-300, 200), "You Died!", fill=(255, 255, 255, 255),
                              font=Imf.truetype('arial.ttf', 132))
        # Imd.Draw(bgd_im).text((SCREEN_SIZE[0]//2-200, SCREEN_SIZE[1]-150), f"Gaming time:%i:%i:%i" % (
        #     self.gaming_time//3600, (self.gaming_time % 3600)//60, int(self.gaming_time % 60)),
        #     fill=(255, 255, 255, 255), font=Imf.truetype('arial.ttf', 32))
        Imd.Draw(bgd_im).text((SCREEN_SIZE[0]//2-200, SCREEN_SIZE[1]-150), f"Deaths:%i" % self.deaths,
                              fill=(255, 255, 255, 255), font=Imf.truetype('arial.ttf', 32))
        Imd.Draw(bgd_im).text((SCREEN_SIZE[0]//2-200, SCREEN_SIZE[1]-100), "Click anywhere to respawn", fill=(255, 255, 255, 255),
                              font=Imf.truetype('arial.ttf', 32))
        Imd.Draw(bgd_im).text((SCREEN_SIZE[0]//2-200, SCREEN_SIZE[1]-50), "Press Q or Esc to quit", fill=(255, 255, 255, 255),
                              font=Imf.truetype('arial.ttf', 32))
        bgd = Media.im2pg(bgd_im)
        # 弹出gameover窗口
        self.show()
        self.main.window.blit(bgd, (0, 0))
        while True:
            self.main.clock.tick(FPS)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.main.quit()
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.position = self.main.start
                        self.keydown = {pg.K_w: 0, pg.K_e: 0, pg.K_d: 0,
                                        pg.K_x: 0, pg.K_z: 0, pg.K_a: 0, pg.K_s: 0,
                                        pg.K_i: 0, pg.K_o: 0, pg.K_l: 0,
                                        pg.K_COMMA: 0, pg.K_m: 0, pg.K_j: 0, pg.K_k: 0}
                        self.cooltime = 0
                        self.health = 100
                        self.armor = 100
                        self.offset_target = self.main.start
                        return
                elif event.type == pg.KEYDOWN:
                    if event.key in [pg.K_ESCAPE, pg.K_q]:
                        raise GameExit
                    elif event.key in [pg.K_SPACE, pg.K_RETURN]:
                        self.position = self.main.start
                        self.keydown = {pg.K_w: 0, pg.K_e: 0, pg.K_d: 0,
                                        pg.K_x: 0, pg.K_z: 0, pg.K_a: 0, pg.K_s: 0,
                                        pg.K_i: 0, pg.K_o: 0, pg.K_l: 0,
                                        pg.K_COMMA: 0, pg.K_m: 0, pg.K_j: 0, pg.K_k: 0}
                        self.cooltime = 0
                        self.health = 100
                        self.armor = 100
                        self.offset_target = self.main.start
                        return

            pg.display.update()

    def move(self, direction: int):
        try:
            _tget = self.main.maze.move(
                direction, *self.position)
            if self.main.maze.visit(*_tget) in [0, 4, 7]:
                raise Maze.CanNotMove
            elif self.main.maze.visit(*_tget) == 5:
                Hub.Prompt("BOOM!!!")
                self.main.landmine.remove(*_tget, prompt=False)
                self.main.refreshMaze()
                try:
                    self.hurt(randint(50, 120), True)
                except Death:
                    return True
            elif self.main.maze.visit(*_tget) == 10:
                self.main.approach_exit()
            self.position = _tget
            self.main.moving = True
            return True
        except Maze.CanNotMove:
            # 判断能不能向两侧动一动？
            _tget_dict = {}
            for _change in [0b001, 0b010, 0b100]:
                _direction = direction ^ _change
                if _direction not in [0b000, 0b111]:
                    try:
                        _tget_dict[_direction] = self.main.maze.move(
                            _direction, *self.position)
                        if self.main.maze.visit(*(_tget_dict[_direction])) in [0, 4, 7]:
                            _tget_dict[_direction] = None
                    except Maze.CanNotMove:
                        _tget_dict[_direction] = None

                else:
                    _tget_dict[_direction] = None

            if list(_tget_dict.values()).count(None) == 2:
                _l = list(_tget_dict.values())
                _l.remove(None)
                _l.remove(None)
                _tget = _l[0]
                self.position = _tget
                self.main.moving = True
                if self.main.maze.visit(*_tget) == 5:
                    Hub.Prompt("BOOM!!!")
                    self.main.landmine.remove(
                        *_tget, prompt=False)
                    self.main.refreshMaze()
                    try:
                        self.hurt(randint(50, 120), True)
                    except Death:
                        return True
                elif self.main.maze.visit(*_tget) == 10:
                    self.main.approach_exit()
                return True
            else:
                return False

    def show(self):
        if self.cooltime >= 0:
            self.cooltime -= 1/FPS
        else:
            self.cooltime = 0.12

            # 关注摇杆
            d = self.main.hub.rocker.getdirection()
            if d:
                originpoint = self.main.mc.map2screen(*self.position)
                if self.move(d):
                    targetpoint = self.main.mc.map2screen(*self.position)
                    self.offset_target = (self.main.offset[0]+originpoint[0]-targetpoint[0],
                                          self.main.offset[1]+originpoint[1]-targetpoint[1])
            # 看按键
            else:
                for d in self.keydown:
                    originpoint = self.main.mc.map2screen(*self.position)
                    if self.keydown[d]:
                        if self.move(self.direction[d]):
                            targetpoint = self.main.mc.map2screen(
                                *self.position)
                            self.offset_target = (self.main.offset[0]+originpoint[0]-targetpoint[0],
                                                  self.main.offset[1]+originpoint[1]-targetpoint[1])
                            break

        if self.main.zooming:
            self.rolecover = self.main.media.get_rolecover(self.main.zoom)
            self.screenpos = self.main.mc.map2screen(
                *self.position, -self.main.zoom/2, -self.main.zoom*SQRT3/4)
            self.shadecover = Media.get_shader(
                *SCREEN_SIZE, self.main.zoom, self.screenpos,
                self.main.torch.get_torch_pos())

        elif self.main.moving:
            self.screenpos = self.main.mc.map2screen(
                *self.position, -self.main.zoom/2, -self.main.zoom*SQRT3/4)
            self.shadecover = Media.get_shader(
                *SCREEN_SIZE, self.main.zoom, self.screenpos,
                self.main.torch.get_torch_pos())

        if self.offset_target is not None:
            delta = (self.offset_target[0]-self.main.offset[0],
                     self.offset_target[1]-self.main.offset[1])
            r, phi = polar(complex(*delta))
            if r <= 5:
                self.main.offset = self.offset_target
                self.main.moving = True
                self.offset_target = None
            else:
                self.main.offset = (self.main.offset[0]+round(5*cos(phi)),
                                    self.main.offset[1]+round(5*sin(phi)))
                self.main.moving = True

        self.main.hub.hpbar.change_percentage(self.health)
        self.main.hub.shbar.change_percentage(self.armor)
        self.main.window.blit(self.rolecover, self.screenpos)
        self.main.window.blit(self.shadecover, (0, 0))


class Main:
    MODE_CLASSIC = 0
    MODE_TIMER = 1
    MODE_EXTREME = 2
    MODE_CRYSTAL = 3

    def __init__(self, fp: str, window: pg.Surface, mode=0, raiseerror=False) -> None:
        self.media = Media()
        self.window = window
        self.raiseerror = raiseerror

        self.maze = Maze.Maze(SavePath/fp)
        self.mazesize = self.maze.size

        self.start = None
        # 找到主角
        for _point in self.maze:
            if self.maze.visit(*_point) == 2:
                if self.start is None:
                    self.start = _point
                self.maze.setpoint(*_point, 1)
                break
        else:
            self.start = (0, 0, 0)

        self.clock = pg.time.Clock()
        self.zoom = 30  # 放大倍数
        self.mc = MotionControl(self)
        self.offset = (0, 0)  # 迷宫左上角落在屏幕的哪一部分
        _fxpt = self.mc.map2screen(*self.start)
        _tget = SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2
        self.offset = (_tget[0]-_fxpt[0], _tget[1]-_fxpt[1])

        self.role = Role(self)
        self.moving = True
        self.zooming = True

        self.mazecover = None
        self.torch = Hub.Torch(self, self.maze)
        self.landmine = Hub.LandMine(self, self.maze)
        self.barrier = Hub.Barrier(self, self.maze)
        self.hub = Hub.HUB(self)
        self.Enemy = Enemies.Enemy
        Enemies.Enemy.init()
        self.portals = Enemies.Portals
        self.portals.read(self, self.maze)
        self.read_moreinfo()
        self.refreshMaze()

        self.mode = mode

    def save(self):
        if self.maze.visit(*self.role.position) == 10:
            Hub.Prompt("Cannot save the game at the exit")
            return

        filename = "MazeSavingRecord_size%i.thirdmaze" % self.mazesize
        try:
            open(SavePath/filename, 'rb').close()
            if True:
                opt = ErrorNotice.Confirm_Notice(
                    'File "%s" already exists. What do you want to do? ' % filename,
                    opts=["Save&cover", "Save as \"...\"", "Cancel"], optdict={0: 0, 1: 1, 2: 2})\
                    .mainloop()
                if opt == 0:
                    pass
                elif opt == 1:
                    i = 1
                    while True:
                        filename = "MazeSavingRecord_size%i_(%i).thirdmaze" % (
                            self.mazesize, i)
                        try:
                            open(SavePath/filename, 'rb').close()
                            i += 1
                        except FileNotFoundError:
                            break
                else:
                    self.maze.setpoint(*self.role.position, 1)
                    Hub.Prompt("Save operation canceled")
                    return False
        except FileNotFoundError:
            pass

        self.maze.setpoint(*self.role.position, 2)
        self.save_moreinfo()
        self.maze.write(SavePath/filename)
        self.maze.setpoint(*self.role.position, 1)
        Hub.Prompt("Saved to %s" % filename)
        return True

    def save_moreinfo(self) -> bytes:
        out = b''
        out += self.role.health.to_bytes(1, 'big')
        out += self.role.armor.to_bytes(1, 'big')
        out += bytes([255]*9+[0])

        # death times
        out += self.role.deaths.to_bytes(4, 'big')
        # survival duration
        out += round(self.role.gaming_time).to_bytes(4, 'big')

        # enemy number
        out += len(list(Enemies.Enemy.__iter__())).to_bytes(2, 'big')
        for enemy in Enemies.Enemy.__iter__():
            out += enemy.health.to_bytes(2, 'big')
            out += enemy.attack_value.to_bytes(2, 'big')
            out += round(enemy.attack_gap*100).to_bytes(2, 'big')
            out += enemy.position[0].to_bytes(4, 'big')
            out += enemy.position[1].to_bytes(4, 'big')
            out += enemy.position[2].to_bytes(4, 'big')

        out += len(Enemies.Portals.portals).to_bytes(2, 'big')
        for portal in Enemies.Portals.portals:
            out += portal.vacancy.to_bytes(2, 'big')

        self.maze.more_info = out
        return out

    def read_moreinfo(self):
        src = self.maze.more_info
        if len(src) == 0:
            return False
        self._tick = 0

        def getint(n: int):
            out = src[self._tick:self._tick+n]
            self._tick += n
            try:
                return int(out.hex(), 16)
            except ValueError:
                return False
        self.role.health = getint(1)
        self.role.armor = getint(1)

        getint(9)
        getint(1)
        self.role.deaths = getint(4)
        self.role.gaming_time = getint(4)

        for i in range(getint(2)):
            health = getint(2)
            attack_value = getint(2)
            attack_gap = getint(2)/100
            x, y, z = getint(4), getint(4), getint(4)
            Enemies.Enemy(self, (x, y, z), health,
                          attack_value, attack_gap)

        getint(2)
        for portal in Enemies.Portals.portals:
            portal.vacancy = getint(2)
            print(f"portal vacancy(wasted): {portal.vacancy}")

        del self._tick
        return True

    def refreshMaze(self):
        pic = self.maze.show2(self.zoom, self.torch.torches.keys(),
                              self.landmine.landmines.keys(), self.barrier.barriers.keys())
        self.mazecover = pg.image.frombuffer(
            pic.tobytes(), pic.size, 'RGBA')

    def approach_exit(self):
        if self.mode in [self.MODE_CLASSIC, self.MODE_EXTREME]:
            _enemynum = len(list(Enemies.Enemy.__iter__()))
            if _enemynum == 0:
                self._win()
            else:
                Hub.Prompt(
                    f"There are still {_enemynum} enemies in the world.", 5)
                Hub.Prompt(f"Go and kill all of them!", 5)
        else:
            self._win()

    def _win(self):
        self.fireworks = []
        letter = Fireshow.Letter(self)
        mask = Im.new('RGBA', SCREEN_SIZE, (0, 0, 0, 128))
        Imd.Draw(mask).text((SCREEN_SIZE[0]//2-100, SCREEN_SIZE[1]//2-50),
                            "You Win!", (255, 201, 14, 255), Imf.truetype('arial.ttf', 72))
        mask = Media.im2pg(mask)

        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.quit()
                if event.type == pg.MOUSEBUTTONDOWN:
                    raise GameExit
                elif event.type in [pg.MOUSEBUTTONUP, pg.KEYUP]:
                    self.mc.dealevent(event)
                    self.role.dealevent(event)
                    self.hub.dealevent(event)
                letter.dealevent(event)
            if not randint(0, Fireshow.POSSIBILITY):
                self.fireworks.append(Fireshow.Firework(self))

            self.portals.show()
            self.mc.show()

            self.window.blit(self.media.backgroundcover, (0, 0))
            self.window.blit(self.mazecover, self.offset)
            self.role.show()

            self.window.blit(mask, (0, 0))
            for firework in self.fireworks:
                firework.show()

            pg.display.update()
            self.clock.tick(FPS)

    def quit(self):
        if self.raiseerror:
            raise GameExit
        else:
            pg.quit()
            raise SystemExit

    def mainloop(self):
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.quit()
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_RETURN:
                        Hub.Prompt("Key<Return> Pressed!")
                        # self.role.armor -= 3
                self.mc.dealevent(event)
                self.role.dealevent(event)
                self.hub.dealevent(event)
            self.portals.show()

            if self.zooming:
                self.refreshMaze()
            self.mc.show()
            Hub.Wrench.show(self)
            Enemies.Enemy.refresh()

            self.window.blit(self.media.backgroundcover, (0, 0))
            self.window.blit(self.mazecover, self.offset)
            Enemies.Enemy.show()
            self.role.show()
            self.hub.show()
            Hub.Prompt.show(self.window)

            pg.display.update()
            self.zooming = False
            self.role.gaming_time += 1/FPS
            self.clock.tick(FPS)


if __name__ == "__main__":
    window = display_init()
    # Main("Maze2_size200_data.thirdmaze").mainloop()
    # Main("MazeSavingRecord_size100.thirdmaze").mainloop()
    Main("Maze2.2_size100_data.thirdmaze", window).mainloop()
