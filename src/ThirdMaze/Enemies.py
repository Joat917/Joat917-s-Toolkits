from BaseImport import *
from Maze import *


class Media:
    def __init__(self) -> None:
        self.enemy = Im.new('RGBA', (16, 16))
        Imd.Draw(self.enemy).ellipse(
            (0, 0, 15, 15), fill=(216, 0, 0, 255))

    @staticmethod
    def im2pg(im: Im.Image, format='RGBA'):
        return pg.image.frombuffer(im.tobytes(), im.size, format)

    def get_enemycover(self, zoom: int):
        return Media.im2pg(self.enemy.resize((zoom, zoom)))


MEDIA = Media()


class MiniHPBar:
    def __init__(self, enemy) -> None:
        self.host = enemy
        self.origin_health = enemy.health
        self.health = self.origin_health

        self.image = Im.new('RGBA', MINI_HPBAR_SIZE, (255, 255, 255, 128))
        Imd.Draw(self.image).rectangle(
                (1, 1, MINI_HPBAR_SIZE[0]-2, MINI_HPBAR_SIZE[1]-2),
                (255, 0, 0, 128))
        self.cover = MEDIA.im2pg(self.image)
        pass

    def show(self):
        if self.host.health != self.health:
            self.health = self.host.health
            self.image = Im.new('RGBA', MINI_HPBAR_SIZE, (255, 255, 255, 128))
            Imd.Draw(self.image).rectangle(
                (1, 1, max(MINI_HPBAR_SIZE[0]*self.health//self.origin_health-1,1), MINI_HPBAR_SIZE[1]-2),
                (255, 0, 0, 128))
            self.cover = MEDIA.im2pg(self.image)
        position = self.host.position
        pos2 = self.host.main.mc.map2screen(*position)
        pos3 = pos2[0]-MINI_HPBAR_SIZE[0]//2, pos2[1]-self.host.main.zoom//2
        self.host.main.window.blit(self.cover, pos3)


"""
重新设置Enemy的AI
阶段0：等队友
1. 远离自己的Portal，至少8格开外；
2. 随机游荡（避开和Enemy重合，必要时可以静止或者后退），但是不要离开到16格开外；
3. 如果在5格内发现Role，直接抵近肉搏。伤害所有周围的生物，包括Enemy。
4. 检查自己16格以内的范围内Enemy的数量是否达到阈值，阈值是定值在5~10之间。

阶段1：组队集合（队伍编号唯一）
1. 检查自己的队伍和集合地点，寻路到集合地点附近6格以内。地点要在Portal范围8格开外。
2. 如果路被队友堵住了，并且堵住的那个人认为自己到了指定地点，则认为自己也到了指定地点。
3. 队长为队伍随机设置巡逻点，检查队员是否50%以上都有到达目标，如果是，集体切换目标巡逻点。
4. 队员不断检查是否到达目标巡逻点。

阶段2：战斗
1. 全员迫近对方，并且定向攻击。不断追击，如果失去目标，沿着原计划路径前进到底，之后静止。

重置Portal的AI
冷却时间3秒，每轮有20%产生一个Enemy
如果Role距离大于50，停止工作
如果整个地图中Enemy数量大于0.1*size**2，停止工作。
如果整个地图中Enemy数量大于1200时候，停止工作。
"""


class Enemy:
    enemies = {}

    @staticmethod
    def init():
        Enemy.enemies = {}
        EnemyTeam.teams = {}
        Portals.portals = []

    def __init__(self, main, position: tuple, health=50, attack_value=5, attack_gap=0.5) -> None:
        self.health = health
        self.attack_value = attack_value
        self.attack_gap = attack_gap
        self.main = main
        self.position = position
        self.mini_hpbar = MiniHPBar(self)
        self.team = None

        # 如果这个地方已经有人占了，不来也罢
        for enemy in self.enemies.values():
            if enemy is not None and self.position == enemy.position:
                print("Generation Failure: Occupied")
                del self
                return

        # 生成一个身份号码
        self.identity = randint(0, 32767)
        if self.identity in self.enemies:
            for _t in range(5):
                self.identity = randint(0, 32767)
                if self.identity not in self.enemies:
                    break
            else:
                for self.identity in range(0, 32768):
                    if self.identity not in self.enemies:
                        break
                else:
                    print("Generation Failure: Identity full")
                    del self
                    return
        self.enemies[self.identity] = self

        self.attack_cool_time = self.attack_gap
        self.moving_cool_time = 0.5
        self.phase = 0
        self.maketeam_threhold = randint(5, 10)
        self.cover = MEDIA.get_enemycover(self.main.zoom)
        self._old_place = None  # 上一次移动之前自己在哪里？
        self.path = {}  # 有没有设置路径？
        self.arrival = False  # 是否到达目的地？
        self.blacklist = []  # 仇敌！！！的号码
        self.stuck_count = 0  # 路被堵住的时候冲过去
        self.portal=self.get_nearest_portal()[0]

    @classmethod
    def __iter__(cls):
        buffer = list(cls.enemies.values())
        try:
            while True:
                buffer.remove(None)
        except ValueError:
            return iter(buffer)

    def get_nearest_portal(self):
        "得到距离自己最近的一个或几个Portal"
        _nearest_distance = float('inf')
        _nearest_portal = []
        for _portal in Portals.portals:
            if _portal is not None:
                _distance = Maze.distance(self.position, _portal.position)
                if _distance < _nearest_distance:
                    _nearest_distance = _distance
                    _nearest_portal = [_portal]
                elif _distance == _nearest_distance:
                    _nearest_portal.append(_portal)
        return _nearest_portal

    def hurt(self, points: int, attacker=None):
        self.health -= points
        if attacker is not None and attacker.health > 0:
            "revenge! "
            self.blacklist.append(attacker.identity)
        if self.health <= 0:
            self.enemies[self.identity] = None
            del self
            return

    def attack(self, desperate=False):
        "desperate: attack whoever nearby!"
        _attack_value = randint(self.attack_value-1, self.attack_value+1)
        if random() > 0.95:
            _attack_value *= 2

        neighbors = self.main.maze.neighbors(*self.position)
        if self.main.role.position in neighbors:
            self.moving = False
            if self.attack_cool_time <= 0:
                self.main.role.hurt(_attack_value)
                if desperate:
                    for enemy in self.__class__.__iter__():
                        if enemy.position in neighbors:
                            enemy.hurt(_attack_value, self)
                self.attack_cool_time = self.attack_gap
        # revenge
        if self.attack_cool_time <= 0 and self.blacklist:
            ...

    def get_destination(self, no_turnback=False):
        "自己能够移动到哪些位置。no_turnback指不回头，在遭遇死胡同的时候被忽视。"
        neighbors = self.main.maze.neighbors(*self.position)
        desti = []
        for pos in neighbors:
            if self.main.maze.visit(*pos) not in [0, 4, 7]:
                desti.append(pos)
        if no_turnback and len(desti) > 1 and (self._old_place in desti):
            desti.remove(self._old_place)
        return desti

    def followpath(self, reset=True):
        "跟随self.path到达目的地。如果不能前进，视reset参数决定是否重置path参数，并返回False"
        if self.position not in self.path or self.path[self.position] == None:
            if reset:
                self.path = {}
            return False
        return self.moveto(self.path[self.position])

    def AI(self):
        if self.phase == 0:
            roledist = self.main.maze.distance(
                self.position, self.main.role.position)  # 到 role的距离
            # 看到role
            if 1 < roledist <= 5:
                # 追逐
                if not self.followpath():
                    if self.path == {}:
                        self.path, _ = self.main.maze.astar(
                            self.main.role.position, self.position)
                        # self.path, _ = self.main.maze.astar(
                        #     self.position, self.main.role.position)
                        self.followpath()
            elif roledist == 1:
                # 攻击
                self.attack(True)
            elif roledist == 0:
                # 躲开
                self.moveto(choice(self.get_destination()))
            # 没有看到
            else:
                nearest_portal = self.portal
                portaldist = self.main.maze.distance(
                    self.position, nearest_portal.position)
                if portaldist <= 8:
                    # 离门太近了，选择最远离的方向进行行动。
                    desti = self.get_destination(True)  # 所有可能目的地的集合
                    desti = sorted(desti, key=lambda pos: self.main.maze.distance(
                        pos, nearest_portal.position))[-1]  # 最合适的那个方向
                    self.moveto(desti)
                elif portaldist > 16:
                    # 离门太原了，选择最靠近的方向进行行动。
                    desti = self.get_destination(True)  # 所有可能目的地的集合
                    desti = sorted(desti, key=lambda pos: self.main.maze.distance(
                        pos, nearest_portal.position))[0]  # 最合适的那个方向
                    self.moveto(desti)
                else:
                    # 随机游荡
                    if choice([True, False]):
                        self.moveto(choice(self.get_destination(True)))
                    # 试图拉起队伍
                    nearby_mates = []
                    for enemy in Enemy.__iter__():
                        if enemy.team is None and self.main.maze.distance(self.position, enemy.position) <= 16:
                            nearby_mates.append(enemy)
                    if len(nearby_mates) > self.maketeam_threhold:
                        EnemyTeam(self, [self]+nearby_mates)
        elif self.phase == 1:
            # 判断是否进入战斗状态
            if self.main.maze.distance(
                    self.position, self.main.role.position) < 8:
                for e in self.team.teammates:
                    e.phase = 2
            # 走向目的地
            if not self.followpath() and not self.arrival:
                if self.path == {}:
                    # 为自己寻路
                    desti = self.team.destination
                    if self.main.maze.distance(self.position, desti) > 1:
                        self.path, _ = self.main.maze.astar(
                            desti, self.position)
                        # self.path, _ = self.main.maze.astar(
                        #     self.position, desti)
                        self.followpath()
                    else:
                        self.arrival = True
                elif self.moving_cool_time <= 0:
                    # 说明来路被堵住了，此时根据临近队友判断是否到达
                    self.stuck_count += 1
                    for enemy in Enemy.__iter__():
                        if enemy.team == self.team and enemy.arrival and self.main.maze.distance(self.position, enemy.position) <= 1:
                            self.arrival = True
                            break
        elif self.phase == 2:
            roledist = self.main.maze.distance(
                self.position, self.main.role.position)  # 到 role的距离
            if roledist > 1:
                # 追逐
                if not self.followpath():
                    self.path, _ = self.main.maze.astar(
                        self.main.role.position, self.position)
                    # self.path, _ = self.main.maze.astar(
                    #         self.position, self.main.role.position)
                    self.followpath()
            elif roledist == 1:
                # 攻击
                self.attack(False)
            elif roledist == 0:
                # 躲开
                self.moveto(choice(self.get_destination()))

    def moveto(self, position: tuple, check=True):
        if self.moving_cool_time > 0:
            return False
        if self.main.maze.visit(*position) in [0, 4, 7]:
            return False
        if check and self.stuck_count < 10:
            if position == self.main.role.position:
                return False
            for enemy in self.__class__.__iter__():
                if enemy.position == position:
                    return False
        # print('\r', position, end='')
        self._old_place = self.position
        self.position = position
        self.stuck_count = 0
        # check mine
        if self.main.maze.visit(*position) == 5:
            self.main.landmine.remove(
                *position, prompt=False)
            self.main.refreshMaze()
            self.hurt(randint(50, 120))
        # set cool time
        self.moving_cool_time = 0.5
        return True

    def _tick(self):
        "include AI"
        if self.attack_cool_time > 0:
            self.attack_cool_time -= 1/FPS
        if self.moving_cool_time > 0:
            self.moving_cool_time -= 1/FPS
        self.AI()

    def _show(self):
        self._tick()

        if self.main.zooming:
            self.cover = MEDIA.get_enemycover(self.main.zoom)

        self.main.window.blit(self.cover, self.main.mc.map2screen(
            *self.position, -self.main.zoom/2, -self.main.zoom*SQRT3/4))
        self.mini_hpbar.show()

    @classmethod
    def refresh(cls):
        for enemy in cls.__iter__():
            if enemy is not None:
                enemy.AI()
        keys = list(cls.enemies.keys())
        for key in keys:
            if cls.enemies[key] is None:
                cls.enemies.pop(key)

    @classmethod
    def show(cls):
        for enemy in cls.__iter__():
            enemy._show()
        EnemyTeam.tick()


class EnemyTeam:
    teams = {}

    def __init__(self, captain: Enemy, teammates: list) -> None:
        self.teamid = randint(0, 32767)
        if self.teamid in self.teams:
            for _t in range(5):
                self.teamid = randint(0, 32767)
                if self.teamid not in self.teams:
                    break
            else:
                for self.teamid in range(32768):
                    if self.teamid not in self.teams:
                        break
                else:
                    del self
                    self = None
                    return

        self.teammates = teammates
        self.captain = captain
        self.destination = self.captain.position
        self.blacklist = []
        for e in self.teammates:
            self.blacklist += e.blacklist
            del e.blacklist
            e.blacklist = self.blacklist

        for e in self.teammates:
            e.team = self
            e.phase = 1

    def allarrival(self, proport=0.81):
        "是不是大部分的队友都到达了？"
        return [bool(e.arrival) for e in self.teammates].count(True) >= proport*len(self.teammates)

    def _tick(self):
        if self.allarrival():
            if self.blacklist:
                for e in self.blacklist:
                    if e in Enemy.enemies and Enemy.enemies[e] is not None:
                        self.destination = e.position
                        break
                else:
                    self.destination = choice(self.captain.main.maze)
                    while self.captain.main.maze.visit(*self.destination) in [0, 4, 7]:
                        self.destination = choice(self.captain.main.maze)
            for e in self.teammates:
                e.arrival = False
    
    @classmethod
    def tick(cls):
        for t in cls.teams.values():
            t._tick()




class Portals:
    portals = []

    @classmethod
    def read(cls, main, maze: Maze):
        cls.portals = []
        for point in maze:
            if maze.visit(*point) == 7:
                cls.portals.append(Portals(main, point))
        print(len(cls.portals))

    def __init__(self, main, position: tuple) -> None:
        self.main = main
        self.position = position
        self.vacancy = 10
        self.cool_time = 3
        pass

    def _tick(self):
        if self.cool_time > 0:
            self.cool_time -= 1/FPS
            return
        # 满足一定条件停止工作
        if self.main.maze.distance(self.position, self.main.role.position) > 50 or len(Enemy.enemies) > min(1200, 0.1*self.main.maze.size**2):
            return
        self.cool_time = 3+random()-0.5
        if random() < 0.2:
            try:
                point = choice(self.main.maze.neighbors(*self.position))
                if self.main.maze.visit(*point) == 1 and point not in Enemy.enemies:
                    Enemy(self.main, point)
                    print("Enemy generated at (%i, %i, %i)"
                          % (point))
            except Exception as e:
                print(e)

    @classmethod
    def show(cls):
        for p in cls.portals:
            p._tick()
