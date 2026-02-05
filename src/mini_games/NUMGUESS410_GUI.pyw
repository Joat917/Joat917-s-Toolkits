import os
from random import randint
from time import sleep, localtime
from PIL import Image as Im, ImageDraw as Imd, ImageFont as Imf
from math import sin
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import pygame as pg

SCREEN_WIDTH = 720
SCREEN_HEIGHT = 540
BLOCK_WIDTH = 100
BLOCK_HEIGHT = 120
FIREWORK_SIZE = 10
FIREWORK_ACCELERATION = 1


def numcompare(digits1: list[int], digits2: list[int]) -> tuple[int]:
    # [1,2,3,4]&[2,3,3,5]->((A=)1, (B=)2)
    compared = [False]*4

    A = 0
    for i in range(4):
        if digits1[i] == digits2[i]:
            A += 1
            compared[i] = True

    count1 = [0]*10
    count2 = [0]*10
    for i in range(4):
        if not compared[i]:
            count1[digits1[i]] += 1
            count2[digits2[i]] += 1
    B = 0
    for i in range(10):
        B += min(count1[i], count2[i])

    return (A, B)


class Media:
    def __init__(self) -> None:
        _ROOT = os.path.abspath(os.path.dirname(__file__))
        while 'src' not in os.listdir(_ROOT):
            _ROOT = os.path.dirname(_ROOT)
            if os.path.dirname(_ROOT) == _ROOT:
                raise FileNotFoundError("Cannot find 'src' directory.")
            
        self.ROOT_PATH = os.path.abspath(os.path.join(_ROOT, 'assets', 'numguess'))
        # BG
        self.backgrounds = [pg.transform.scale(pg.image.load(os.path.join(self.ROOT_PATH, "Starnight.png")), (SCREEN_WIDTH, SCREEN_HEIGHT)),
                            pg.transform.scale(pg.image.load(os.path.join(self.ROOT_PATH, "Skyclean.png")), (SCREEN_WIDTH, SCREEN_HEIGHT))]

        # Blocks
        self.norm = [pg.transform.scale(pg.image.load(os.path.join(self.ROOT_PATH, f"Norm-{i}.png")), (BLOCK_WIDTH, BLOCK_HEIGHT)) for i in range(10)]
        self.high = [pg.transform.scale(pg.image.load(os.path.join(self.ROOT_PATH, f"High-{i}.png")), (BLOCK_WIDTH, BLOCK_HEIGHT)) for i in range(10)]
        self.crrt = [pg.transform.scale(pg.image.load(os.path.join(self.ROOT_PATH, f"Crrt-{i}.png")), (BLOCK_WIDTH, BLOCK_HEIGHT)) for i in range(10)]
        self.norm_none = pg.transform.scale(pg.image.load(os.path.join(self.ROOT_PATH, "Norm-None.png")), (BLOCK_WIDTH, BLOCK_HEIGHT))
        self.high_none = pg.transform.scale(pg.image.load(os.path.join(self.ROOT_PATH, "High-None.png")), (BLOCK_WIDTH, BLOCK_HEIGHT))

        # Icon
        self.icon = pg.image.load(os.path.join(self.ROOT_PATH, 'icon.png'))

        # Text
        self.font = Imf.truetype("arial.ttf", 30)
        self.textcanavas = Im.new("RGBA", (SCREEN_WIDTH, 40))

        # Help
        self.help = [pg.transform.scale(pg.image.load(os.path.join(self.ROOT_PATH, f"Help-{i}.png")), (SCREEN_WIDTH, SCREEN_HEIGHT)) for i in range(1, 7)]
        self.help_continue = pg.transform.scale(pg.image.load(os.path.join(self.ROOT_PATH, "Help-continue.png")), (300, 80))

        # Fireworks
        self.fireworks = [pg.transform.scale(pg.image.load(os.path.join(self.ROOT_PATH, f"Firework-{i}.png")), (FIREWORK_SIZE, FIREWORK_SIZE)) for i in range(10)]

    def getNorm(self, index):
        if index is None:
            return self.norm_none
        else:
            return self.norm[index]

    def getHigh(self, index):
        if index is None:
            return self.high_none
        else:
            return self.high[index]


MEDIA = Media()


class Inputs:
    def __init__(self, command) -> None:
        "do command(input) if enter pressed"
        self.cont = [None]*4
        self.tick = 0
        self.pictures = []
        self.get_pictures()
        self.command = command

    def clear(self) -> None:
        self.cont = [None]*4
        self.tick = 0
        self.get_pictures()

    def push(self, number: int) -> None:
        self.cont[self.tick] = number
        if self.tick < 3 and self.cont[self.tick+1] is None:
            self.tick += 1
        self.get_pictures()

    def back(self) -> None:
        if self.cont[self.tick] is None and self.tick:
            self.tick -= 1
        self.cont[self.tick] = None
        self.get_pictures()

    def delete(self) -> None:
        if self.cont[self.tick] is None and self.tick < 3:
            self.tick += 1
        self.cont[self.tick] = None
        self.get_pictures()

    def left(self) -> None:
        if self.tick:
            self.tick -= 1
            self.get_pictures()

    def right(self) -> None:
        if self.tick < 3:
            self.tick += 1
            self.get_pictures()

    def home(self) -> None:
        self.tick = 0
        self.get_pictures()

    def end(self) -> None:
        self.tick = 3
        self.get_pictures()

    def deal_event(self, event: pg.event.Event) -> None:
        if event.type == pg.KEYDOWN:
            if 48 <= event.key < 58:  # number 0~9
                self.push(event.key-48)
                return
            elif event.key == pg.K_BACKSPACE:
                self.back()
                return
            elif event.key == pg.K_LEFT:
                self.left()
                return
            elif event.key == pg.K_RIGHT:
                self.right()
                return
            elif event.key == pg.K_RETURN:
                self.command(self.cont)
                return
            elif event.key == pg.K_DELETE:
                self.delete()
                return
            elif event.key in [pg.K_ESCAPE, pg.K_c]:
                self.clear()
            elif event.key == pg.K_HOME:
                self.home()
            elif event.key == pg.K_END:
                self.end()
        return

    def get_pictures(self, win=False) -> None:
        self.pictures.clear()

        if win:
            for i in range(4):
                self.pictures.append(MEDIA.crrt[self.cont[i]])
            return
        else:
            for i in range(4):
                if self.tick == i:
                    self.pictures.append(MEDIA.getHigh(self.cont[i]))
                else:
                    self.pictures.append(MEDIA.getNorm(self.cont[i]))
            return

    def show(self, window: pg.Surface) -> None:
        window.blit(self.pictures[0], (20, 30))
        window.blit(self.pictures[1], (100, 30))
        window.blit(self.pictures[2], (180, 30))
        window.blit(self.pictures[3], (260, 30))
        pass

    def victory(self):
        self.get_pictures(win=True)


class Text:
    def __init__(self, text: str, y: int, color="#ffffff") -> None:
        self.text = text
        self.y = y
        self.picture = MEDIA.textcanavas.copy()
        imd = Imd.Draw(self.picture)
        imd.text((0, 0), self.text, fill=color, font=MEDIA.font)
        self.pic_buffer = self.picture.tobytes()
        self.surface = pg.image.frombuffer(
            self.pic_buffer, self.picture.size, "RGBA")

    def show(self, window: pg.Surface):
        window.blit(self.surface, (0, self.y))


class SqueezeTextHolder:
    def __init__(self, texts: list[str], lines=5, y0=300):
        self.lines = lines
        self.y0 = y0
        self.texts = texts
        self.surface = None
        self.tick = 0
        self.getsurface()

    def update(self, texts: list[str]):
        self.texts = texts
        self.getsurface()

    def deal_event(self, event: pg.event.Event) -> None:
        changed = False
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_UP:
                if self.tick:
                    self.tick -= 1
                    changed = True
            elif event.key == pg.K_DOWN:
                if self.tick < len(self.texts):
                    self.tick += 1
                    changed = True
            elif event.key == pg.K_PAGEDOWN:
                self.tick += 4
                if self.tick > len(self.texts):
                    self.tick = len(self.texts)
                changed = True
            elif event.key == pg.K_PAGEUP:
                self.tick -= 4
                if self.tick < 0:
                    self.tick = 0
                changed = True
        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 4:
                if self.tick:
                    self.tick -= 1
                    changed = True
            elif event.button == 5:
                if self.tick < len(self.texts):
                    self.tick += 1
                    changed = True
        if changed:
            self.getsurface()

    def getsurface(self) -> None:
        texts = self.texts+["#This is the bottom..."]
        while len(texts) <= self.lines+self.tick:
            texts.append("")
        canavas = Im.new("RGBA", (SCREEN_WIDTH, self.lines*50))
        canavasdraw = Imd.Draw(canavas)

        for i in range(self.lines):
            canavasdraw.text((0, 50*i), texts[self.tick+i], font=MEDIA.font)
        buffer = canavas.tobytes()
        self.surface = pg.image.frombuffer(
            buffer, (SCREEN_WIDTH, self.lines*50), "RGBA")

    def show(self, window: pg.Surface):
        window.blit(self.surface, (0, self.y0))


class CheatCode:
    def __init__(self, maingame):
        self.process = 0
        self.maingame = maingame
        self.cont = [pg.K_UP, pg.K_UP, pg.K_DOWN, pg.K_DOWN,
                     pg.K_LEFT, pg.K_RIGHT, pg.K_LEFT, pg.K_RIGHT,
                     pg.K_b, pg.K_a]

    def deal_event(self, event: pg.event.Event):
        if event.type == pg.KEYDOWN:
            if self.cont[self.process] == event.key:
                self.process += 1
                return
            elif self.cont[0] == event.key:
                self.process = 2
            else:
                self.process = 0
        if self.process == 10:
            self.maingame.game.answer = [0, 0, 0, 0]
            self.maingame.game.guess = lambda selv, inp: (4, 0)
            self.maingame.texts =\
                [Text("Cheat Code Passed", 150), Text("Cheat Code Passed", 200),
                 Text("Cheat Code Passed", 250)]
            self.maingame.game.victory = True
            self.maingame.input.cont = [0, 0, 0, 0]
            self.process = 0
            return


class NumGuess:
    def __init__(self):
        self.answer = [randint(0, 9) for i in range(4)]
        self.guesstime = 0
        self.guesshistory = []  # [[2,3,3,5]->(1,2) pairs]
        self.victory = False

    def guess(self, inp):
        if None in inp:
            return ("nan", "nan")
        result = numcompare(self.answer, inp)
        self.guesshistory.append((inp+[], result))
        self.guesstime += 1
        if result[0] == 4:
            self.victory = True
        return result

    def __add__(self, val: list) -> list[Text]:
        result = self.guess(val)
        out = []
        t0 = "".join([str(i) for i in val])
        out.append(Text(f"Your Guess: {t0}\n", 150))
        out.append(
            Text(f"Correct Digit Correct Place(CDCP): {result[0]}\n", 200))
        out.append(
            Text(f"Correct Digit Wrong Place(CDWP): {result[1]}\n", 250))
        return out

    def __repr__(self):
        out = ""
        out += "Guess object\n"

        if self.guesshistory:
            out += "History: \n"
            for item in self.guesshistory:
                out += "".join([str(i) for i in item[0]])
                out += f": CDCP-{item[1][0]}; CDWP-{item[1][1]}\n"

        out += "Answer: "
        for i in self.answer:
            out += str(i)

        out += "\nGuessTime: %i\n" % self.guesstime
        return out

    def gethistory(self) -> list[str]:
        index = 0
        out = []
        for item in self.guesshistory:
            t0 = "".join([str(i) for i in item[0]])
            text = f"Guess{index}: {t0} -> CDCP:{item[1][0]}; CDWP:{item[1][1]}"
            out.append(text)
            index += 1
        return out


class MainGame:
    def __init__(self) -> None:
        self.game = NumGuess()
        self.texts = []
        self.squeezedtexts = SqueezeTextHolder([])
        self.input = Inputs(self.guess)
        self.cheatcode = CheatCode(self)

        self.fireworks = []

        if 7 <= localtime().tm_hour < 18:
            self.background = MEDIA.backgrounds[1]
        else:
            self.background = MEDIA.backgrounds[0]

        pg.display.init()
        self.window = pg.display.set_mode((720, 540))
        pg.display.set_caption("NumGuess")
        pg.display.set_icon(MEDIA.icon)

    def restart(self):
        self.game = NumGuess()
        self.texts = []
        self.squeezedtexts = SqueezeTextHolder([])
        self.input = Inputs(self.guess)
        if 7 <= localtime().tm_hour < 18:
            self.background = MEDIA.backgrounds[1]
        else:
            self.background = MEDIA.backgrounds[0]

    def guess(self, guess: list[int]) -> None:
        self.texts.clear()
        self.texts += (self.game+guess)
        self.squeezedtexts.update(self.game.gethistory())

    def quit(self):
        L_pic = Im.new("RGBA", (SCREEN_WIDTH//2, SCREEN_HEIGHT),
                       (255, 0, 0, 63))
        Imd.Draw(L_pic).text((0, 250), "     QUIT(Q/X/Y/Esc)",
                             "#ffffff", font=MEDIA.font)
        L_pic = pg.image.frombuffer(
            L_pic.tobytes(), (SCREEN_WIDTH//2, SCREEN_HEIGHT), "RGBA")

        R_pic = Im.new("RGBA", (SCREEN_WIDTH//2, SCREEN_HEIGHT),
                       (0, 255, 0, 63))
        Imd.Draw(R_pic).text((0, 250), "       CANCEL(C/N)",
                             "#ffffff", font=MEDIA.font)
        R_pic = pg.image.frombuffer(
            R_pic.tobytes(), (SCREEN_WIDTH//2, SCREEN_HEIGHT), "RGBA")

        while True:
            self.window.blit(self.background, (0, 0))
            self.window.blit(L_pic, (0, 0))
            self.window.blit(R_pic, (SCREEN_WIDTH//2, 0))

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    exit()
                elif event.type == pg.KEYDOWN:
                    if event.key in [pg.K_q, pg.K_x, pg.K_y, pg.K_ESCAPE, pg.K_RETURN]:
                        pg.quit()
                        exit()
                    elif event.key in [pg.K_c, pg.K_n, pg.K_r, pg.K_p]:
                        self.window.blit(pg.image.frombuffer(
                            Im.new("RGBA", (SCREEN_WIDTH, SCREEN_HEIGHT),
                                   (0, 0, 0, 255)).tobytes(),
                            (SCREEN_WIDTH, SCREEN_HEIGHT), "RGBA"),
                            (0, 0))
                        self.window.blit(self.background, (0, 0))
                        return
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        x = pg.mouse.get_pos()[0]
                        if x < SCREEN_WIDTH//2:
                            pg.quit()
                            exit()
                        else:
                            self.window.blit(pg.image.frombuffer(
                                Im.new("RGBA", (SCREEN_WIDTH, SCREEN_HEIGHT),
                                       (0, 0, 0, 255)).tobytes(),
                                (SCREEN_WIDTH, SCREEN_HEIGHT), "RGBA"),
                                (0, 0))
                            self.window.blit(self.background, (0, 0))
                            return

            pg.display.update()
            sleep(0.05)

    def help(self):
        tick = 0.1  # to adjust the floating text
        phase = 0  # to decide which picture to show
        idle = False  # to decide whether the floating text to show
        while True:
            self.window.blit(self.background, (0, 0))
            try:
                self.window.blit(MEDIA.help[phase], (0, 0))
            except IndexError:
                return

            # Origin blits
            self.input.show(self.window)
            for txt in self.texts:
                txt.show(self.window)
            self.squeezedtexts.show(self.window)

            # Events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.quit()
                    idle = False
                elif event.type == pg.KEYDOWN:
                    if event.key in [pg.K_q, pg.K_x, pg.K_p]:
                        self.quit()
                        idle = False
                    elif event.key in [pg.K_h, pg.K_ESCAPE]:
                        idle = False
                        return
                    elif event.key in [pg.K_SPACE, pg.K_RIGHT, pg.K_PAGEDOWN]:
                        idle = False
                        phase += 1
                    elif event.key in [pg.K_LEFT, pg.K_PAGEUP]:

                        if phase:
                            idle = False
                            phase -= 1
                        else:
                            idle = True
                    else:
                        idle = True
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if event.button in [1, 5]:
                        idle = False
                        phase += 1
                    if event.button == 4:
                        if phase:
                            idle = False
                            phase -= 1
                        else:
                            idle = True
                    else:
                        idle = True
                elif event.type not in [pg.MOUSEBUTTONUP, pg.KEYUP, pg.MOUSEMOTION]:
                    idle = True

            # Floating text
            if idle:
                self.window.blit(MEDIA.help_continue, (100*(1-sin(tick)), 400))

            pg.display.update()
            tick += 0.1
            sleep(0.05)

    def mainloop(self):
        while True:
            self.window.blit(self.background, (0, 0))

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.quit()
                else:
                    if event.type == pg.KEYDOWN:
                        if event.key == pg.K_r:
                            self.restart()
                        elif event.key in [pg.K_q, pg.K_p, pg.K_x]:
                            self.quit()
                        elif event.key == pg.K_h:
                            self.help()
                    if not self.game.victory:
                        self.cheatcode.deal_event(event)
                        self.input.deal_event(event)
                    self.squeezedtexts.deal_event(event)

            if self.game.victory:
                self.input.victory()

                if not randint(0, 10):
                    self.fireworks.append(Firework(self))

            for firework in self.fireworks:
                firework.show()
            self.input.show(self.window)
            for txt in self.texts:
                txt.show(self.window)
            self.squeezedtexts.show(self.window)

            pg.display.update()
            sleep(0.05)


class Firework:
    def __init__(self, maingame: MainGame) -> None:
        self.window = maingame.window
        self.game = maingame

        color = randint(0, 9)
        self.pictures = [pg.transform.scale(
            MEDIA.fireworks[color], (i, i)) for i in range(1, 11)]  # slice is its size+1
        self.x = SCREEN_WIDTH
        self.y = SCREEN_HEIGHT
        self.vx = randint(-20, -5)
        self.vy = randint(-30, -20)
        self.ay = FIREWORK_ACCELERATION

        self.time = randint(10, 20)

    def show(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.ay
        self.window.blit(self.pictures[-1], (self.x, self.y))

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


class FireTrace:
    def __init__(self, firework: Firework):
        self.firework = firework
        self.x = firework.x+0
        self.y = firework.y+0
        self.time = 8

    def show(self):
        self.firework.window.blit(
            self.firework.pictures[self.time], (self.x, self.y))
        self.time -= 1
        if self.time < 0:
            self.firework.game.fireworks.remove(self)


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

    def show(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.ay
        self.window.blit(self.pictures[self.time//5], (self.x, self.y))

        self.time -= 1
        self.game.fireworks.append(FireTrace(self))
        if self.time < 0:
            self.game.fireworks.remove(self)


if __name__ == "__main__":
    while True:
        try:
            MainGame().mainloop()
        except Exception:
            __import__('traceback').print_exc()
            input(":(\n")
