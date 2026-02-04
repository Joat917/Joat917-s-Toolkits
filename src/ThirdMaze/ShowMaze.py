from BaseImport import *
import Maze


class Media:
    def __init__(self) -> None:
        self.background = Im.new(
            'RGBA', SCREEN_SIZE, (128, 0, 0, 255))
        self.backgroundcover = Media.im2pg(self.background)

    @staticmethod
    def im2pg(im: Im.Image, format='RGBA'):
        return pg.image.frombuffer(im.tobytes(), im.size, format)


class MotionControl:
    def __init__(self, main) -> None:
        self.main = main
        self.mousedown = False
        self.fixpoint = None
        self.keyspeed = {'up': 0, 'down': 0, 'left': 0, 'right': 0}
        self.direction = {'up': (0, -1), 'down': (0, 1),
                          'left': (-1, 0), 'right': (1, 0)}
        self.zoomspeed = {-1: 0, 1: 0}
        self.zoomwait = {-1: 0, 1: 0}
        self.chosenPoints = []
        pass

    def dealevent(self, event: pg.event.Event):
        if event.type == pg.MOUSEBUTTONDOWN:
            mouse_pos = pg.mouse.get_pos()
            if event.button in [3]:
                self.mousedown = True
                self.fixpoint = self.screen2map(*mouse_pos)
            elif event.button == 4:
                fixpoint = self.screen2map(*mouse_pos)
                self.main.zoom += 1
                self.main.refreshMaze()
                self.main.changing = True
                targetpoint = self.map2screen(*fixpoint)
                self.main.offset = (self.main.offset[0]+mouse_pos[0]-targetpoint[0],
                                    self.main.offset[1]+mouse_pos[1]-targetpoint[1])
            elif event.button == 5:
                if self.main.zoom > 1:
                    fixpoint = self.screen2map(*mouse_pos)
                    self.main.zoom -= 1
                    self.main.refreshMaze()
                    self.main.changing = True
                    targetpoint = self.map2screen(*fixpoint)
                    self.main.offset = (self.main.offset[0]+mouse_pos[0]-targetpoint[0],
                                        self.main.offset[1]+mouse_pos[1]-targetpoint[1])
        elif event.type == pg.MOUSEBUTTONUP:
            if event.button in [3]:
                self.mousedown = False
                self.fixpoint = None
            elif event.button == 1:
                # chose the point
                _pt = self.screen2map(*pg.mouse.get_pos())
                if _pt in self.chosenPoints:
                    print("R", _pt)
                    self.chosenPoints.remove(_pt)
                else:
                    try:
                        if self.main.maze.visit(*_pt) > 0:
                            self.chosenPoints.append(_pt)
                        print("C", _pt)
                    except RuntimeError:
                        pass
                self.main.refreshMaze()
                self.main.changing = True
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
                self.zoomspeed[-1] = 1
                self.zoomspeed[1] = 0
            elif event.key == pg.K_EQUALS:
                self.zoomspeed[1] = 1
                self.zoomspeed[-1] = 0
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
                self.zoomspeed[-1] = 0
                self.zoomwait[-1] = 0
            elif event.key == pg.K_EQUALS:
                self.zoomspeed[1] = 0
                self.zoomwait[1] = 0

    def show(self):
        if self.mousedown:
            mouse_pos = pg.mouse.get_pos()
            targetpoint = self.map2screen(*self.fixpoint)
            self.main.offset = (self.main.offset[0]+mouse_pos[0]-targetpoint[0],
                                self.main.offset[1]+mouse_pos[1]-targetpoint[1])
            self.main.changing = True
        for d in self.keyspeed:
            if self.keyspeed[d]:
                self.main.offset = (
                    self.main.offset[0]-self.direction[d][0]*self.keyspeed[d],
                    self.main.offset[1]-self.direction[d][1]*self.keyspeed[d])
                self.keyspeed[d] += 1

        for z in self.zoomspeed:
            if self.zoomspeed[z]:
                if self.zoomwait[z] <= 0:
                    fixpoint = self.screen2map(
                        SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2)

                    self.main.zoom += z
                    self.zoomspeed[z] += 1
                    if self.main.zoom < 1:
                        self.main.zoom = 1
                    # refresh
                    self.main.refreshMaze()
                    self.main.changing = True
                    targetpoint = self.map2screen(*fixpoint)
                    self.main.offset = (self.main.offset[0]+SCREEN_SIZE[0]//2-targetpoint[0],
                                        self.main.offset[1]+SCREEN_SIZE[1]//2-targetpoint[1])
                    self.zoomwait[z] = 0.3
                else:
                    self.zoomwait[z] -= 1/FPS*self.zoomspeed[z]

    def map2screen(self, x: int, y: int, z: int):
        x0, y0 = self.main.maze.map2xy(x, y, z, self.main.zoom)
        return x0+self.main.offset[0], y0+self.main.offset[1]

    def screen2map(self, x: int, y: int):
        x0, y0 = round((x-self.main.offset[0])),\
            round((y-self.main.offset[1]))
        return self.main.maze.xy2map(x0, y0, self.main.zoom)


class Main:
    def __init__(self, fp: str, window=None, raiseerror=False) -> None:
        self.media = Media()
        if window is None:
            pg.display.init()
            self.window = pg.display.set_mode(SCREEN_SIZE)
        else:
            self.window = window
        self.raiseerror = raiseerror
        self.maze = Maze.Maze(SavePath/fp)
        self.mazesize = self.maze.size

        self.clock = pg.time.Clock()
        self.mc = MotionControl(self)

        self.zoom = 20  # 放大倍数

        self.offset = (0, 0)  # 迷宫左上角落在屏幕的哪一部分
        _fxpt = self.mc.map2screen(0, 0, 0)
        _tget = SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2
        self.offset = (_tget[0]-_fxpt[0], _tget[1]-_fxpt[1])

        self.mazeimg = None
        self.mazecover = None
        self.refreshMaze()

        self.changing = True

    def refreshMaze(self):
        if len(self.mc.chosenPoints) >= 2:
            show_points = self.mc.chosenPoints[:-2]
            # init
            start_point = self.mc.chosenPoints[-2]
            end_point = self.mc.chosenPoints[-1]
            # show_points += [start_point, end_point]
            # find path
            try:
                path, length_path = self.maze.astar(start_point, end_point)
                _point = path[end_point]
                while _point != start_point:
                    show_points.append(_point)
                    _point = path[_point]
            except RuntimeError as exc:
                print(exc)
            pic = self.maze.show(
                self.zoom, [start_point, end_point], show_points)
        else:
            show_points = self.mc.chosenPoints
            pic = self.maze.show(self.zoom, show_points)
        self.mazeimg = pic
        # pic.show()
        self.mazecover = pg.image.frombuffer(
            pic.tobytes(), pic.size, 'RGBA')

    def mainloop(self):
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    if self.raiseerror:
                        raise GameExit
                    else:
                        pg.quit()
                        raise SystemExit
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_s:
                        self.mazeimg.save(SavePath/'SavedImg.png')
                    if event.key == pg.K_SPACE:
                        print(self.offset)
                    elif event.key in [pg.K_q, pg.K_ESCAPE]:
                        if self.raiseerror:
                            raise GameExit
                self.mc.dealevent(event)

            self.mc.show()

            self.window.blit(self.media.backgroundcover, (0, 0))
            self.window.blit(self.mazecover, self.offset)

            pg.display.update()
            self.changing = False
            self.clock.tick(FPS)


if __name__=="__main__":
    try:
        if len(argv) == 0:
            fp = input("filepath:")
            Main(fp).mainloop()
        else:
            Main(argv[1]).mainloop()
    except Exception as e:
        print(f"{type(e)}:{e}")
