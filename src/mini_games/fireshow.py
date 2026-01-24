from random import randint, random
from time import sleep
import os
from PIL import Image as Im, ImageDraw as Imd, ImageFont as Imf
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "shutup"
import pygame as pg

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
FIREWORK_SIZE = 10
FIREWORK_ACCELERATION = 1

POSSIBILITY = 5  # the larger, the rarer, bigger than 0


def get_vinitial(x_target, y_target, x_start, y_start=SCREEN_HEIGHT, time=randint(5, 15)):
    "return vx_init, vy_init"
    vx = (x_target-x_start)/time
    # "y = 1/2 a t2 + vt"
    vy = (y_target-y_start)/time-0.5*FIREWORK_ACCELERATION*time

    return vx, vy


class Media:
    ROOT_PATH = '../../assets/numguess/'
    def __init__(self) -> None:
        try:
            self.backgrounds = pg.transform.scale(pg.image.load(os.path.join(self.ROOT_PATH, "Starnight2.png")), (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception:
            self.backgrounds = self.generate_background()
        self.icon = pg.image.load(os.path.join(self.ROOT_PATH, "icon_fireshow.png"))
        self.font = Imf.truetype("arial.ttf", 30)
        self.textcanavas = Im.new("RGBA", (SCREEN_WIDTH, 40))
        self.fireworks = [pg.transform.scale(pg.image.load(os.path.join(self.ROOT_PATH, f"Firework-{i}.png")), (FIREWORK_SIZE, FIREWORK_SIZE))for i in range(10)]

    def generate_background(self):
        import numpy as np
        im_arr = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH, 4), dtype=np.uint8)
        im_arr[:,:,3] = 255
        X, Y = np.meshgrid(np.arange(SCREEN_WIDTH), np.arange(SCREEN_HEIGHT))
        im_arr[:, :, 0:3] = np.einsum('ij,k->ijk', (X+Y)/(SCREEN_WIDTH+SCREEN_HEIGHT), [23, 55, 94]).astype(np.uint8)
        im = Im.fromarray(im_arr, mode="RGBA")

        star_im = Im.open(os.path.join(self.ROOT_PATH, "Firework-9.png")).convert("RGBA")

        for _ in range(randint(80, 150)):
            size = randint(5, 12)
            alpha = random()*0.8
            position = (randint(0, SCREEN_WIDTH-size), randint(0, SCREEN_HEIGHT-size))
            star_resized = star_im.resize((size, size))
            im.paste(star_resized, position, star_resized.getchannel("A").point(lambda p: p*alpha))
        
        return pg.image.frombuffer(im.tobytes(), (SCREEN_WIDTH, SCREEN_HEIGHT), "RGBA")


MEDIA = Media()


class MainGame:
    def __init__(self) -> None:
        self.texts = []

        self.fireworks = []
        self.letter = Letter(self)

        self.background = MEDIA.backgrounds

        pg.display.init()
        self.window = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption("FireShow")
        pg.display.set_icon(MEDIA.icon)

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

    def mainloop(self):
        while True:
            self.window.blit(self.background, (0, 0))

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.quit()
                else:
                    if event.type == pg.KEYDOWN:
                        if event.key in [3, 17, 16, 26]:
                            self.quit()

                    if event.type == pg.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            self.fireworks.append(
                                Firework(self, pg.mouse.get_pos()))
                    # self.squeezedtexts.deal_event(event)
                    self.letter.dealevent(event)

            if not randint(0, POSSIBILITY):
                self.fireworks.append(Firework(self))

            for firework in self.fireworks:
                firework.show()
            for txt in self.texts:
                txt.show(self.window)
            # self.squeezedtexts.show(self.window)

            pg.display.update()
            sleep(0.05)


class Firework:
    def __init__(self, maingame: MainGame, mousepos=None, waittime=None) -> None:
        self.window = maingame.window
        self.game = maingame

        color = randint(0, 9)
        self.pictures = [pg.transform.scale(
            MEDIA.fireworks[color], (i, i)) for i in range(1, 11)]  # slice is its size+1

        # Mousepos?
        if mousepos is not None:
            self.x = randint(0, SCREEN_WIDTH)
            self.y = SCREEN_HEIGHT
            self.ay = FIREWORK_ACCELERATION
            if waittime is None:
                self.time = randint(10, 20)
            else:
                self.time = waittime
            self.vx, self.vy = get_vinitial(
                *mousepos, self.x, time=self.time+1)
            return

        # Corner or bottomside?
        if randint(0, 1):
            # Which corner, BL or BR?
            if randint(0, 1):
                self.x = SCREEN_WIDTH
                self.y = SCREEN_HEIGHT
                self.vx = randint(-20, -5)
                self.vy = randint(-33, -25)
                self.ay = FIREWORK_ACCELERATION
            else:
                self.x = 0
                self.y = SCREEN_HEIGHT
                self.vx = randint(5, 20)
                self.vy = randint(-33, -25)
                self.ay = FIREWORK_ACCELERATION
        else:
            self.x = randint(40, SCREEN_WIDTH-40)
            self.y = SCREEN_HEIGHT
            self.vx = randint(-5, 5)
            self.vy = randint(-30, -10)
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

        self.time = randint(6, 20)

    def show(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.ay
        self.window.blit(self.pictures[self.time//5], (self.x, self.y))

        self.time -= 1
        self.game.fireworks.append(FireTrace(self))
        if self.time < 0:
            self.game.fireworks.remove(self)


class Letter:
    def __init__(self, main: MainGame):
        self.main = main
        self.font = Imf.truetype("arial.ttf", 10)
        self.image = Im.new("L", (8, 10))
        self.shift_down = False
        self.offset = (randint(100, SCREEN_WIDTH-400), -150)
        self.zoom = 60

    def dealevent(self, event):
        if event.type == pg.KEYDOWN:
            if event.key in [pg.K_LSHIFT, pg.K_RSHIFT]:
                self.shift_down = True
            elif 97 <= event.key <= 122:
                if not self.shift_down:
                    char = chr(event.key-32)
                else:
                    char = chr(event.key)

                image = self.image.copy()
                imagedraw = Imd.Draw(image)
                imagedraw.text((0, 0), char, 255, self.font)
                waittime = randint(3, 5)

                for x in range(8):
                    for y in range(10):
                        if image.getpixel((x, y)) >> 7:
                            self.main.fireworks.append(
                                Firework(self.main,
                                         (self.offset[0]+x*self.zoom,
                                          self.offset[1]+y*self.zoom),
                                         waittime))

                self.offset = (randint(100, SCREEN_WIDTH-400), -150)
            elif 48 <= event.key < 58:
                char = chr(event.key)
                image = self.image.copy()
                imagedraw = Imd.Draw(image)
                imagedraw.text((0, 0), char, 255, self.font)
                waittime = randint(3, 5)

                for x in range(8):
                    for y in range(10):
                        if image.getpixel((x, y)) >> 7:
                            self.main.fireworks.append(
                                Firework(self.main,
                                         (self.offset[0]+x*self.zoom,
                                          self.offset[1]+y*self.zoom),
                                         waittime))

                self.offset = (randint(100, SCREEN_WIDTH-400), -150)

        elif event.type == pg.KEYUP:
            if event.key in [pg.K_LSHIFT, pg.K_RSHIFT]:
                self.shift_down = False


if __name__ == "__main__":
    while True:
        try:
            MainGame().mainloop()
        except Exception:
            __import__('traceback').print_exc()
            input(":(\n")
