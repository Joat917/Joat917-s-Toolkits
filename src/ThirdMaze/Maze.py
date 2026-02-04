"""
六边形的迷宫！从cpp文件的生成结果中读取。
"""
from BaseImport import MediaPath
from PIL import Image as Im, ImageDraw as Imd
R = 0b100
TR = 0b110
TL = 0b010
L = 0b011
BL = 0b001
BR = 0b101
SQRT3 = 1.7320508075688772


class CanNotMove(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class Media:
    def __init__(self) -> None:
        self._floor = Im.open(MediaPath/"Floor1.png").convert('RGBA').rotate(90)
        self._floorHH = Im.open(MediaPath/"Floor3.png").convert('RGBA').rotate(90)
        self._floorH = Im.open(MediaPath/"Floor4.png").convert('RGBA').rotate(90)
        self._floorH2 = Im.open(MediaPath/"Floor5.png").convert('RGBA').rotate(90)
        self._floormask = Im.new('L', self._floor.size)
        for x in range(self._floor.size[0]):
            for y in range(self._floor.size[1]):
                if self._floor.getpixel((x, y))[3] >= 64:
                    self._floormask.putpixel((x, y), 255)

        self._floor_torch = Im.open(
            MediaPath/"Floor2.png").convert('RGBA').rotate(90)
        self._floor_landmine = Im.open(
            MediaPath/"Floor6.png").convert('RGBA').rotate(90)
        self._floor_barrier = Im.open(
            MediaPath/"Floor7.png").convert('RGBA').rotate(90)
        self._floor_portal = Im.open(
            MediaPath/"FloorP.png").convert('RGBA').rotate(90)
        self._floor_exit = Im.open(MediaPath/"Exit.png").convert('RGBA').rotate(90)

        self._zoom = 0
        self._buffer_floor = None
        self._buffer_floorHH = None
        self._buffer_floorH = None
        self._buffer_floorH2 = None
        self._buffer_floormask = None
        self._buffer_floor_torch = None
        self._buffer_floor_landmine = None
        self._buffer_floor_barrier = None
        self._buffer_floor_portal = None
        self._buffer_floor_exit = None

    def changezoom(self, zoom: int):
        self._zoom = zoom
        self._buffer_floor = None
        self._buffer_floorHH = None
        self._buffer_floorH = None
        self._buffer_floorH2 = None
        self._buffer_floormask = None
        self._buffer_floor_torch = None
        self._buffer_floor_landmine = None
        self._buffer_floor_barrier = None
        self._buffer_floor_portal = None
        self._buffer_floor_exit = None

    def floor(self, zoom: int):
        if zoom == self._zoom:
            if self._buffer_floor is not None:
                return self._buffer_floor
            else:
                out = self._floor.resize((zoom, round(zoom*SQRT3/2)))
                self._buffer_floor = out
                return out
        else:
            self.changezoom(zoom)
            out = self._floor.resize((zoom, round(zoom*SQRT3/2)))
            self._buffer_floor = out
            return out

    def floorHH(self, zoom: int):
        if zoom == self._zoom:
            if self._buffer_floorHH is not None:
                return self._buffer_floorHH
            else:
                out = self._floorHH.resize((zoom, round(zoom*SQRT3/2)))
                self._buffer_floorHH = out
                return out
        else:
            self.changezoom(zoom)
            out = self._floorHH.resize((zoom, round(zoom*SQRT3/2)))
            self._buffer_floorHH = out
            return out

    def floorH(self, zoom: int):
        if zoom == self._zoom:
            if self._buffer_floorH is not None:
                return self._buffer_floorH
            else:
                out = self._floorH.resize((zoom, round(zoom*SQRT3/2)))
                self._buffer_floorH = out
                return out
        else:
            self.changezoom(zoom)
            out = self._floorH.resize((zoom, round(zoom*SQRT3/2)))
            self._buffer_floorH = out
            return out

    def floorH2(self, zoom: int):
        if zoom == self._zoom:
            if self._buffer_floorH2 is not None:
                return self._buffer_floorH2
            else:
                out = self._floorH2.resize((zoom, round(zoom*SQRT3/2)))
                self._buffer_floorH2 = out
                return out
        else:
            self.changezoom(zoom)
            out = self._floorH2.resize((zoom, round(zoom*SQRT3/2)))
            self._buffer_floorH2 = out
            return out

    def floormask(self, zoom: int):
        if zoom == self._zoom:
            if self._buffer_floormask is not None:
                return self._buffer_floormask
            else:
                out = self._floormask.resize((zoom, round(zoom*SQRT3/2)))
                self._buffer_floormask = out
                return out
        else:
            self.changezoom(zoom)
            out = self._floormask.resize((zoom, round(zoom*SQRT3/2)))
            self._buffer_floormask = out
            return out

    def floor_torch(self, zoom: int):
        if zoom == self._zoom:
            if self._buffer_floor_torch is not None:
                return self._buffer_floor_torch
            else:
                out = self._floor_torch.resize((zoom, round(zoom*SQRT3/2)))
                self._buffer_floor_torch = out
                return out
        else:
            self.changezoom(zoom)
            out = self._floor_torch.resize((zoom, round(zoom*SQRT3/2)))
            self._buffer_floor_torch = out
            return out

    def floor_landmine(self, zoom: int):
        if zoom == self._zoom:
            if self._buffer_floor_landmine is not None:
                return self._buffer_floor_landmine
            else:
                out = self._floor_landmine.resize((zoom, round(zoom*SQRT3/2)))
                self._buffer_floor_landmine = out
                return out
        else:
            self.changezoom(zoom)
            out = self._floor_landmine.resize((zoom, round(zoom*SQRT3/2)))
            self._buffer_floor_landmine = out
            return out

    def floor_barrier(self, zoom: int):
        if zoom == self._zoom:
            if self._buffer_floor_barrier is not None:
                return self._buffer_floor_barrier
            else:
                out = self._floor_barrier.resize((zoom, round(zoom*SQRT3/2)))
                self._buffer_floor_barrier = out
                return out
        else:
            self.changezoom(zoom)
            out = self._floor_barrier.resize((zoom, round(zoom*SQRT3/2)))
            self._buffer_floor_barrier = out
            return out

    def floor_portal(self, zoom: int):
        if zoom == self._zoom:
            if self._buffer_floor_portal is not None:
                return self._buffer_floor_portal
            else:
                out = self._floor_portal.resize((zoom, round(zoom*SQRT3/2)))
                self._buffer_floor_portal = out
                return out
        else:
            self.changezoom(zoom)
            out = self._floor_portal.resize((zoom, round(zoom*SQRT3/2)))
            self._buffer_floor_portal = out
            return out

    def floor_exit(self, zoom: int):
        if zoom == self._zoom:
            if self._buffer_floor_exit is not None:
                return self._buffer_floor_exit
            else:
                out = self._floor_exit.resize((zoom, round(zoom*SQRT3/2)))
                self._buffer_floor_exit = out
                return out
        else:
            self.changezoom(zoom)
            out = self._floor_exit.resize((zoom, round(zoom*SQRT3/2)))
            self._buffer_floor_exit = out
            return out


class Maze:
    def __init__(self, fp: str) -> None:
        with open(fp, 'rb') as file:
            self.file_cont = file.read()
        self.size = int(self.file_cont[:4][::-1].hex(), 16)
        self.tick = 4
        self.media = Media()

        def getchar():
            out = self.file_cont[self.tick]
            self.tick += 1
            return out
        self.xylist = [[getchar() for j in range(self.size+1)]
                       for i in range(self.size+1)]
        self.yzlist = [[getchar() for j in range(self.size+1)]
                       for i in range(1, self.size+1)]
        self.zxlist = [[getchar() for j in range(1, self.size+1)]
                       for i in range(1, self.size+1)]

        # more infomation
        self.more_info = self.file_cont[self.tick:]
        del self.tick

        self._iterator_list_buffer = []
        for y in range(self.size+1):
            for x in range(self.size+1):
                self._iterator_list_buffer.append((x, y, 0))
        for z in range(1, self.size+1):
            for y in range(self.size+1):
                self._iterator_list_buffer.append((0, y, z))
        for x in range(1, self.size+1):
            for z in range(1, self.size+1):
                self._iterator_list_buffer.append((x, 0, z))

    def write(self, fp: str):
        out = b''
        out += self.size.to_bytes(4, 'little')
        for i in self.xylist:
            out += bytes(i)
        for i in self.yzlist:
            out += bytes(i)
        for i in self.zxlist:
            out += bytes(i)
        out += self.more_info
        with open(fp, 'wb') as file:
            file.write(out)

    def visit(self, x: int, y: int, z: int):
        # check size
        if (x > self.size or y > self.size or z > self.size):
            raise RuntimeError("Coordinate Error!--OverRange")
        # visit
        if (z == 0):
            return (self.xylist[y][x])
        elif (x == 0):
            return (self.yzlist[z - 1][y])
        elif (y == 0):
            return (self.zxlist[x - 1][z - 1])
        else:
            raise RuntimeError("Coordinate Error!--ALL NoneZero")

    def setpoint(self, x: int, y: int, z: int, value: int):
        if value < 0 or value >= 256:
            raise ValueError("Value %i not acceptable" % value)
        # check size
        if (x > self.size or y > self.size or z > self.size):
            raise RuntimeError("Coordinate Error!--OverRange")
        # visit
        if (z == 0):
            (self.xylist[y][x]) = value
            return value
        elif (x == 0):
            (self.yzlist[z - 1][y]) = value
            return value
        elif (y == 0):
            (self.zxlist[x - 1][z - 1]) = value
            return value
        else:
            raise RuntimeError("Coordinate Error!--ALL NoneZero")

    def neighbors(self, x: int, y: int, z: int):
        out = []
        for direction in range(1, 7):
            try:
                tx, ty, tz = self. move(direction, x, y, z)
                self.visit(tx, ty, tz)
                out.append((tx, ty, tz))
            except CanNotMove:
                pass
        return out

    def move(self, direction: int, x: int, y: int, z: int):
        if (direction & 0b100):
            x += 1
        if (direction & 0b010):
            y += 1
        if (direction & 0b001):
            z += 1
        if (x and y and z):
            x -= 1
            y -= 1
            z -= 1
        if (x > self.size or y > self.size or z > self.size):
            raise CanNotMove
        return x, y, z

    def map2xy(self, x: int, y: int, z: int, zoom: int, offsetx=0.0, offsety=0.0):
        x0, y0 = x-1/2*y-1/2*z, SQRT3/2*(y-z)
        x0 += self.size+0.5
        y0 += SQRT3/2*(self.size+0.5)
        x0 = x0*zoom+offsetx
        y0 = y0*zoom+offsety
        return round(x0), round(y0)

    def xy2map(self, x: int, y: int, zoom: int):
        x0, y0 = x/zoom, y/zoom
        y0 /= SQRT3/2
        x0 -= self.size+0.5
        y0 -= self.size+0.5
        # 此时x0=x-0.5y-0.5z, y0=y-z, 不妨假设x=0
        yt = -x0+y0/2
        zt = -x0-y0/2
        if round(zt) >= 0 and round(yt) >= 0:
            return 0, round(yt), round(zt)
        elif zt < yt:
            return round(-zt), round(yt-zt), 0
        else:
            return round(-yt), 0, round(zt-yt)

    def __iter__(self):
        "return iterator of all possible coordinates"
        return iter(self._iterator_list_buffer)

    def show(self, zoom: int, highlight=[], highlight2=[]):
        "highlight (list[tuple[3]]): use green to dye it and its neighbors; highlight2 (list[tuple[3]]): use purple to dye the points without their neighbors; return PIL.Image"
        self.image = Im.new("RGBA", (zoom*(2*self.size+1),
                                     round(zoom*SQRT3*(self.size+0.5))))
        hn = []
        for p in highlight:
            hn += self.neighbors(*p)

        for (x, y, z) in self:
            if self.visit(x, y, z) not in [0, 7, 10]:
                if (x, y, z) in highlight:
                    self.image.paste(
                        self.media.floorHH(zoom),
                        self.map2xy(x, y, z, zoom, -zoom /
                                    2, -SQRT3/4*zoom),
                        self.media.floormask(zoom))
                elif (x, y, z) in hn:
                    self.image.paste(
                        self.media.floorH(zoom),
                        self.map2xy(x, y, z, zoom, -zoom /
                                    2, -SQRT3/4*zoom),
                        self.media.floormask(zoom))
                elif (x, y, z) in highlight2:
                    self.image.paste(
                        self.media.floorH2(zoom),
                        self.map2xy(x, y, z, zoom, -zoom /
                                    2, -SQRT3/4*zoom),
                        self.media.floormask(zoom))
                else:
                    self.image.paste(
                        self.media.floor(zoom),
                        self.map2xy(x, y, z, zoom, -zoom /
                                    2, -SQRT3/4*zoom),
                        self.media.floormask(zoom))
            elif self.visit(x, y, z) == 7:
                self.image.paste(
                    self.media.floor_portal(zoom),
                    self.map2xy(x, y, z, zoom, -zoom /
                                2, -SQRT3/4*zoom),
                    self.media.floormask(zoom))
            elif self.visit(x, y, z) == 10:
                self.image.paste(
                    self.media.floor_exit(zoom),
                    self.map2xy(x, y, z, zoom, -zoom /
                                2, -SQRT3/4*zoom),
                    self.media.floormask(zoom))

        return self.image

    def show2(self, zoom: int, torches=[], landmines=[], barriers=[]):
        "torches (list[tuple[3]]);  landmines (list[tuple[3]]); return PIL.Image"
        self.image = Im.new("RGBA", (zoom*(2*self.size+1),
                                     round(zoom*SQRT3*(self.size+0.5))))

        for (x, y, z) in self:
            if self.visit(x, y, z) not in [0, 7, 10]:
                if (x, y, z) in torches:
                    self.image.paste(
                        self.media.floor_torch(zoom),
                        self.map2xy(x, y, z, zoom, -zoom /
                                    2, -SQRT3/4*zoom),
                        self.media.floormask(zoom))
                elif (x, y, z) in landmines:
                    self.image.paste(
                        self.media.floor_landmine(zoom),
                        self.map2xy(x, y, z, zoom, -zoom /
                                    2, -SQRT3/4*zoom),
                        self.media.floormask(zoom))
                elif (x, y, z) in barriers:
                    self.image.paste(
                        self.media.floor_barrier(zoom),
                        self.map2xy(x, y, z, zoom, -zoom /
                                    2, -SQRT3/4*zoom),
                        self.media.floormask(zoom))
                else:
                    self.image.paste(
                        self.media.floor(zoom),
                        self.map2xy(x, y, z, zoom, -zoom /
                                    2, -SQRT3/4*zoom),
                        self.media.floormask(zoom))
            elif self.visit(x, y, z) == 7:
                self.image.paste(
                    self.media.floor_portal(zoom),
                    self.map2xy(x, y, z, zoom, -zoom /
                                2, -SQRT3/4*zoom),
                    self.media.floormask(zoom))
            elif self.visit(x, y, z) == 10:
                self.image.paste(
                    self.media.floor_exit(zoom),
                    self.map2xy(x, y, z, zoom, -zoom /
                                2, -SQRT3/4*zoom),
                    self.media.floormask(zoom))
        return self.image

    @staticmethod
    def distance(point1: tuple, point2: tuple):
        x, y, z = point1[0]-point2[0], point1[1]-point2[1], point1[2]-point2[2]
        return max(x, y, z)-min(x, y, z)

    def astar(self, start: tuple, end: tuple) -> tuple:
        "找到从start到end的最短通路，返回（上一个点[这一个点]，长度）"
        # 初始化数据
        frontier = {0: [start]}
        frontier_size = 1
        came_from = {start: None}
        cost_so_far = {start: 0}

        # 我现在都不知道这个代码到底在干什么……
        while True:
            # print("frontier_size:", frontier_size)
            if end in cost_so_far:
                break
            if not frontier_size:
                raise RuntimeError("Cannot find a path!")

            if True:
                # 现在选择current作为扩张基地
                p = min(sorted(frontier))
                current = frontier[p][0]
                # print("current:", current)
                # 随便找到下一个点
                for next in self.neighbors(*current):
                    # 选中的目标不能是墙
                    if self.visit(*next) in [0, 4, 7]:
                        continue
                    # print("next:", next)
                    # 计算选中的目标已经走了多远
                    new_cost = cost_so_far[current]+1
                    # 如果目标没有被探索过 或者 已经被探索过但是这条路更短
                    if next not in cost_so_far \
                            or new_cost < cost_so_far[next]:
                        # 标记目标的探索结果
                        cost_so_far[next] = new_cost
                        # 计算从目标走向终点这条路径的预估总距离
                        priority = new_cost+self.distance(next, end)
                        # 把目标加入“前线”
                        if priority in frontier:
                            frontier[priority].append(next)
                            frontier_size += 1
                        else:
                            frontier[priority] = [next]
                            frontier_size += 1
                            # 标记目标的来源-扩张基地
                        came_from[next] = current
                # end for 扩张结束，基地拆除
                frontier[p].remove(current)
                if not frontier[p]:
                    frontier.pop(p)
                frontier_size -= 1

        return came_from, cost_so_far[end]+1


def main():
    pass


if __name__ == "__main__":
    main()
