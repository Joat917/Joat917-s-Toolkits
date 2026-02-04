from BaseImport import *
from Menu import PureText, Button, Text, Row, ScrollWindow, InputBox
from ErrorNotice import *
from Game import Main as Game
from Maze import Maze
from ShowMaze import Main as ShowMaze
from MazeGenerate import generate
from HelpPage import helppage as _helppage
import os
import re

PREVIEW_PHOTOS = [
    (Im.open(MediaPath/'screenshot1.png').convert('RGBA')),
    (Im.open(MediaPath/'screenshot2.png').convert('RGBA'))
]
BGD_ORIGIN = Im.open(MediaPath/'3756101.jpg').convert('RGBA')
BGD = im2pg(BGD_ORIGIN.resize((SCREEN_SIZE[0], round(
    SCREEN_SIZE[0]*BGD_ORIGIN.height/BGD_ORIGIN.width))).crop((0, 0, *SCREEN_SIZE)))

GRAND_TITLE = Im.open(MediaPath/'GrandTitle.png').convert('RGBA')

for pic in PREVIEW_PHOTOS:
    pic.paste((0, 0, 0, 0), (0, 0, *pic.size), Im.new('L', pic.size, 128))


def init():
    global window, clock
    window = display_init()
    clock = pg.time.Clock()
    loading()


def loading():
    window.blit(im2pg(Im.new('RGBA', SCREEN_SIZE, (0, 0, 0, 128))), (0, 0))
    Text((SCREEN_SIZE[0]//2-100, SCREEN_SIZE[1]//2-50), (200, 100), PureText("Loading...", (255,)*4,
         font=Imf.truetype('arial.ttf', 32))).show(window, (SCREEN_SIZE[0]//2-100, SCREEN_SIZE[1]//2-50))
    pg.display.update()


def __get_mazes_list():
    "get the list of filenames of the mazes. return list[str]"
    filenames = os.listdir(SavePath.SAVE_ROOT)
    myre = re.compile(r'(?i).*?\.thirdmaze$')
    return [s for s in filenames if myre.match(s)]


def __getrow(index: int, name: str):
    "turn filenames into visualized rows. return Row"
    def enter_game():
        try:
            show_detail(name)
        except GameExit:
            return
    return Row((0, 0), (900, 60), PREVIEW_PHOTOS[index % len(PREVIEW_PHOTOS)], [
        Button(None, (0, 0), (100, 60), (0, 0, 0, 0), str(index+1)),
        Text((100, 10), (500, 60), PureText(
            re.match(r'(?i)^(.+?)\.thirdmaze$', name).groups()[0],
             (255,)*4), Text.LEFT),
        Button(None, (750, 0), (150, 60), (163, 73, 164, 200), 'PLAY',
               callfunc=enter_game),
    ])


def __getrow_creation():
    "get rows for creation. return list[Row]"
    def _generate(size: int):
        try:
            loading()
            generate(size)
            Info_Notice("Generation Success!").mainloop()
            mainmenu()
        except Exception as e:
            print_exc()
            Error_Notice(f"{str(type(e))[8:-2]}:\n{e}").mainloop()
            return False
    return [
        Row((0, 0), (900, 60), PREVIEW_PHOTOS[0], [
            Button(None, (0, 0), (100, 60), (0, 0, 0, 0), "+"),
            Text((100, 10), (500, 60), PureText(
                "Generate a size-20 maze", (255,)*4), Text.LEFT),
            Button(None, (750, 0), (150, 60), (255, 201, 14, 200), 'CREATE',
                   callfunc=_generate, args=(20,)),
            Button(None, (600, 0), (150, 60), (255, 127, 39, 200), 'Advanced',
                   callfunc=__genadvanced, args=(20,))]),
        Row((0, 0), (900, 60), PREVIEW_PHOTOS[0], [
            Button(None, (0, 0), (100, 60), (0, 0, 0, 0), "+"),
            Text((100, 10), (500, 60), PureText(
                "Generate a size-35 maze", (255,)*4), Text.LEFT),
            Button(None, (750, 0), (150, 60), (255, 201, 14, 200), 'CREATE',
                   callfunc=_generate, args=(35,)),
            Button(None, (600, 0), (150, 60), (255, 127, 39, 200), 'Advanced',
                   callfunc=__genadvanced, args=(35,))]),
        Row((0, 0), (900, 60), PREVIEW_PHOTOS[0], [
            Button(None, (0, 0), (100, 60), (0, 0, 0, 0), "+"),
            Text((100, 10), (500, 60), PureText(
                "Generate a size-50 maze", (255,)*4), Text.LEFT),
            Button(None, (750, 0), (150, 60), (255, 201, 14, 200), 'CREATE',
                   callfunc=_generate, args=(50,)),
            Button(None, (600, 0), (150, 60), (255, 127, 39, 200), 'Advanced',
                   callfunc=__genadvanced, args=(50,))]),
        Row((0, 0), (900, 60), PREVIEW_PHOTOS[0], [
            Button(None, (0, 0), (100, 60), (0, 0, 0, 0), "+"),
            Text((100, 10), (500, 60), PureText(
                "Generate a size-100 maze", (255,)*4), Text.LEFT),
            Button(None, (750, 0), (150, 60), (255, 201, 14, 200), 'CREATE',
                   callfunc=_generate, args=(100,)),
            Button(None, (600, 0), (150, 60), (255, 127, 39, 200), 'Advanced',
                   callfunc=__genadvanced, args=(100,))]),
        Row((0, 0), (900, 60), PREVIEW_PHOTOS[0], [
            Button(None, (0, 0), (100, 60), (0, 0, 0, 0), "+"),
            Text((100, 10), (500, 60), PureText(
                "Generate a size-200 maze", (255,)*4), Text.LEFT),
            Button(None, (750, 0), (150, 60), (255, 201, 14, 200), 'CREATE',
                   callfunc=_generate, args=(200,)),
            Button(None, (600, 0), (150, 60), (255, 127, 39, 200), 'Advanced',
                   callfunc=__genadvanced, args=(200,))])
    ]


class __genadvanced:
    def __init__(self, size: int):
        "called to make a new page to choose the seed for the maze"
        loading()
        self.size = size
        self.seed = randint(0, (1 << 32)-1)
        self.sc = ScrollWindow((10, 10), (920, SCREEN_SIZE[1]-5), [
            Row((0, 0), (900, 60), (0, 0, 0, 0), [
                Text((0, 0), (900, 60), PureText("Advanced Maze Map Generator", (255,)*4))]),
            Row((0, 0), (900, 60), (0, 0, 0, 0), [Button(None, (300, 0), (300, 60), (255, 201, 14, 200), "CREATE", callfunc=self._generate),
                                                  Button(None, (0, 0), (300, 60), (127, 127, 127, 200), "BACK", callfunc=self._quit),]),
            Row((0, 0), (900, 60), (0, 0, 0, 0), [Text((0, 0), (300, 60), PureText("Size:", (255,)*4), Text.LEFT),
                Button(None, (600, 0), (300, 60), (127, 127, 127, 100), str(size), callfunc=self._changesize)]),
            Row((0, 0), (900, 60), (0, 0, 0, 0), [Text((0, 0), (300, 60), PureText("Seed:", (255,)*4), Text.LEFT),
                InputBox((300, 0), (600, 60), f"Default Seed:{self.seed}", self._generate)]),
        ], (222, 174, 201, 100))
        # Row2 button text need changing

        try:
            while True:
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        raise GameExit
                    if self.sc.handleEvent(event):
                        continue
                    if event.type == pg.KEYDOWN:
                        if event.key == pg.K_ESCAPE:
                            raise GameExit

                window.blit(BGD, (0, 0))
                self.sc.show(window)
                pg.display.flip()
                clock.tick(FPS)
        except GameExit:
            del self
            return

    def _quit(self):
        raise GameExit

    def _changesize(self):
        self.size = {20: 35, 35: 50, 50: 100, 100: 200, 200: 20}[self.size]
        self.sc.rows[2].objects[1].__init__(self.sc.rows[2].objects[1].window, (600, 0), (
            300, 60), (127, 127, 127, 100), str(self.size), callfunc=self._changesize)
        self.sc.rows[2].objects[1].row = self.sc.rows[2]
        self.sc.rows[2].objects[1].sw = self.sc

    def _generate(self):
        if self.sc.rows[3].objects[1].result != "":
            try:
                self.seed = int(eval(self.sc.rows[3].objects[1].get_result()))
                if self.seed < -(1 << 32) or self.seed >= (1 << 32):
                    raise ValueError(f"Seed {self.seed} too large! ")
            except Exception as exc:
                print_exc()
                Error_Notice(f"{str(type(exc))[8:-2]}:\n{exc}").mainloop()
                self.sc.rows[3].objects[1].result = ""
                self.sc.rows[3].objects[1].tick = 0
                return
        generate(self.size, self.seed,
                 f"Maze_size{self.size}_seed{self.seed}.thirdmaze")
        Info_Notice("Generation Success!").mainloop()

        mainmenu()


def getscrollwindow(pos: tuple):
    mazes_list = __get_mazes_list()
    rows = [__getrow(i, mazes_list[i])
            for i in range(len(mazes_list))]+__getrow_creation()
    return ScrollWindow(pos, (920, SCREEN_SIZE[1]-5), rows, (222, 174, 201, 100))


def __get_detail(filename: str, width=round(SCREEN_SIZE[0]*0.618),
                 zoom=15, imsize=(round(SCREEN_SIZE[0]*0.3), round(SCREEN_SIZE[1]*0.618))):
    "return: ScrollWindow, PreviewPicture"
    maze = Maze(SavePath/filename)
    size = maze.size
    more_info = maze.more_info

    rows = []
    font = Imf.truetype('arial.ttf', 48)

    if len(more_info):
        _tick = 0

        def getint(n: int, _tick):
            out = more_info[_tick:_tick+n]
            _tick += n
            return int(out.hex(), 16), _tick

        role_health, _tick = getint(1, _tick)
        role_armor, _tick = getint(1, _tick)

        _tick += 10
        role_death, _tick = getint(4, _tick)
        role_gaming_time, _tick = getint(4, _tick)

        enemy_num, _tick = getint(2, _tick)
        _tick += 18*enemy_num+2

        rows.append(Row((0, 0), (width, 70), (0,)*4, [
            Text((0, 0), (width-10, 60), PureText(
                "Info: ", (255,)*4, font=font), align=Text.LEFT)]))
        rows.append(Row((0, 0), (width, 70), (0,)*4, [
            Text((0, 0), (width-10, 60), PureText(
                f"Size: {size}*{size}", (255,)*4, font=font), align=Text.LEFT)]))
        rows.append(Row((0, 0), (width, 70), (0,)*4, [
            Text((0, 0), (width-10, 60), PureText(
                f"Filename: {filename}", (255,)*4, font=font), align=Text.LEFT)]))
        rows.append(Row((0, 0), (width, 70), (0,)*4, [
            Text((0, 0), (width-10, 60), PureText(
                f"Health: {role_health}", (241, 75, 84), font=font), align=Text.LEFT)]))
        rows.append(Row((0, 0), (width, 70), (0,)*4, [
            Text((0, 0), (width-10, 60), PureText(
                f"Armor: {role_armor}", (195,)*3, font=font), align=Text.LEFT)]))
        rows.append(Row((0, 0), (width, 70), (0,)*4, [
            Text((0, 0), (width-10, 60), PureText(
                f"Deaths: {role_death}", (136, 0, 21), font=font), align=Text.LEFT)]))
        rows.append(Row((0, 0), (width, 70), (0,)*4, [
            Text((0, 0), (width-10, 60), PureText(
                f"GamingTime: {role_gaming_time}", (55, 216, 100), font=font), align=Text.LEFT)]))
        rows.append(Row((0, 0), (width, 70), (0,)*4, [
            Text((0, 0), (width-10, 60), PureText(
                f"EnemyLeft: {enemy_num}", (255, 20, 20), font=font), align=Text.LEFT)]))
    else:
        rows.append(Row((0, 0), (width, 70), (0,)*4, [
            Text((0, 0), (width-10, 60), PureText(
                f"Size: {size}*{size}", (255,)*4, font=font), align=Text.LEFT)]))
        rows.append(Row((0, 0), (width, 70), (0,)*4, [
            Text((0, 0), (width-10, 60), PureText(
                "No more info available.", (255,)*4, font=font), align=Text.LEFT)]))

    # 找到主角
    for _point in maze:
        if maze.visit(*_point) == 2:
            start = _point
            break
    else:
        start = (0, 0, 0)

    temp_image = maze.show(zoom)
    im_focus = maze.map2xy(*start, zoom)
    croppos = im_focus[0]-imsize[0]//2, im_focus[1]-imsize[1]//2
    temp_image = temp_image.crop(
        (*croppos, croppos[0]+imsize[0], croppos[1]+imsize[1]))
    out_image = BACKGROUND.resize(imsize)
    out_image.paste(temp_image, (0, 0), temp_image.getchannel('A'))

    return ScrollWindow((10, 10), (width+10, SCREEN_SIZE[1]-20), rows, (255, 174, 201, 200)), im2pg(out_image)


def show_detail(filename: str):
    def back(): raise GameExit
    def play(): Game(filename, window, raiseerror=True).mainloop()
    def preview(): ShowMaze(filename, window, True).mainloop()

    loading()

    sc0, sf1 = __get_detail(filename)
    buttons = []
    buttons.append(Button(window, (round(SCREEN_SIZE[0]*0.66), round(SCREEN_SIZE[1]*0.66)),
                          (round(SCREEN_SIZE[0]*0.15), round(SCREEN_SIZE[1]*0.15)), (127, 127, 127, 216), "Back", callfunc=back))
    buttons.append(Button(window, (round(SCREEN_SIZE[0]*0.82), round(SCREEN_SIZE[1]*0.66)),
                          (round(SCREEN_SIZE[0]*0.15), round(SCREEN_SIZE[1]*0.31)), (50, 216, 100, 216), "Start", callfunc=play))
    buttons.append(Button(window, (round(SCREEN_SIZE[0]*0.66), round(SCREEN_SIZE[1]*0.82)),
                          (round(SCREEN_SIZE[0]*0.15), round(SCREEN_SIZE[1]*0.15)), (163, 73, 164, 216), "Preview", callfunc=preview))
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                raise SystemExit
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    raise GameExit
            if sc0.handleEvent(event):
                continue
            for button in buttons[::-1]:
                if button.handleEvent(event):
                    break
        window.blit(BGD, (0, 0))
        window.blit(sf1, (round(SCREEN_SIZE[0]*0.66), 10))
        sc0.show(window, (10, 10))
        for button in buttons:
            button.show()
        pg.display.flip()
        clock.tick(FPS)


def helppage():
    try:
        _helppage(window, BGD)
    except GameExit:
        return


def mainmenu():
    pos = (0, 0)
    sw = getscrollwindow(pos)

    buttons = [Button(window, (SCREEN_SIZE[0]-150, 0), (150, 60), (128,)*4,
                      "Back", callfunc=lambda: exec("raise GameExit")),
               Button(window, (SCREEN_SIZE[0]-150, 80), (150, 60), (0, 255, 0, 128),
                      "Refresh", callfunc=lambda: [loading(), mainmenu()]),
               Button(window, (SCREEN_SIZE[0]-150, 160), (150, 60), (155, 0, 0, 128),
                      "Quit", callfunc=exit),
               Button(window, (SCREEN_SIZE[0]-150, 240), (150, 60), (128, 64, 255, 128),
                      "Help", callfunc=helppage)]

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                raise SystemExit
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    raise GameExit
            for button in buttons[::-1]+[sw]:
                if button.handleEvent(event):
                    break

        window.blit(BGD, (0, 0))
        sw.show(window, pos)
        for button in buttons:
            button.show()
        pg.display.flip()
        clock.tick(FPS)


def mainInterface():
    grandtitle_surface = im2pg(GRAND_TITLE)
    grandtitle_pos = ((SCREEN_SIZE[0]-GRAND_TITLE.size[0])//2, 50)

    bgd_surface = im2pg(BGD_ORIGIN)
    bgd_position_limit = (
        BGD_ORIGIN.size[0]-SCREEN_SIZE[0], BGD_ORIGIN.size[1]-SCREEN_SIZE[1])
    bgd_pos = [0, 0]
    bgd_velocity = [randint(4, 9), randint(4, 9)]

    text_pos = (100, SCREEN_SIZE[1]-200)
    text = Text(text_pos, (
        SCREEN_SIZE[0]-2*text_pos[0], 100), PureText(
        "Click Anywhere to start the game...", (255,)*4, font=Imf.truetype('arial.ttf', 36)))

    quitbutton = Button(window, (SCREEN_SIZE[0]-150, SCREEN_SIZE[1]-80), (150, 80),
                        (0, 0, 0, 0), "QUIT", (255, 128, 128, 255), exit)
    helpbutton = Button(window, (SCREEN_SIZE[0]-300, SCREEN_SIZE[1]-80), (150, 80),
                        (0, 0, 0, 0), "HELP", (128, 255, 128, 255), helppage)

    while True:
        for event in pg.event.get():
            if quitbutton.handleEvent(event) or helpbutton.handleEvent(event):
                continue
            if event.type == pg.QUIT:
                pg.quit()
                raise SystemExit
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    try:
                        loading()
                        mainmenu()
                    except GameExit:
                        pass
            elif event.type == pg.KEYDOWN:
                if event.key in [pg.K_ESCAPE, pg.K_q]:
                    pg.quit()
                    raise SystemExit
                if event.key == pg.K_RETURN:
                    try:
                        loading()
                        mainmenu()
                    except GameExit:
                        pass
        bgd_pos[0] += bgd_velocity[0]
        bgd_pos[1] += bgd_velocity[1]
        if bgd_pos[0] < 0:
            bgd_pos[0] = 0
            bgd_velocity[0] = randint(4, 9)
        elif bgd_pos[0] >= bgd_position_limit[0]:
            bgd_pos[0] = bgd_position_limit[0]-1
            bgd_velocity[0] = -randint(4, 9)
        if bgd_pos[1] < 0:
            bgd_pos[1] = 0
            bgd_velocity[1] = randint(4, 9)
        elif bgd_pos[1] >= bgd_position_limit[1]:
            bgd_pos[1] = bgd_position_limit[1]-1
            bgd_velocity[1] = -randint(4, 9)
        window.blit(bgd_surface, (-bgd_pos[0], -bgd_pos[1]))
        window.blit(grandtitle_surface, grandtitle_pos)
        quitbutton.show()
        helpbutton.show()
        text.show(window, text_pos)
        pg.display.flip()
        clock.tick(30)


def main():
    try:
        init()
        mainInterface()
    except SystemExit:
        return 0
    except Exception as exc:
        print_exc()
        Error_Notice(
            f"A fatal error occurred and the game broke down!\n{type(exc)}: \n{exc}", "Fatal Error!!!").mainloop()


if __name__ == "__main__":
    main()
