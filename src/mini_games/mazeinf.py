from itertools import product
import hashlib
import time
import os
from os import path
import sys
import lzma
import numpy as np
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

SCREEN_SIZE = (960, 540)
CENTER_COORD = (480, 270)
FPS = 60
SLIDE_DURATION = 0.5
BOUNCING_COEF = 0.5
sys.setrecursionlimit(2000)

class ByteStream:
    def __init__(self, source=b''):
        self.data = bytes(source)

    def __len__(self):
        return len(self.data)

    def __bool__(self):
        return len(self.data) != 0

    def get(self, n=1, strict=True):
        if not isinstance(n, int):
            raise TypeError
        if not self.data:
            raise IndexError('bytestream is empty')
        out = self.data[:n]
        self.data = self.data[n:]
        if strict and not len(out) == n:
            raise ValueError('not enough data')
        return out

    def push(self, b):
        if not isinstance(b, bytes):
            raise TypeError
        self.data += b
        return len(b)

    def to_file(self, filename):
        hash_data = hashlib.sha256(self.data).digest()
        assert len(hash_data) == 32
        zip_data = lzma.compress(self.data, format=lzma.FORMAT_XZ)
        with open(filename, 'wb') as file:
            file.write(hash_data+zip_data)

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'rb') as file:
            data = file.read()
        hash_data, zip_data = data[:32], data[32:]
        origin_data = lzma.decompress(zip_data, format=lzma.FORMAT_XZ)
        if hash_data != hashlib.sha256(origin_data).digest():
            raise ValueError("Hash check not passed!")
        return ByteStream(origin_data)


class Coord:
    def __init__(self, row, col):
        self.row = row
        self.col = col

    def __add__(self, other):
        return Coord(self.row+other.row, self.col+other.col)

    def __iadd__(self, other):
        self.row += other.row
        self.col += other.col
        return self

    def __neg__(self):
        return Coord(-self.row, -self.col)

    def __sub__(self, other):
        return Coord(self.row-other.row, self.col-other.col)

    def __isub__(self, other):
        self.row -= other.row
        self.col -= other.col
        return self

    def __mul__(self, number):
        return Coord(self.row*number, self.col*number)

    def __rmul__(self, number):
        return self*number

    def as_tuple(self):
        return (self.row, self.col)

    def toXY(self, zoom=32, x0=0, y0=0):
        "x0, y0是(0,0)点在显示屏上的坐标"
        return x0+zoom*self.col, y0-zoom*self.row

    @classmethod
    def fromXY(cls, x, y, zoom=32, x0=0, y0=0):
        return Coord(-(y-y0)/zoom, (x-x0)/zoom)

    def get_region_index(self):
        return round(self.row)//64, round(self.col)//64


class Media:
    "管理所有的媒体以及相关的函数"
    from PIL import Image as Im, ImageDraw as Imd, ImageFont as Imf
    floor = Im.new('RGBA', (32, 32), (200,)*4)
    wall = Im.new('RGBA', (32, 32), (0, 0, 0, 200))
    # background = Im.open('background.jpg').convert('RGB')
    background = Im.new('RGB', SCREEN_SIZE, (100, 149, 237))
    h_creature = Im.new('RGBA', (32, 32))
    Imd.Draw(h_creature).rectangle((5, 5, 26, 26), (164, 72, 164, 200))
    print('Media Ready.')

    @staticmethod
    def getImSurface(name):
        image = getattr(Media, name)
        return pygame.image.frombuffer(image.tobytes(), image.size, image.mode)

    @staticmethod
    def getImArray(name):
        image = getattr(Media, name)
        return np.asarray(image, np.uint8)

    @staticmethod
    def array2Surface(arr, mode='RGBA'):
        return pygame.image.frombuffer(arr[::-1, :, :].tobytes(), (arr.shape[1], arr.shape[0]), mode)

    @classmethod
    def show_background(cls, root):
        if not hasattr(cls, '_buffer_background_surface'):
            cls._buffer_background_surface = cls.getImSurface('background')
        root.blit(cls._buffer_background_surface, (0, 0))


class RegionGenerator:
    "仅用于生成区块"

    def __init__(self, target_array: np.ndarray, random_engine: np.random.Generator) -> None:
        self.target_array = target_array
        self.random_engine = random_engine
        self.random_shuffle_func = lambda x: [
            self.random_engine.shuffle(x), x][1]
        map_type = random_engine.integers(0, 2147483648)

        if map_type % 6 == 3:
            # type 1 (straight)
            self.target_array.fill(1)
            for _ in range(60):
                x_min, x_max = sorted((self.random_engine.integers(0, 64),
                                       self.random_engine.integers(0, 64)))
                if x_min < 10:
                    x_min = 0
                if x_max > 54:
                    x_max = 64
                y = random_engine.integers(0, 64)
                self.target_array[x_min:x_max+1, y] = 0
            for _ in range(60):
                y_min, y_max = sorted((self.random_engine.integers(0, 64),
                                       self.random_engine.integers(0, 64)))
                if y_min < 10:
                    y_min = 0
                if y_max > 54:
                    y_max = 64
                x = random_engine.integers(0, 64)
                self.target_array[x, y_min:y_max+1] = 0
            # self.target_array[0, :] = 0
            # self.target_array[63, :] = 0
            # self.target_array[:, 0] = 0
            # self.target_array[:, 63] = 0
        elif map_type % 12 == 4:
            # type 2 (diagnal): several diagnal tunnels
            self.target_array.fill(1)
            for _ in range(20):
                diag_coord = self.random_engine.integers(
                    0, 63)+self.random_engine.integers(0, 63)
                _r = min(diag_coord, 126-diag_coord)
                for _d in range(-_r, _r+1):
                    self.target_array[(diag_coord+_d)//2,
                                      (diag_coord-_d)//2] = 0
                    self.target_array[(diag_coord+_d+1)//2,
                                      (diag_coord-_d+1)//2] = 0
            for _ in range(20):
                diag_coord = self.random_engine.integers(
                    0, 63)+self.random_engine.integers(0, 63)
                _r = min(diag_coord, 126-diag_coord)
                for _d in range(-_r, _r+1):
                    self.target_array[(diag_coord+_d)//2,
                                      (126-diag_coord+_d)//2] = 0
                    self.target_array[(diag_coord+_d+1)//2,
                                      (125-diag_coord+_d)//2] = 0
            # self.target_array[0, :] = 0
            # self.target_array[63, :] = 0
            # self.target_array[:, 0] = 0
            # self.target_array[:, 63] = 0
        elif map_type % 12 == 8:
            # type 3 (plaza)
            self.target_array.fill(0)
            for _ in range(400):
                self.target_array[random_engine.integers(0, 64),
                                  random_engine.integers(0, 64)] = 1

        else:
            # type 0 (pure maze)
            self.target_array.fill(1)
            # _t0 = time.time()
            self.explore((self.random_engine.integers(0, 64),
                          self.random_engine.integers(0, 64)))
            # print("time consumed generating region: {:.2f}ms".format(
            #     (time.time()-_t0)*1000))
        self.decorate()
        pass

    @staticmethod
    def neighbors(t: tuple):
        "四周的八个格子"
        r, c = t
        outs = [(i, j) for i in range(max(r-1, 0), min(r+1, 63)+1)
                for j in range(max(c-1, 0), min(c+1, 63)+1)]
        outs.remove((r, c))
        return outs

    @staticmethod
    def direct_neighbors(t: tuple):
        "四边的四个格子"
        r, c = t
        if r != 0:
            yield r-1, c
        if c != 0:
            yield r, c-1
        if r != 63:
            yield r+1, c
        if c != 63:
            yield r, c+1

    def explore(self, start):
        "探索墙和地板的位置"
        self.target_array[start] = 0
        for next_move in self.random_shuffle_func(list(self.direct_neighbors(start))):
            # 看看这个格子能不能挖掉，就是它的周围有没有其它已经被挖掉的格子。
            for _detected_block in self.direct_neighbors(next_move):
                if _detected_block == start:
                    continue
                if self.target_array[_detected_block] == 0:
                    # 有其它格子被挖掉了，那就不能挖这个格子了。
                    break
            else:
                # 这个格子是安全的，可以挖！
                self.explore(next_move)

    def decorate(self):
        "把墙和地板替换成对应的装饰方块"
        for _ in range(256):
            r, c = (self.random_engine.integers(0, 64),
                    self.random_engine.integers(0, 64))
            # turn wall into floor
            if self.target_array[r, c] & 1:
                self.target_array[r, c] = 0
        pass


class Region:
    "区块"

    def __init__(self, index: tuple) -> None:
        self.data = np.zeros((64, 64), np.uint8)
        self.image = None
        self.surface = None
        self.index = index
        self.rendered = False

    @staticmethod
    def number_to_block_name(index):
        "给定方块编号，返回它的名称"
        if index & 1:
            return 'wall'
        else:
            return 'floor'

    @staticmethod
    def block_name_to_number(name):
        "给定方块名称，返回它的编号"
        if name == 'wall':
            return 1
        else:
            return 0

    @staticmethod
    def seed_generator(data1=0, data2=0, data3=0, data4=0):
        "把一些数据整合到一个种子里面。"
        return int(hashlib.sha256(f"^{data1}!{data2}@{data3}#{data4}$".encode()).hexdigest()[:8], 16)

    def datum_from_seed(self, seed: int):
        "通过种子和自己的编号生成这个区块"
        seed = self.seed_generator(seed, self.index[0], self.index[1])
        random_engine = np.random.Generator(np.random.MT19937(seed))
        RegionGenerator(self.data, random_engine)
        self.rendered = False
        return self

    @classmethod
    def from_stream(cls, stream: ByteStream):
        "从数据流中获取自己的数据"
        s = Region((0, 0))
        s.index = (int.from_bytes(stream.get(2), 'little', signed=True),
                   int.from_bytes(stream.get(2), 'little', signed=True))
        s.data = np.frombuffer(stream.get(4096), np.uint8).reshape((64, 64))
        return s

    def to_stream(self, stream: ByteStream):
        "把自己的数据输入到流中"
        stream.push(self.index[0].to_bytes(2, 'little', signed=True))
        stream.push(self.index[1].to_bytes(2, 'little', signed=True))
        stream.push(self.data.tobytes())

    def render(self):
        "绘制自己的地图"
        # print('rendered:', self.rendered)
        if not self.rendered:
            print("rendering:", self.index)
            # _t0=time.time()
            self.rendered = True
            self.image = np.zeros((2048, 2048, 4), dtype=np.uint8)
            for row, col in product(range(64), range(64)):
                self.image[row*32:row*32+32, col*32:col*32+32, :] \
                    = Media.getImArray(
                    Region.number_to_block_name(self.data[row, col]))
            self.surface = Media.array2Surface(self.image)
            # print("rendering time: {:.2f}ms".format((time.time()-_t0)*1000))
        return self.surface

    def change_block(self, place: Coord, target_block: int):
        "在保持地图大致不变的情况下，对其进行一些更改"
        self.data[place.as_tuple()] = target_block
        if not self.rendered:
            self.render()
            return
        self.image[place.row*32:place.row*32+32,
                   place.col*32:place.col*32+32, :] = Media.getImArray('floor')
        self.surface = Media.array2Surface(self.image)

    def derender(self, center_region_index: tuple):
        "给定核心的位置，判断是否需要释放自己的内存，并执行。"
        if max(abs(self.index[0]-center_region_index[0]), abs(self.index[1]-center_region_index[1])) <= 3:
            return
        if not self.rendered and self.image is None and self.surface is None:
            return
        print("derendered: ", self.index)
        self.rendered = False
        del self.image
        self.image = None
        del self.surface
        self.surface = None


class Map:
    def __init__(self, seed=None, filename=None):
        self.regions = {}
        if seed is None:
            self.seed = np.random.randint(0, 1048576)
        else:
            self.seed = seed
        if filename is None:
            now = time.localtime()
            self.filename = f"Map_seed{self.seed}_time{now.tm_year:04d}{now.tm_mon:02d}{now.tm_mday:02d}_0.map.dat"
            i = 0
            while path.exists(self.filename):
                i += 1
                self.filename = f"Map_seed{self.seed}_time{now.tm_year:04d}{now.tm_mon:02d}{now.tm_mday:02d}_{i}.map.dat"
        else:
            self.filename = filename

    def generateRegion(self, region_index: tuple):
        out = Region(region_index).datum_from_seed(self.seed)
        self.regions[region_index] = out
        if region_index == (0, 0):
            out.data[0:2, 0:2] = 0
        return out

    def to_file(self):
        stream = ByteStream()
        stream.push(self.seed.to_bytes(4, 'little', signed=False))
        for region in self.regions.values():
            region.to_stream(stream)
        stream.to_file(self.filename)

    @classmethod
    def from_file(cls, filename: str):
        stream = ByteStream.from_file(filename)
        seed = int.from_bytes(stream.get(4), 'little', signed=False)
        s = Map(seed, filename)
        while stream:
            region = Region.from_stream(stream)
            s.regions[region.index] = region
        return s

    def at(self, place: Coord):
        try:
            region = self.regions[place.get_region_index()]
        except KeyError:
            region = self.generateRegion(place.get_region_index())
        return region.data[round(place.row) % 64, round(place.col) % 64]


class MapDisplay:
    def __init__(self, the_map: Map, root):
        self.the_map = the_map
        self.root = root

    def render_regions(self, screen_x0, screen_y0):
        "找到需要渲染的几个区域，把它们渲染；并把不需要的部分剔除。返回需要显示的区域。"
        region_index_xys = {(0, 0),
                            (SCREEN_SIZE[0], 0),
                            (0, SCREEN_SIZE[1]),
                            SCREEN_SIZE}  # corners of the screen
        region_index = {Coord.fromXY(*xy, x0=screen_x0, y0=screen_y0).get_region_index()
                        for xy in region_index_xys}

        center_region = Coord.fromXY(
            *CENTER_COORD, x0=screen_x0, y0=screen_y0).get_region_index()
        for r in self.the_map.regions.values():
            r.derender(center_region)
        # print("\rregion indexes:", region_index, end='')
        for i in region_index:
            if i in self.the_map.regions:
                self.the_map.regions[i].render()
            else:
                self.the_map.generateRegion(i).render()
        return region_index

    def event_dealer(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                print('File Saved!')
                self.the_map.to_file()

    def show(self, x0, y0):
        for i in self.render_regions(x0, y0):
            self.root.blit(
                self.the_map.regions[i].surface,
                # bl corner 2 tl corner: row+=1 when showing
                Coord((i[0]+1)*64-1, i[1]*64).toXY(x0=x0, y0=y0))



class H_Creature:
    NONE = 0
    USING = 1
    BREAKING = 2
    KILLING = 3
    TRADING = 4

    def __init__(self, place: Coord, root: pygame.Surface, the_map: Map) -> None:
        self.place = place
        self.root = root
        self.surface = Media.getImSurface('h_creature')
        self.the_map = the_map
        self.move_helper = MoveHelper(self)
        self.using = None
        self.usetype = 0

    def stationary_destination(self):
        "按照现有速度走下去会停止在什么地方"
        # 滑行0.5s后停止
        return self.place+self.velocity*(SLIDE_DURATION/2)

    def todo_func(self):
        self.move_helper.todo_func()
        pass

    def event_dealer(self, event):
        self.move_helper.event_dealer(event)
        pass

    def show(self, x0, y0):
        self.root.blit(self.surface, self.place.toXY(x0=x0, y0=y0))


class MoveHelper:
    def __init__(self, target: H_Creature) -> None:
        self.target = target
        self.moving = False
        self.velocity = Coord(0.0, 0.0)
        # left, up, down, right
        self.accelerating = [False, False, False, False]
        pass

    def todo_func(self):
        vm = 8
        dv = vm/SLIDE_DURATION/FPS

        seq = pygame.key.get_pressed()
        self.accelerating[0] = seq[pygame.K_a]
        self.accelerating[1] = seq[pygame.K_w]
        self.accelerating[2] = seq[pygame.K_s]
        self.accelerating[3] = seq[pygame.K_d]
        self.moving = any(self.accelerating)

        if self.moving:
            if self.accelerating[0] and not self.accelerating[3]:
                self.velocity.col -= dv
                if self.velocity.col < -vm:
                    self.velocity.col = -vm
            elif self.accelerating[3] and not self.accelerating[0]:
                self.velocity.col += dv
                if self.velocity.col > vm:
                    self.velocity.col = vm
            if self.accelerating[1] and not self.accelerating[2]:
                self.velocity.row += dv
                if self.velocity.row > vm:
                    self.velocity.row = vm
            elif self.accelerating[2] and not self.accelerating[1]:
                self.velocity.row -= dv
                if self.velocity.row < -vm:
                    self.velocity.row = -vm
        else:
            if self.velocity.row > dv:
                self.velocity.row -= dv
            elif self.velocity.row < -dv:
                self.velocity.row += dv
            else:
                self.velocity.row = 0
            if self.velocity.col > dv:
                self.velocity.col -= dv
            elif self.velocity.col < -dv:
                self.velocity.col += dv
            else:
                self.velocity.col = 0

        self.target.place += self.velocity*(1/FPS)
        # collision detect
        if self.target.the_map.at(self.target.place+Coord(1, -0.15)) & 1\
                or self.target.the_map.at(self.target.place+Coord(1, 0.15)) & 1:
            if round(self.target.place.row)+1-self.target.place.row < 0.85:
                self.target.place.row = round(self.target.place.row)+0.15
                if self.velocity.row > 0:
                    self.velocity.row *= -BOUNCING_COEF
        if self.target.the_map.at(self.target.place+Coord(-1, -0.15)) & 1\
                or self.target.the_map.at(self.target.place+Coord(-1, 0.15)) & 1:
            if self.target.place.row+1-round(self.target.place.row) < 0.85:
                self.target.place.row = round(self.target.place.row)-0.15
                if self.velocity.row < 0:
                    self.velocity.row *= -BOUNCING_COEF
        if self.target.the_map.at(self.target.place+Coord(-0.15, 1)) & 1\
                or self.target.the_map.at(self.target.place+Coord(0.15, 1)) & 1:
            if round(self.target.place.col)+1-self.target.place.col < 0.85:
                self.target.place.col = round(self.target.place.col)+0.15
                if self.velocity.col > 0:
                    self.velocity.col *= -BOUNCING_COEF
        if self.target.the_map.at(self.target.place+Coord(-0.15, -1)) & 1\
                or self.target.the_map.at(self.target.place+Coord(0.15, -1)) & 1:
            if self.target.place.col+1-round(self.target.place.col) < 0.85:
                self.target.place.col = round(self.target.place.col)-0.15
                if self.velocity.col < 0:
                    self.velocity.col *= -BOUNCING_COEF

    def event_dealer(self, event):
        pass


class Main:
    def __init__(self, source_file=None, default_seed=None):
        self.root = pygame.display.set_mode(SCREEN_SIZE)
        if source_file is None:
            self.map = Map(seed=default_seed)
        else:
            self.map = Map.from_file(source_file)
        self.mapDisplay = MapDisplay(self.map, self.root)
        self.clock = pygame.time.Clock()
        self.xy0 = CENTER_COORD  # x0, y0, where (0,0) lies
        self.h_creature = H_Creature(Coord(0, 0), self.root, self.map)
        self.todo_funcs = [self.todo_func, self.h_creature.todo_func]
        self.event_dealers = [
            self.h_creature.event_dealer, self.mapDisplay.event_dealer]
        print('Main Ready')

    def todo_func(self):
        source_coord = Coord.fromXY(
            CENTER_COORD[0], CENTER_COORD[1],
            x0=self.xy0[0], y0=self.xy0[1])
        target_coord = self.h_creature.place
        beta = 1.5/FPS
        delta = target_coord-source_coord
        self.xy0 = (-Coord(source_coord.row+delta.row*beta,
                           source_coord.col+delta.col*beta)).toXY(
            x0=CENTER_COORD[0], y0=CENTER_COORD[1])  # which x0,y0 can move c0,c1 to target place?

    def mainloop(self):
        t_old = time.time()
        while True:
            t0 = time.time()
            self.clock.tick(FPS)
            for func in self.todo_funcs:
                func()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                for func in self.event_dealers:
                    func(event)
            Media.show_background(self.root)
            self.mapDisplay.show(self.xy0[0], self.xy0[1])
            self.h_creature.show(self.xy0[0], self.xy0[1])
            pygame.display.update()
            if time.time()-t_old > 0.1:
                print("\rFPS: {:.1f}Hz; Coord: ({:.2f},{:.2f})".format(
                    1/(time.time()-t0), self.h_creature.place.row, self.h_creature.place.col), end='')
                t_old = time.time()
            t0 = time.time()


if __name__ == "__main__":
    Main().mainloop()

"""
这是什么？
这是一个2D迷宫游戏引擎的部分代码。（该游戏已经放弃维护）

已经实现的功能：
- 地图的无缝生成与加载存储
- 基本的角色移动与碰撞检测
- 地图区块的动态渲染与内存管理

开发日志(versions.txt)：

V0.1

地图的生成、存储和显示。
正方形迷宫，每个格子具有一个唯一的id（0到255），其最后一位决定了这个方块是否能够穿过。0可以，1不行。
游戏分区块渲染，一个区块大小为64*64，每个方块的像素大小是32*32，这样一个区块会占据16MB的内存。每个区块默认情况下由种子完全确定，如果被更改，就会生成一个存储文件专门记录这个区块的内容。

class ByteStream
class Coord

class Media
property dict media
method get_background

class Main
property todo_funcs
property event_dealers
property object_showers
method quit
method mainloop

class Region
property np.ndarray[uint8](64*64) data
property np.ndarray[uint8](2048*2048*4) image
property rendered
method fromSeed(int seed, tuple region)
method fromStream(ByteStream bytestream)
method toStream(ByteStream bytestream)
method render(Media media) //render or de-render if possible
method changeBlock(coord place, int targetblock)

class Map
property dict regions
method generateRegion(coord place)
method fromFile(str filename)
method toFile(str filename)

class MapDisplay
property pygame.Surface root
property Map map
method render_regions(coord center, coord screenSize)
method show(list[tuple] required_regions, coord offsets)


V0.2

加入角色“H_creature”。
角色的位置在静止情况下是整数，但是原则上可以是任何小数。角色可以尝试向任何方向移动，如果停止尝试，会回退并静止到距离最近的、可以落脚的整数格点上。
视角跟着角色一起移动，但是为了保证丝滑的游戏体验，二者并不同步。

class H_creature
property coord place
property coord velocity
property pygame.Surface root
property Map map
property MoveHelper move_helper
property pointing_direction
property using
property usetype(Using/Breaking/Killing/Trading)
method coord stationary_destination // next stationary destination
method todo_func
method event_dealer
method show

class MoveHelper
property target
property bool moving
property bool[4] accelerating
method todo_func // accelerating, moving according to velocity, and return to integer points after moving
method start_move(direction)
method stop_move(direction)

V 0.3 

加入了界面

class Button
property Rect rect
property str text
property color fg_color
property color bg_color
property func
method in_self(tuple cursor_pos)
method event_dealer
method show
method act

class InputBar
property Rect rect
property str text
property color fg_color
property color bg_color
property bool active
property snip_keys
method in_self(tuple cursor_pos)
method event_dealer
method show
method act

class GraphicInterFace
property main
property todo_funcs
property event_dealers
property object_showers
method show
method event_dealer
method to_do_func
method quit

class Prompt(GraphicInterFace)
property Rect rect (default)
property str text
property color fg_color 
property color bg_color 
method in_self(tuple cursor_pos)
method event_dealer
method show
method act

class UI(GraphicInterFace)
property hp_icon
property hp_bar
property armor_icon
property armor_bar
"""

