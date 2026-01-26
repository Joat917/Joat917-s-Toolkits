from PIL import Image as Im, ImageDraw as Imd, ImageFont as Imf
from random import randint
import os, sys
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "shutup"
import pygame as pg

WIDTH = 960
HEIGHT = 480
FPS = 30
TPS = 300
TPS_over_FPS = TPS // FPS
FIREWORK_ACCELERATION = 1
FIREWORK_GAP = 5 * TPS_over_FPS

IMAGE_ROOT = os.path.abspath('../../assets/numguess/')
WORKING_DIR = os.path.join(os.environ['APPDATA'], 'PyScriptX', 'MyToolkits') # from settings.py

try:
    bkg = Im.open(os.path.join(WORKING_DIR, 'img', 'bg_image_horizontal.png')).resize((WIDTH, HEIGHT)).convert("RGBA")
except Exception:
    bkg = Im.new("RGBA", (WIDTH, HEIGHT), color='#17375E')
bkg.paste(Im.new("RGBA", (WIDTH, HEIGHT), color=(0, 0, 0, 255)), (0, 0, WIDTH, HEIGHT), mask=Im.new('L', (WIDTH, HEIGHT), 100))
BACKGROUND = pg.image.frombuffer(bkg.tobytes(), (WIDTH, HEIGHT), "RGBA")

FIREWORK_IMG = [pg.transform.scale(pg.image.load(os.path.join(IMAGE_ROOT, f"Firework-{i}.png")), (10, 10)) for i in range(10)]
ICON = pg.image.load(os.path.join(IMAGE_ROOT, 'icon.png'))

FONT1 = Imf.truetype('arial.ttf', 30)
FONT2 = Imf.truetype('simkai.ttf', 30)


def Txt2Img(text: str, size=(0, 0), color=(255, 255, 255, 255)):
    texts = []
    tick = 0
    last = 0
    while tick < len(text):
        if text[tick] == "\n":
            texts.append(text[last:tick])
            last = tick+1
        tick += 1
    texts.append(text[last:])

    size = (30*max([len(t) for t in texts]), 25*len(texts))
    canavas = Im.new("RGBA", size)
    draw = Imd.Draw(canavas)
    for line in range(len(texts)):
        draw.text((0, 25*line), texts[line], color, FONT1)

    return pg.image.frombuffer(
        canavas.tobytes(), size, "RGBA")


class Attack:
    @staticmethod
    def fullarrange(*var):
        var = list(var)
        if len(var) <= 1:
            return var
        if len(var) == 2:
            if var[0] == var[1]:
                return [var]
            else:
                return [var, var[::-1]]
        else:
            out = []
            L = Attack.fullarrange(*var[1:])
            for i in L:
                for j in range(len(i)+1):
                    temp = i+[]
                    temp.insert(j, var[0])
                    out.append(temp)
            # no repeat
            output = []
            for i in out:
                if i not in output:
                    output.append(i)
            return output

    @staticmethod
    def output_to_text(out):
        if not out:
            return "No solution"
        t = 0
        L = 6
        output = ""
        out = list(out)
        while out[L*t: L*t+L]:
            output += "\t".join(out[L*t: L*t+L])
            output += "\n"
            t += 1
        return output

    def __init__(self, a, b, c, d):
        self.outputs = set()
        for i in "+-*/":
            for j in "+-*/":
                for k in "+-*/":
                    text = f"(%i%s%i)%s(%i%s%i)" % (a, i, b, j, c, k, d)
                    self.exam(text)
                    text = f"(%i%s%i)%s(%i%s%i)" % (a, i, c, j, b, k, d)
                    self.exam(text)
                    text = f"(%i%s%i)%s(%i%s%i)" % (a, i, d, j, b, k, c)
                    self.exam(text)
                    for p, q, r, s in Attack.fullarrange(a, b, c, d):
                        text = "((%i%s%i)%s%i)%s%i" % (p, i, q, j, r, k, s)
                        self.exam(text)
                        text = "(%i%s(%i%s%i))%s%i" % (p, i, q, j, r, k, s)
                        self.exam(text)
                        text = "%i%s((%i%s%i)%s%i)" % (p, i, q, j, r, k, s)
                        self.exam(text)
                        text = "%i%s(%i%s(%i%s%i))" % (p, i, q, j, r, k, s)
                        self.exam(text)

    def exam(self, text):
        try:
            if eval(text) == 24:
                self.outputs.add(text)
        except Exception as e:
            pass

    def __str__(self):
        return Attack.output_to_text(self.outputs)


class Button:
    buttons = []

    def __init__(self, maingame, x: int, y: int, func=lambda *args: None,
                 size=(100, 80), text="Button", textcolor=(255, 255, 255, 255),
                 backgroundcolor=(0, 0, 0, 127), funcargs=(), funckwargs={}) -> None:
        self.main = maingame
        self.x = x
        self.y = y
        self.func = func
        self.funcargs = funcargs
        self.funckwargs = funckwargs
        self.size = size
        Button.buttons.append(self)

        canavas = Im.new("RGBA", self.size, backgroundcolor)
        Imd.Draw(canavas).text((20, 20), text, textcolor, FONT1)
        self.cover = pg.image.frombuffer(canavas.tobytes(), self.size, 'RGBA')

    def dealevent(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                mousepos = pg.mouse.get_pos()
                if self.x <= mousepos[0] < self.x+self.size[0]\
                        and self.y <= mousepos[1] < self.y+self.size[1]:
                    self.func(*self.funcargs, **self.funckwargs)

    def show(self):
        self.main.window.blit(self.cover, (self.x, self.y))


class Textshow:
    texts = []

    def __init__(self, main, text: str, color=(255, 255, 255, 255), time=30):
        self.main = main
        self.text = text
        self.time = time
        self.size = (20 * len(self.text)+10, 30)
        self.image = Im.new('RGBA', self.size)
        imd = Imd.Draw(self.image)
        imd.text((0, 0), self.text, color, FONT1)
        self.cover = pg.image.frombuffer(
            self.image.tobytes(), self.size, 'RGBA')
        Textshow.texts.append(self)

    def tick(self, pos=(0, 0)):
        self.time -= 1
        if not self.time:
            Textshow.texts.remove(self)
            del self

    def show(self, pos=(0, 0)):
        self.main.window.blit(self.cover, pos)


class Dragger:
    draggers = []
    expression_dragger = None
    trashbin = None

    def __init__(self, maingame, x: int, y: int, text="Null", size=(100, 80),
                 textcolor=(255, 255, 255, 255), backgroundcolor=(0, 0, 0, 127), eraseable=True) -> None:
        Dragger.draggers.append(self)
        self.main = maingame
        self.x = x
        self.y = y
        self.text = str(text)
        self.size = size
        self.textcolor = textcolor
        self.backgroundcolor = backgroundcolor
        self.eraseable = eraseable
        self.fellow = None
        self.mousedown = False  # status: mouse down on me;
        self.mouseup = False  # status: mouse just up and wanna find pri-fellow dragger;
        self.mousepos_offset = None

        canavas = Im.new("RGBA", self.size, self.backgroundcolor)
        Imd.Draw(canavas).text((20, 30), self.text, self.textcolor, FONT1)
        self.cover = pg.image.frombuffer(canavas.tobytes(), self.size, "RGBA")

        self.outtext = " "+self.text+" "

    def copy(self):
        return Dragger(self.main, self.x+self.size[0]+60, self.y+self.size[1],
                       self.text, self.size, self.textcolor, self.backgroundcolor)

    def get_text(self):
        if self.fellow is self:
            self.fellow = None
        if self.fellow is None:
            return self.outtext
        else:
            return self.outtext+self.fellow.get_text()

    def dealevent(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                mousepos = pg.mouse.get_pos()
                if self.x <= mousepos[0] < self.x+self.size[0]\
                        and self.y <= mousepos[1] < self.y+self.size[1]:
                    self.mousedown = True
                    self.mousepos_offset = (
                        mousepos[0]-self.x, mousepos[1]-self.y)
        if event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                self.mousedown = False
                self.mousepos_offset = None
                mousepos = pg.mouse.get_pos()
                if self.x <= mousepos[0] < self.x+self.size[0]\
                        and self.y <= mousepos[1] < self.y+self.size[1]:
                    self.mouseup = True

    def tick(self):
        if self.mousedown:
            mousepos = pg.mouse.get_pos()
            self.x = mousepos[0]-self.mousepos_offset[0]
            self.y = mousepos[1]-self.mousepos_offset[1]
        if self.mouseup:
            radius = 60
            for dragger in Dragger.draggers:
                if dragger.fellow is None:
                    if abs(dragger.x+dragger.size[0]-self.x)+abs(dragger.y-self.y) < radius:
                        self.x = dragger.x+dragger.size[0]
                        self.y = dragger.y+0
                        dragger.fellow = self
            self.mouseup = False

        if self.eraseable and self.fellow is Dragger.trashbin:
            Dragger.draggers.remove(self)
            for dragger in Dragger.draggers:
                if dragger.fellow is self:
                    dragger.fellow = None
            return
        elif self is Dragger.trashbin:
            assert self in Dragger.draggers
            while self.fellow is not None and self.fellow.eraseable:
                Dragger.draggers.remove(self.fellow)
                self.fellow = self.fellow.fellow
            if self.fellow is self:
                self.fellow = None
        if self.fellow is not None:
            if abs(self.fellow.x - self.size[0] - self.x) > 40 or abs(self.fellow.y - self.y) > 40:
                self.fellow = None
            else:
                self.fellow.x = self.x+self.size[0]
                self.fellow.y = self.y+0

    def show(self):
        self.main.window.blit(self.cover, (self.x, self.y))

    # for sort
    def __lt__(self, other):
        pivot = self
        while pivot.fellow is not None:
            if pivot.fellow is other:
                return True
            if pivot.fellow is pivot:
                pivot.fellow = None
                break
            pivot = pivot.fellow
        return False

class TrashBin(Dragger):
    def __init__(self, maingame, textcolor=(255, 255, 255, 255), backgroundcolor=(255, 0, 0, 63)) -> None:
        super().__init__(maingame, 730, 20, "TrashBin", (160, 100), textcolor, backgroundcolor)
        Dragger.trashbin = self
        self.eraseable = False


class Game:
    def __init__(self, maingame, buttoninit=True) -> None:
        self.main = maingame
        self.numbers = [randint(1, 13) for i in range(4)]
        while not Attack(*self.numbers).outputs:
            self.numbers = [randint(1, 13) for i in range(4)]

        Dragger.expression_dragger = Dragger(self.main, 30, 350, ">>>", backgroundcolor=(127, 216, 30, 216), eraseable=False)
        for i in range(4):
            Dragger(self.main, 30+120*i, 20, str(self.numbers[i]), size=(80, 80),
                    backgroundcolor=(randint(127, 255), randint(127, 255),
                    randint(127, 255), 63), eraseable=False)
        
        self.button_colors = {
            '+': (randint(127, 255), randint(127, 255), randint(127, 255), 63),
            '-': (randint(127, 255), randint(127, 255), randint(127, 255), 63),
            '*': (randint(127, 255), randint(127, 255), randint(127, 255), 63),
            '/': (randint(127, 255), randint(127, 255), randint(127, 255), 63),
            '(': (randint(127, 255), randint(127, 255), randint(127, 255), 63),
            ')': (randint(127, 255), randint(127, 255), randint(127, 255), 63),
        }

        self.button_positions = {
            '+': (30, 120),
            '-': (110, 120),
            '*': (190, 120),
            '/': (270, 120),
            '(': (350, 120),
            ')': (430, 120),
        }

        if buttoninit:
            self.refresh_buttons()
            # Button(self.main, 30, 120, Dragger, size=(60, 80),
            #        funcargs=(self.main, 30, 220, "+"),
            #        funckwargs={"size": (60, 80), "backgroundcolor": (
            #            randint(127, 255), randint(127, 255), randint(127, 255), 63)},
            #        text="+", backgroundcolor=(randint(127, 255), randint(127, 255),
            #                                   randint(127, 255), 216))
            # Button(self.main, 110, 120, Dragger, size=(60, 80),
            #        funcargs=(self.main, 110, 220, "-"),
            #        funckwargs={"size": (60, 80), "backgroundcolor": (
            #            randint(127, 255), randint(127, 255), randint(127, 255), 63)},
            #        text="-", backgroundcolor=(randint(127, 255), randint(127, 255),
            #                                   randint(127, 255), 216))
            # Button(self.main, 190, 120, Dragger, size=(60, 80),
            #        funcargs=(self.main, 190, 220, "*"),
            #        funckwargs={"size": (60, 80), "backgroundcolor": (
            #            randint(127, 255), randint(127, 255), randint(127, 255), 63)},
            #        text="*", backgroundcolor=(randint(127, 255), randint(127, 255),
            #                                   randint(127, 255), 216))
            # Button(self.main, 270, 120, Dragger, size=(60, 80),
            #        funcargs=(self.main, 270, 220, "/"),
            #        funckwargs={"size": (60, 80), "backgroundcolor": (
            #            randint(127, 255), randint(127, 255), randint(127, 255), 63)},
            #        text="/", backgroundcolor=(randint(127, 255), randint(127, 255),
            #                                   randint(127, 255), 216))
            # Button(self.main, 350, 120, Dragger, size=(60, 80),
            #        funcargs=(self.main, 350, 220, "("),
            #        funckwargs={"size": (60, 80), "backgroundcolor": (
            #            randint(127, 255), randint(127, 255), randint(127, 255), 63)},
            #        text="(", backgroundcolor=(randint(127, 255), randint(127, 255),
            #                                   randint(127, 255), 216))
            # Button(self.main, 430, 120, Dragger, size=(60, 80),
            #        funcargs=(self.main, 430, 220, ")"),
            #        funckwargs={"size": (60, 80), "backgroundcolor": (
            #            randint(127, 255), randint(127, 255), randint(127, 255), 63)},
            #        text=")", backgroundcolor=(randint(127, 255), randint(127, 255),
            #                                   randint(127, 255), 216))
            Button(self.main, 750, 380, self.main.replay, (140, 90), "RePlay",
                   backgroundcolor=(randint(127, 255), randint(127, 255), randint(127, 255), 216))

    def refresh_buttons(self):
        button_dragger_exists = {
            '+': False,
            '-': False,
            '*': False,
            '/': False,
            '(': False,
            ')': False,
        }
        for dragger in Dragger.draggers:
            for symbol in button_dragger_exists:
                if dragger.text == symbol and (dragger.x, dragger.y) == self.button_positions[symbol]:
                    button_dragger_exists[symbol] = True
        for symbol in button_dragger_exists:
            if not button_dragger_exists[symbol]:
                Dragger(self.main, *self.button_positions[symbol], symbol,
                        size=(60, 80), backgroundcolor=self.button_colors[symbol], eraseable=True)
    
    def victory(self):
        "to tell whether victory"
        text = Dragger.expression_dragger.get_text()[5:]
        while text and text[0] == " ":
            text = text[1:]
        try:
            if eval(text) == 24:
                for i in self.numbers:
                    if str(i) not in text:
                        return False
                return True
            else:
                return False
        except Exception as e:
            return False


class Firework:
    def __init__(self, maingame) -> None:
        self.window = maingame.window
        self.game = maingame

        color = randint(0, 9)
        self.pictures = [pg.transform.scale(
            FIREWORK_IMG[color], (i, i)) for i in range(1, 11)]  # slice is its size+1
        self.x = WIDTH
        self.y = HEIGHT
        self.vx = randint(-20, -5)
        self.vy = randint(-30, -20)
        self.ay = FIREWORK_ACCELERATION

        self.time = randint(10, 20)

    def tick(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.ay

        self.time -= 1
        self.game.fireworks.append(FireTrace(self))
        if self.time < 0:
            self.game.fireworks.append(FireBlast(self, 7, 0))
            self.game.fireworks.append(FireBlast(self, -7, 0))
            self.game.fireworks.append(FireBlast(self, 0, 7))
            self.game.fireworks.append(FireBlast(self, 0, -7))
            self.game.fireworks.append(FireBlast(self, 5, 5))
            self.game.fireworks.append(FireBlast(self, -5, 5))
            self.game.fireworks.append(FireBlast(self, -5, -5))
            self.game.fireworks.append(FireBlast(self, 5, -5))
            self.game.fireworks.remove(self)

    def show(self):
        self.window.blit(self.pictures[-1], (self.x, self.y))


class FireTrace:
    def __init__(self, firework: Firework):
        self.firework = firework
        self.x = firework.x+0
        self.y = firework.y+0
        self.time = 8

    def tick(self):
        self.time -= 1
        if self.time < 0:
            self.firework.game.fireworks.remove(self)

    def show(self):
        self.firework.window.blit(self.firework.pictures[self.time], (self.x, self.y))


class FireBlast:
    def __init__(self, firework: Firework, vx, vy) -> None:
        self.window = firework.window
        self.pictures = firework.pictures
        self.game = firework.game
        self.x = firework.x+0
        self.y = firework.y+0
        self.vx = vx
        self.vy = vy
        self.ay = FIREWORK_ACCELERATION

        self.time = 49

    def tick(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.ay

        self.time -= 1
        self.game.fireworks.append(FireTrace(self))
        if self.time < 0:
            self.game.fireworks.remove(self)

    def show(self):
        self.window.blit(self.pictures[self.time//5], (self.x, self.y))


class MainGame:
    def __init__(self) -> None:
        self.window = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption('Point 24 Game')
        pg.display.set_icon(ICON)
        self.clock = pg.time.Clock()
        self.game = Game(self)
        TrashBin(self)
        self.fireworks = []
        pass

    def mainloop(self):
        while True:
            self.window.blit(BACKGROUND, (0, 0))

            for _ in range(TPS_over_FPS):
                self.clock.tick(TPS)
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        self.quit()
                    elif event.type == pg.MOUSEBUTTONDOWN:
                        # print(pg.mouse.get_pos())
                        pass
                    elif event.type == pg.MOUSEBUTTONUP:
                        self.game.refresh_buttons()
                    for dragger in Dragger.draggers:
                        dragger.dealevent(event)
                    Dragger.trashbin.dealevent(event)
                    for button in Button.buttons:
                        button.dealevent(event)

                
                Dragger.draggers.sort()

                if self.game.victory():
                    self.victory()

                for dragger in Dragger.draggers:
                    dragger.tick()
                for text in Textshow.texts:
                    text.tick()
                    
            
            for button in Button.buttons:
                button.show()
            for dragger in Dragger.draggers:
                dragger.show()
            for text in Textshow.texts:
                text.show()
            for firework in self.fireworks:
                firework.tick()
                firework.show()

            pg.display.update()

    def quit(self):
        pg.quit()
        sys.exit(0)

    def victory(self):
        if not randint(0, FIREWORK_GAP):
            self.fireworks.append(Firework(self))
        pass

    def replay(self):
        Dragger.draggers = [Dragger.trashbin]
        self.game = Game(self, buttoninit=False)


if __name__ == "__main__":
    MainGame().mainloop()
