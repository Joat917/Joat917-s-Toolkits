from BaseImport import *

SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN_SIZE
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
    def __init__(self) -> None:
        # Text
        self.font = Imf.truetype("arial.ttf", 30)
        self.textcanavas = Im.new("RGBA", (SCREEN_WIDTH, 40))

        # Fireworks
        self.fireworks = [pg.transform.scale(pg.image.load(MediaPath/f"Firework-{i}.png"),
                                             (FIREWORK_SIZE, FIREWORK_SIZE))
                          for i in range(10)]


MEDIA = Media()



class Firework:
    def __init__(self, maingame, mousepos=None, waittime=None) -> None:
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
    def __init__(self, main):
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
