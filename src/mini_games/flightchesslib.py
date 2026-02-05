import enum
import numpy as np
import os

class Locations(enum.Enum):
    AIRWAY = 0
    APRON = 1
    FINAL = 2
    RUNWAY = 3

class Colors(enum.Enum):
    RED = 0
    YELLOW = 1
    BLUE = 2
    GREEN = 3

STRING_COLORS = ['Red', 'Yellow', 'Blue', 'Green']

class Dice:
    def __init__(self, seed=None):
        self.rng = np.random.Generator(np.random.PCG64(seed))
        self.rounds = 0
        self.current_player = None
        self.current_value = None
        self.last_value = None
        self.continuous_sixes = 0

    def roll(self):
        "掷骰子，返回1-6的值"
        self.last_value = self.current_value
        self.current_value = int(self.rng.integers(1, 7))
        self.rounds += 1
        if self.current_value == 6:
            self.continuous_sixes += 1
        if self.last_value != 6 or self.current_player is None:
            self.current_player = self.next_player()
        return self.current_value
    
    def next_player(self):
        "切换到下一个玩家"
        self.continuous_sixes = 0
        if self.current_player is None:
            self.current_player = Colors.RED
        else:
            self.current_player = Colors((self.current_player.value - 1) % 4)
        return self.current_player

class Plane:
    def __init__(self, color: Colors, idx:int, game:'Game'=None):
        self.color = color
        self.idx = idx
        self.location = self.apron = (Locations.APRON, self.idx*4+self.color.value)
        self.skipped = False # 当移动到同色航道时，将自动向前移动4格，每回合只能触发一次。标记是否触发
        self.arrival = False # 是否到达终点

        self.game = game # 所属游戏对象
        self.stack = None # 其上是否堆叠了其他飞机。构成一循环链表。

    @property
    def planes_list(self):
        return self.game.planes
    
    @property
    def statistics_dict(self):
        return self.game.statistics[self.color]

    @classmethod
    def get_next_position(cls, color:Colors, current_location:tuple[Locations, int], steps:int):
        "获取在执行点数后，所有途径的位置（包括起点和终点）"
        if steps == 0:
            return [current_location]
        if steps < 0:
            raise ValueError("Steps must be non-negative")
        if current_location[0] == Locations.APRON:
            if steps < 5:
                raise ValueError("Cannot move to runway with less than 5 steps")
            return [current_location, (Locations.RUNWAY, color.value)]
        elif current_location[0] == Locations.RUNWAY:
            return [current_location]+[(Locations.AIRWAY, (i+2+13*color.value)%52) for i in range(1, steps+1)]
        elif current_location[0] == Locations.AIRWAY:
            pos  = current_location[1] % 52
            if pos == 13*color.value:
                next_positions = cls.get_next_position(color, (Locations.FINAL, color.value), steps-1)
            else:
                next_positions = cls.get_next_position(color, (Locations.AIRWAY, (pos+1) % 52), steps-1)
            return [current_location] + next_positions
        elif current_location[0] == Locations.FINAL:
            starting_point = current_location[1] // 4
            return [(Locations.FINAL, (5-abs(5-(starting_point+i))) * 4 + color.value) for i in range(steps+1)]
        else:
            raise ValueError("Invalid location")
        
    def can_move(self, steps:int):
        "把点数告诉自己，看看自己能不能做点什么"
        if self.arrival:
            return False
        if self.location[0] == Locations.APRON:
            return steps >= 5
        return True
        
    def get_progress(self):
        "返回一个数字，表征自己自从出发已经走过了多少格子。"
        if self.arrival:
            return 200
        if self.location[0] == Locations.APRON:
            return 0
        elif self.location[0] == Locations.RUNWAY:
            return 1
        elif self.location[0] == Locations.AIRWAY:
            return 2+(self.location[1]-2-13*self.color.value) % 52
        elif self.location[0] == Locations.FINAL:
            return 60+self.location[1]//4
        else:
            raise ValueError("Invalid location")
        
    def get_all_stacked_planes(self):
        "获取堆叠在自己上的所有飞机。第一个输出自己"
        current_plane = self
        yield self
        while current_plane.stack is not None and current_plane.stack is not self:
            if current_plane.stack is current_plane:
                current_plane.stack=None
                break
            current_plane = current_plane.stack
            yield current_plane
        
    def move_to(self, new_location:tuple[Locations, int]):
        "把自己移动到新的位置"
        # print("Move From", self.location, "To", new_location)
        for plane in self.get_all_stacked_planes():
            plane.location = new_location

    def fight(self):
        "与当前格子上的其他飞机进行战斗"
        if self.planes_list is not None:
            other_planes = [p for p in self.planes_list if p.location==self.location and p is not self]
            if not other_planes:
                return
            if other_planes[0].color != self.color:
                self_stacked_planes = list(self.get_all_stacked_planes())
                other_stacked_planes = list(other_planes[0].get_all_stacked_planes())

                other_stacked_planes.pop(0).crash(self)
                while self_stacked_planes and other_stacked_planes:
                    self_stacked_planes.pop(0).crash(other_planes[0])
                    other_stacked_planes.pop(0).crash(self)
            elif self.location[0]!=Locations.RUNWAY:
                bottom_plane = other_planes[0]
                self_stacked_planes = list(self.get_all_stacked_planes())
                other_stacked_planes = list(bottom_plane.get_all_stacked_planes())
                if not set(self_stacked_planes)==set(other_stacked_planes):
                    # 连接两堆互不相连的飞机
                    assert not set(self_stacked_planes).intersection(other_stacked_planes)
                    self_stacked_planes[-1].stack = other_stacked_planes[0]
                    other_stacked_planes[-1].stack = self_stacked_planes[0]

    def crash(self, other_plane:'Plane'=None):
        "牢大坠机力"
        crash_distance = self.get_progress()
        self.move_to(self.apron)
        self.statistics_dict['crash_counts'] += 1
        self.statistics_dict['crash_distance'] += crash_distance
        if other_plane is not None:
            other_plane.statistics_dict['damage_counts'] += 1
            other_plane.statistics_dict['damage_distance'] += crash_distance

        stacked_planes = list(self.get_all_stacked_planes())[1:]
        if len(stacked_planes) > 1:
            stacked_planes[-1].stack = self.stack
        elif len(stacked_planes) == 1:
            stacked_planes[0].stack = None
        self.stack = None  

    def move(self, steps:int):
        "移动指定步数，并考虑全部特殊规则"
        # print("Plane", self.color, self.idx, "moving", steps, "steps from", self.location)
        if not self.can_move(steps):
            raise ValueError("This plane cannot move the specified steps")
        path = self.get_next_position(self.color, self.location, steps)
        for pos in path[1:]:
            self.move_to(pos)
        # 记录统计数据
        self.statistics_dict['movement_distance'] += steps
        self.statistics_dict['stacked_movement_distance'] += (len(list(self.get_all_stacked_planes()))-1)*steps
        if self.location[0] == Locations.FINAL and path[-1][1]//4!=5 and any((loc[0]==Locations.FINAL and loc[1]//4==5) for loc in path):
            overshoot_steps = 5-path[-1][1]//4
            self.statistics_dict['total_moveback_distance'] += overshoot_steps
        
        self.fight()

        _loop_flag = True
        while _loop_flag:
            _loop_flag = False
            if not (self.location[0] == Locations.AIRWAY and self.location[1]%4 == self.color.value):
                break
            if self.location[1]%13==0:
                break
            elif self.location[1]%13==7:
                self.move_to((Locations.AIRWAY, (self.location[1]+12)%52))
                self.statistics_dict['skip_counts'] += 1
                self.statistics_dict['skip_distance'] += 12
                self.fight()
                _loop_flag = True
            elif not self.skipped:
                self.skipped = True
                self.move_to((Locations.AIRWAY, (self.location[1]+4)%52))
                self.statistics_dict['skip_counts'] += 1
                self.statistics_dict['skip_distance'] += 4
                self.fight()
                _loop_flag = True

        if self.location[0] == Locations.FINAL and self.location[1]//4 == 5:
            for plane in list(self.get_all_stacked_planes()):
                plane.arrival = True
                plane.stack = None
                plane.move_to(plane.apron)

    def newround(self):
        "每回合开始时调用，重置状态"
        self.skipped = False


class AnimatedPlane(Plane):
    def __init__(self, color, idx, game, animation_duration=0.5, fps=60, board_size=780):
        super().__init__(color, idx, game)
        self.animations = [] # 动画步骤：((start_tick, end_tick, start_pos, end_pos), ...)
        self._current_tick = 0
        self._registered_tick = 0
        self.animation_duration=animation_duration # 每一步动画的持续时间，单位秒
        self.fps = fps # 每秒帧数
        self.board_size = board_size # 棋盘大小，单位像素

    def move_to(self, new_location, start_tick=None):
        old_location = self.location
        if start_tick is None:
            start_tick = self._registered_tick
        end_tick = round(start_tick + self.animation_duration*self.fps)
        for plane in self.get_all_stacked_planes():
            plane.animations.append((start_tick, end_tick, old_location, new_location))
            plane.location = new_location
        self._registered_tick = end_tick

    @staticmethod
    def mix(p1, p2, β):
        "当β∈[0,1]时，从p1到p2插值"
        β = np.clip(β, 0, 1)
        β = (1-np.cos(β*np.pi))/2
        return p1[0]*(1-β)+p2[0]*β, p1[1]*(1-β)+p2[1]*β
    
    def scale(self, location:tuple[Locations, int]):
        "将棋盘位置转换为像素坐标"
        x, y = POINTS_COORD[location[0].value, location[1]]
        return x*self.board_size/780, y*self.board_size/780
    
    def crash(self, other_plane:Plane=None):
        if other_plane is not None:
            self._registered_tick = max(self._registered_tick, other_plane._registered_tick)
        super().crash(other_plane)
    
    def tick(self):
        "获取当前动画帧的位置"
        if self.animations:
            start_tick, end_tick, start_pos, end_pos = self.animations[0]
            if self._current_tick>=end_tick:
                self.animations.pop(0)
                if not self.animations:
                    return self.scale(end_pos)
                start_tick, end_tick, start_pos, end_pos = self.animations[0]
            beta = (self._current_tick-start_tick)/(end_tick-start_tick)
            self._current_tick += 1
            return self.mix(self.scale(start_pos), self.scale(end_pos), beta)
        return self.scale(self.location)
    
    def newround(self):
        super().newround()
        self._current_tick = 0
        self._registered_tick = 0
        self.animations = []
    
class PlayerBase:
    def __init__(self, color:Colors, game:'Game'):
        self.color = color
        self.game = game

    def choose_plane(self, movable_planes:list[Plane], dice_value:int):
        "从可移动的飞机列表中选择一架飞机进行移动"
        raise NotImplementedError


class Game:
    def __init__(self, players:dict[Colors, PlayerBase], seed=None, plane_factory=Plane, plane_count=4):
        self.dice = Dice(seed)
        assert 1<=plane_count<=4
        
        self.statistics = {color:{
            'rank': None, # 最终排名，1-4（由Game对象维护）
            'crash_counts': 0, # 被击落次数
            'crash_distance': 0, # 被击落时距离起点的距离总和
            'damage_counts': 0, # 击落对方飞机次数
            'damage_distance': 0, # 击落对方飞机时距离起点的距离总和
            'skip_counts': 0, # 跳跃航道次数
            'skip_distance': 0, # 跳跃航道时前进的距离总和
            'total_rounds': 0, # 掷骰子总次数（由Game对象维护）
            'total_moves': 0, # 移动总次数；如果无子可动则不计入（由Game对象维护）
            'total_choices': 0, # 可选择的移动总次数；如果只有一个子可动则不计入（由Game对象维护）
            'movement_distance': 0, # 自己移动的距离总和
            'stacked_movement_distance': 0, # 堆叠移动时被堆叠飞机前进的距离总和
            'total_moveback_distance': 0, # 在终点处多余步数的回退距离总和
        } for color in Colors}

        self.planes = [
            plane_factory(
                color=color, idx=idx, 
                game=self
            )
            for idx in range(plane_count)
            for color in Colors
        ]

        self.players = players
        for player in self.players.values():
            player.game = self
        self.finished = {color: False for color in Colors}

    def gameover(self):
        return all(self.finished.values())

    def step(self):
        "进行游戏的一个步骤，掷骰子并移动"
        if self.gameover():
            raise RuntimeError("Game is already over")
        self.dice.roll()
        while self.finished[self.dice.current_player]:
            self.dice.next_player()

        # 初始化所有飞机
        for plane in self.planes:
            plane.newround()
        
        # 当前玩家连续掷出三个6，直接强制返回起点
        if self.dice.continuous_sixes >= 3:
            for plane in self.planes:
                if plane.color == self.dice.current_player and not plane.arrival:
                    plane.crash()
            self.dice.continuous_sixes = 0
            self.dice.next_player()
            return

        movable_planes = [plane for plane in self.planes if plane.color==self.dice.current_player and plane.can_move(self.dice.current_value)]
        self.statistics[self.dice.current_player]['total_rounds'] += 1

        if not movable_planes:
            return
        
        self.statistics[self.dice.current_player]['total_moves'] += 1
        if len(movable_planes) > 1 and len(set(p.location for p in movable_planes)) > 1:
            self.statistics[self.dice.current_player]['total_choices'] += 1
            plane_to_move = self.players[self.dice.current_player].choose_plane(movable_planes, self.dice.current_value)
            if not plane_to_move in movable_planes:
                raise ValueError("Chosen plane is not in the list of movable planes")
            plane_to_move.move(self.dice.current_value)
        else:
            movable_planes[0].move(self.dice.current_value)
        
        if all(plane.arrival for plane in self.planes if plane.color==self.dice.current_player):
            self.finished[self.dice.current_player] = True
            rank = int(sum(self.finished.values()))
            self.statistics[self.dice.current_player]['rank'] = rank

        return
    
try:
    from PIL import Image, ImageDraw, ImageFont
    import cv2
    import json
    import tqdm
    class VideoGame(Game):
        "AI对战，然后将游戏相关信息保存为文件和视频"
        def __init__(self, players:dict[Colors, PlayerBase], record_dir:str, seed=None, fps=30, animation_duration=0.2, step_gap=0.3):
            super().__init__(players, seed, lambda*args,**kwargs:AnimatedPlane(*args,**kwargs,animation_duration=animation_duration,fps=fps), 4)
            self.record_dir = record_dir
            os.makedirs(self.record_dir, exist_ok=True)
            self.fps = fps
            self.animation_frames = round(animation_duration*fps)
            self.step_gap_frames = round(step_gap*fps)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(
                os.path.join(self.record_dir, 'game_record.mp4'),
                fourcc, fps, (780, 780)
            )

            self.IMG_ROOT = os.path.abspath('.')
            while 'src' not in os.listdir('.'):
                self.IMG_ROOT = os.path.dirname(self.IMG_ROOT)
                if self.IMG_ROOT == os.path.dirname(self.IMG_ROOT):
                    raise FileNotFoundError("Cannot find project root directory")
            self.IMG_ROOT = os.path.join(self.IMG_ROOT, 'assets', 'flightchess')
            self.FLIGHT_PICS = [Image.open(os.path.join(self.IMG_ROOT, f"icon_{clr}.png")) for clr in ['red', 'yellow', 'blue', 'green']]
            self.FINAL_PICS = [im.copy().convert('LA').convert('RGBA') for im in self.FLIGHT_PICS]
            self.BG_PIC = Image.open(os.path.join(self.IMG_ROOT, 'board.png'))
            

        def mainloop(self):
            pbar = tqdm.tqdm(leave=False)
            while not self.gameover():
                self.step()
                pbar.set_description(f"Round {self.dice.rounds} - Player {STRING_COLORS[self.dice.current_player.value]} rolled {self.dice.current_value}")
                # 每一步动画
                base_frame = self.BG_PIC.copy()
                ImageDraw.Draw(base_frame).text(
                    (470, 300), 
                    str((self.dice.current_value if self.dice.current_value is not None else '-')), 
                    self.dice.current_player.name.lower() if self.dice.current_player is not None else 'gray', 
                    ImageFont.truetype('arial.ttf', 32)
                )
                while any(plane.animations for plane in self.planes):
                    frame = base_frame.copy()
                    
                    for plane in self.planes:
                        pos = plane.tick()
                        plane_image = self.FINAL_PICS[plane.color.value] if plane.arrival and not plane.animations else self.FLIGHT_PICS[plane.color.value]
                        frame.paste(plane_image, (round(pos[0]), round(pos[1])), plane_image)
                    self.video_writer.write(cv2.cvtColor(np.array(frame), cv2.COLOR_RGBA2BGR))
                    pbar.update()
                # 步骤间隔
                frame = base_frame
                for plane in self.planes:
                    pos = plane.tick()
                    plane_image = self.FINAL_PICS[plane.color.value] if plane.arrival and not plane.animations else self.FLIGHT_PICS[plane.color.value]
                    frame.paste(plane_image, (round(pos[0]), round(pos[1])), plane_image)
                for _ in range(self.step_gap_frames):
                    self.video_writer.write(cv2.cvtColor(np.array(frame), cv2.COLOR_RGBA2BGR))
                pbar.update()
            self.video_writer.release()
            pbar.close()
            with open(os.path.join(self.record_dir, 'statistics.json'), 'w') as f:
                json.dump({color.name.lower():value for color,value in self.statistics.items()}, f, indent=4)
except ImportError as exc:
    import traceback
    traceback.print_exc()
    pass


class PlayerRandom(PlayerBase):
    def __init__(self, color, game):
        self.rng = np.random.Generator(np.random.PCG64())
        super().__init__(color, game)

    def choose_plane(self, movable_planes, dice_value):
        return self.rng.choice(movable_planes)
    
class PlayerFirst(PlayerBase):
    def choose_plane(self, movable_planes, dice_value):
        return min(movable_planes, key=lambda p:p.get_progress())
    
class PlayerLast(PlayerBase):
    def choose_plane(self, movable_planes, dice_value):
        return max(movable_planes, key=lambda p:p.get_progress())
    
class PlayerA1(PlayerBase):
    def choose_plane(self, movable_planes, dice_value):
        # 优先选择能击落更多对方飞机的
        crashes = {p:0 for p in movable_planes}
        paths = {p:Plane.get_next_position(self.color, p.location, dice_value) for p in movable_planes}
        for plane in movable_planes:
            path = paths[plane]
            for pos in path[1:]:
                for other_plane in self.game.planes:
                    if other_plane.color != self.color and other_plane.location == pos:
                        crashes[plane] += 1
        max_crash = max(crashes.values())
        planes_filtered = [p for p, c in crashes.items() if c == max_crash]
        if len(planes_filtered) == 1:
            return planes_filtered[0]
        # 优先选择靠前的飞机
        planes_filtered.sort(key=lambda p:p.get_progress(), reverse=True)
        # 如果存在可以进入终点的飞机，选择该飞机
        for p in planes_filtered:
            if p.location[0] == Locations.AIRWAY and paths[p][-1][0] == Locations.FINAL:
                return p
        # 如果存在可以跳跃的飞机，选择该飞机
        for p in planes_filtered:
            if p.location[0] == Locations.AIRWAY and p.location[1]%4 == self.color.value:
                return p
        # 如果可以起飞，优先选择起飞
        for p in planes_filtered:
            if p.location[0] == Locations.APRON:
                return p
        # 优先叠加飞机
        for p in planes_filtered:
            for other_plane in self.game.planes:
                if other_plane is not p and other_plane.color == self.color and other_plane.location == paths[p][-1]:
                    return p
        # 如果存在即将到达终点的飞机，选择该飞机
        for p in planes_filtered:
            if p.location[0] == Locations.FINAL and p.location[1]//4 + dice_value == 5:
                return p
        # 如果飞机在终点附近，但是不能恰好到达终点，不要选它
        planes_filtered_2 = [p for p in planes_filtered if p.location[0]!=Locations.FINAL]
        if planes_filtered_2:
            planes_filtered = planes_filtered_2
        return planes_filtered[0]


POINTS_COORD_DATA_COMPRESSED = \
'>lXkT!<<*!s8W-!rr>3>!Wq1KS-=1S^m(,i:fFB?,Eg+A*M9gYnQY+54KG7#E&u`ImpbYR]%EaJgj$q$?@q_\\e$Q!n%HKE(-G\
Zt?Thlc;Y=9hPmM=qsTdo&tY8D4[T-=`YF>:e0)f$u2l\'_&<d2:bp.+l055AVgub]D3`bL)@6SFq@r/MfW!Oj:H0JYD!HT]\\41\
\\kFrfJ`5_Dh6+[\'R%OkhQj)s2c`KsiNmi#%e6_S`VicDhlB-/@D=^.aF>bYYa^V;ka91Wr<3(nI&8g>0:BJE++"uV[8$EMWkPo5\
s$GZQ4WbDKe8Ze>nFWuU4e#$eY;r0>/4#uT#H_p/&l6/JS$\\DeL"iK?jFQNO8-H:08bB^ZP,iRZ&Rn1O559Tj4W/TfFL@=cCKOj\'\
E!<&WPA=,/UG>&9Sl:>F49YHrc?H"qj0LQ\\O+>cJC8Oncj\'i0[`+0uO"o)>s6fF.q-&8^)!\\S,Ln1ND+ibu1:bSPb7W5gfi_$8%j\
c\\%NuuSgto7/qU=JGr3MZ,Z:?u]B.F;8;.^QR*eQes1r!pOQSRsZ@Gra<$.`L5%j3Y>$HoM2efeq+$&Mb&0W4+93+V)>eAo?\'nrItd\
sH"S1sZGMZ=f#7Sa@VgoSa:78H8HWRj%'
import base64,lzma
POINTS_COORD = dict(eval(lzma.decompress(base64.a85decode(POINTS_COORD_DATA_COMPRESSED)).decode())) # 假设棋盘大小为780x780，那么各个点位对应的坐标在什么地方

if __name__ == "__main__":
    game = VideoGame(
        players = {
            Colors.RED: PlayerA1(Colors.RED, None),
            Colors.YELLOW: PlayerA1(Colors.YELLOW, None),
            Colors.BLUE: PlayerA1(Colors.BLUE, None),
            Colors.GREEN: PlayerA1(Colors.GREEN, None),
        },
        record_dir = './flightchess_record',
        seed = None
    )
    game.mainloop()
    print(game.statistics)
