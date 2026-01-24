import os
from sys import exit
from copy import deepcopy
from random import randint, random
from math import ceil as ceiling
from PIL import Image as Im, ImageDraw as Imd, ImageFont as Imf
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame as pg

STRAIGHT_CLASSIC = True  # do not use arrows to make straight-forward lights
LAG_TIME = 2  # Speed for simulation slow down for ~ times

UP = 0
LEFT = 1
RIGHT = 3
DOWN = 2
FORWARD = 0
TURNLEFT = 1
TURNRIGHT = 3
TURNBACK = 2
RED = 4
YELLOW = 2
GREEN = 1
ROAD_LENGTH = 20
SIZE = 51  # Default size when drawing the lights
# It multiplies (11+2*ROAD_LENGTH)(namely 51) is the side of the mainwindow!
PIXELSIZE = 12
MAINSIZE = PIXELSIZE*(11+2*ROAD_LENGTH)
BACKGROUND_COLOR = (153, 217, 234, 255)

FPS = 30

# possibility of cars on each turnings of each track
POSSIBILITY = [[0.15, 0.15, 0.35, 0.35]+[]*(FORWARD),
               [0.15, 0.1, 0.35, 0.1]+[]*(TURNLEFT),
               [UP, LEFT, DOWN, RIGHT]+[]*(0),
               [0.1, 0.15, 0.1, 0.35]+[]*(TURNRIGHT)]

# Default traffic light
Traffic_timeperiod = 200
Traffic_instruction = ['FromUp', 'FromLeft', 'FromDown', 'FromRight']
# Traffic_leftSignals = [(74, 106), (178, 200), (32, 106), (178, 200)]
# Traffic_straightSignals = [(0, 32), (106, 178), (0, 74), (106, 178)]
Traffic_leftSignals = [(70, 110), (174, 204), (28, 130), (174, 204)]
Traffic_straightSignals = [(196, 36), (126, 182), (196, 78), (102, 182)]
Traffic_rightSignals = [(179, 104), (0, 200), (0, 200), (0, 200)]

"""
phases:(2:3:7)
up2down(3/3) & down2up(3/7) - 3 (0, 32)
down2up(4/7) & down2left(4/7) - 4 (32, 74)
down2left(3+/7) & up2right(3/3) - 3 (74, 106)
left2right(7-/3) & right2left(7/7) - 7 (106, 178)
left2up(2/2) & right2down(2/2) - 2 (178, 200)
"""

#SidePanel or Extention
EXTENTION_WIDTH = 240
FONT = Imf.truetype('arial.ttf', SIZE)
# FONT=Imf.truetype('simkai.ttf')
FONT_SMALLER = Imf.truetype('arial.ttf', int(SIZE*0.6))

DIGITS = {
    1: [1, 1, 0, 0, 0, 0, 0],
    2: [1, 0, 1, 1, 0, 1, 1],
    3: [1, 1, 1, 0, 0, 1, 1],
    4: [1, 1, 0, 0, 1, 0, 1],
    5: [0, 1, 1, 0, 1, 1, 1],
    6: [0, 1, 1, 1, 1, 1, 1],
    7: [1, 1, 0, 0, 0, 1, 0],
    8: [1, 1, 1, 1, 1, 1, 1],
    9: [1, 1, 1, 0, 1, 1, 1],
    0: [1, 1, 1, 1, 1, 1, 0],
    'H': [1, 1, 0, 1, 1, 0, 1]
}
DIRECTION_DICT = {UP: "UP", DOWN: "DOWN", LEFT: "LEFT", RIGHT: "RIGHT"}


def move(direction: int, x: int, y: int, step=1):
    if direction == UP:
        y += 1
    elif direction == DOWN:
        y -= 1
    elif direction == LEFT:
        x -= 1
    elif direction == RIGHT:
        x += 1
    else:
        raise ValueError
    return x, y


def img2suf(image: Im.Image, format='RGBA') -> pg.Surface:
    size = image.size
    return pg.image.frombuffer(
        image.tobytes(), size, format)


def make_text(text: str, align='left', size=(300, 50), font=FONT_SMALLER, color=(0, 0, 0, 255)) -> Im.Image:
    image = Im.new('RGBA', size)
    Imd.Draw(image).text((0, 0), text, color,
                         font, align=align)
    return image


class Node:
    def __init__(self, x: int, y: int) -> None:
        self.neighbors = [None]*4
        self.occupied = None
        self.coordinate = [(y, -x), (-x, -y), (-y, x), (x, y)]
        pass

    def connect(self, other):
        dx = other.coordinate[-1][0]-self.coordinate[-1][0]
        dy = other.coordinate[-1][1]-self.coordinate[-1][1]

        if dx == 1 and dy == 0:
            self.neighbors[RIGHT] = other
            other.neighbors[LEFT] = self
        elif dx == -1 and dy == 0:
            self.neighbors[LEFT] = other
            other.neighbors[RIGHT] = self
        elif dx == 0 and dy == 1:
            self.neighbors[UP] = other
            other.neighbors[DOWN] = self
        elif dx == 0 and dy == -1:
            self.neighbors[DOWN] = other
            other.neighbors[UP] = self
        else:
            print(
                f"Warning: not connecting neighbor: ({self.coordinate[-1]})->({other.coordinate[-1]})")
            return False
        return True

    def oneway(self, other):
        dx = other.coordinate[-1][0]-self.coordinate[-1][0]
        dy = other.coordinate[-1][1]-self.coordinate[-1][1]

        if dx == 1 and dy == 0:
            self.neighbors[RIGHT] = other
        elif dx == -1 and dy == 0:
            self.neighbors[LEFT] = other
        elif dx == 0 and dy == 1:
            self.neighbors[UP] = other
        elif dx == 0 and dy == -1:
            self.neighbors[DOWN] = other
        else:
            print(
                f"Warning: not connecting neighbor: ({self.coordinate[-1]})->({other.coordinate[-1]})")
            return False
        return True


class Grid:
    def __init__(self) -> None:
        self.nodes = {}
        self.pixelsize = PIXELSIZE
        self.image = Im.new(
            "RGBA", (MAINSIZE, MAINSIZE), (0, 0, 0, 64))
        self.imd = Imd.Draw(self.image)

        for x in range(-5, 6):
            for y in range(-5, 6):
                if abs(x)+abs(y) < 8:
                    self.nodes[(x, y)] = (Node(x, y))
                    self.setSquare(x, y, (80, 80, 80, 255))

        for x in range(-5, 6):
            for y in range(-5, 6):
                if abs(x)+abs(y) < 8:
                    for direction in range(4):
                        temp = move(direction, x, y)
                        if temp in self.nodes:
                            self.nodes[(x, y)].connect(self.nodes[temp])

        # From Down
        for side in range(-2, 3):
            for ahead in range(ROAD_LENGTH):
                self.nodes[(side, ahead-5-ROAD_LENGTH)
                           ] = Node(side, ahead-5-ROAD_LENGTH)
                if side >= 0:
                    self.setSquare(*(side, ahead-5-ROAD_LENGTH),
                                   (15+15*side, 15+15*side, 15+15*side, 255))
                else:
                    self.setSquare(*(side, ahead-5-ROAD_LENGTH),
                                   (80, 80, 80, 255))
        for side in range(-2, 3):
            for ahead in range(ROAD_LENGTH):
                if side >= 0:
                    self.nodes[(side, ahead-5-ROAD_LENGTH)
                               ].oneway(self.nodes[(side, ahead-4-ROAD_LENGTH)])
                else:
                    self.nodes[(side, ahead-4-ROAD_LENGTH)
                               ].oneway(self.nodes[(side, ahead-5-ROAD_LENGTH)])

        # from up
        for side in range(-2, 3):
            for ahead in range(ROAD_LENGTH):
                self.nodes[(-side, 5+ROAD_LENGTH-ahead)
                           ] = Node(-side, 5+ROAD_LENGTH-ahead)
                if side >= 0:
                    self.setSquare(*(-side, 5+ROAD_LENGTH-ahead),
                                   (15+15*side, 15+15*side, 15+15*side, 255))
                else:
                    self.setSquare(*(-side, 5+ROAD_LENGTH-ahead),
                                   (80, 80, 80, 255))

        for side in range(-2, 3):
            for ahead in range(ROAD_LENGTH):
                if side >= 0:
                    self.nodes[(-side, 5+ROAD_LENGTH-ahead)
                               ].oneway(self.nodes[(-side, 4+ROAD_LENGTH-ahead)])
                else:
                    self.nodes[(-side, 4+ROAD_LENGTH-ahead)
                               ].oneway(self.nodes[(-side, 5+ROAD_LENGTH-ahead)])

        # from left
        for side in range(-2, 3):
            for ahead in range(ROAD_LENGTH):
                self.nodes[(ahead-5-ROAD_LENGTH, -side)
                           ] = Node(ahead-5-ROAD_LENGTH, -side)
                if side >= 0:
                    self.setSquare(*(ahead-5-ROAD_LENGTH, -side),
                                   (15+15*side, 15+15*side, 15+15*side, 255))
                else:
                    self.setSquare(*(ahead-5-ROAD_LENGTH, -side),
                                   (80, 80, 80, 255))
        for side in range(-2, 3):
            for ahead in range(ROAD_LENGTH):
                if side >= 0:
                    self.nodes[(ahead-5-ROAD_LENGTH, -side)
                               ].oneway(self.nodes[(ahead-4-ROAD_LENGTH, -side)])
                else:
                    self.nodes[(ahead-4-ROAD_LENGTH, -side)
                               ].oneway(self.nodes[(ahead-5-ROAD_LENGTH, -side)])

        # from right
        for side in range(-2, 3):
            for ahead in range(ROAD_LENGTH):
                self.nodes[(5+ROAD_LENGTH-ahead, side)
                           ] = Node(5+ROAD_LENGTH-ahead, side)
                if side >= 0:
                    self.setSquare(*(5+ROAD_LENGTH-ahead, side),
                                   (15+15*side, 15+15*side, 15+15*side, 255))
                else:
                    self.setSquare(*(5+ROAD_LENGTH-ahead, side),
                                   (80, 80, 80, 255))
        for side in range(-2, 3):
            for ahead in range(ROAD_LENGTH):
                if side >= 0:
                    self.nodes[(5+ROAD_LENGTH-ahead, side)
                               ].oneway(self.nodes[(4+ROAD_LENGTH-ahead, side)])
                else:
                    self.nodes[(4+ROAD_LENGTH-ahead, side)
                               ].oneway(self.nodes[(5+ROAD_LENGTH-ahead, side)])

        pass

    def getImagePlace(self, x: int, y: int) -> tuple:
        "return coordinates in the image"
        return self.pixelsize//2+self.pixelsize * (ROAD_LENGTH+5+x),\
            self.image.size[1]-1-(self.pixelsize//2 +
                                  self.pixelsize * (ROAD_LENGTH+5+y))

    def setSquare(self, x: int, y: int, color: tuple):
        "Paint the image with each block self.pixelsize"
        target_central_x, target_central_y = self.getImagePlace(x, y)
        half_pixel = ceiling(self.pixelsize/2)
        target_TL_x, target_BR_x = \
            target_central_x-half_pixel, target_central_x+half_pixel-1
        target_TL_y, target_BR_y = \
            target_central_y-half_pixel, target_central_y+half_pixel-1
        self.imd.rectangle((target_TL_x, target_TL_y, target_BR_x, target_BR_y),
                           fill=color)


class TrafficLight:
    def __init__(self) -> None:
        self.timeperiod = Traffic_timeperiod
        self.leftSignals = Traffic_leftSignals
        self.straightSignals = Traffic_straightSignals
        self.rightSignals = Traffic_rightSignals
        Traffic_timeperiod

        self.now_status = 0
        self.leftSignal = [RED]*4
        self.straightSignal = [GREEN, RED]*2
        self.rightSignal = [GREEN]*4

    def mainoperate(self):
        self.now_status += 1
        self.now_status %= self.timeperiod
        for direction in range(4):
            if self.leftSignal[direction] & RED:
                if self.now_status == self.leftSignals[direction][0]:
                    self.leftSignal[direction] = GREEN
                elif self.now_status in [(self.leftSignals[direction][0]-i) % self.timeperiod for i in range(4)]:
                    self.leftSignal[direction] = RED | YELLOW
            elif self.leftSignal[direction] & YELLOW:
                if self.now_status == (self.leftSignals[direction][1]-1) % self.timeperiod:
                    self.leftSignal[direction] = RED
            elif self.leftSignal[direction] & GREEN:
                if self.now_status == (self.leftSignals[direction][1]-4) % self.timeperiod\
                        and (self.leftSignals[direction][0]-self.leftSignals[direction][1]) % self.timeperiod > 4:
                    self.leftSignal[direction] = YELLOW

            if self.straightSignal[direction] & RED:
                if self.now_status == self.straightSignals[direction][0]:
                    self.straightSignal[direction] = GREEN
                elif self.now_status in [(self.straightSignals[direction][0]-i) % self.timeperiod for i in range(4)]:
                    self.straightSignal[direction] = RED | YELLOW
            elif self.straightSignal[direction] & YELLOW:
                if self.now_status == (self.straightSignals[direction][1]-1) % self.timeperiod:
                    self.straightSignal[direction] = RED
            elif self.straightSignal[direction] & GREEN:
                if self.now_status == (self.straightSignals[direction][1]-4) % self.timeperiod\
                        and (self.straightSignals[direction][0]-self.straightSignals[direction][1]) % self.timeperiod > 4:
                    self.straightSignal[direction] = YELLOW

            if self.rightSignal[direction] & RED:
                if self.now_status == self.rightSignals[direction][0]:
                    self.rightSignal[direction] = GREEN
                elif self.now_status in [(self.rightSignals[direction][0]-i) % self.timeperiod for i in range(4)]:
                    self.rightSignal[direction] = RED | YELLOW
            elif self.rightSignal[direction] & YELLOW:
                if self.now_status == (self.rightSignals[direction][1]-1) % self.timeperiod:
                    self.rightSignal[direction] = RED
            elif self.rightSignal[direction] & GREEN:
                if self.now_status == (self.rightSignals[direction][1]-4) % self.timeperiod\
                        and (self.rightSignals[direction][0]-self.rightSignals[direction][1]) % self.timeperiod > 4:
                    self.rightSignal[direction] = YELLOW

    @ staticmethod
    def paint1(status: int, size=SIZE):
        portion = 0.6
        half_size = size//2
        circle_radius = round(portion*size/2)
        image = Im.new("RGBA", (size, 3*size), (0, 0, 0, 128))
        draw = Imd.Draw(image)
        if status & RED:
            draw.ellipse((half_size-circle_radius, half_size-circle_radius,
                          half_size+circle_radius, half_size+circle_radius),
                         fill=(255, 64, 64, 255))
        else:
            draw.ellipse((half_size-circle_radius, half_size-circle_radius,
                          half_size+circle_radius, half_size+circle_radius),
                         fill=(127, 127, 127, 255))

        if status & YELLOW:
            draw.ellipse((half_size-circle_radius, 3*half_size-circle_radius,
                          half_size+circle_radius, 3*half_size+circle_radius),
                         fill=(255, 255, 64, 255))
        else:
            draw.ellipse((half_size-circle_radius, 3*half_size-circle_radius,
                          half_size+circle_radius, 3*half_size+circle_radius),
                         fill=(127, 127, 127, 255))

        if status & GREEN:
            draw.ellipse((half_size-circle_radius, 5*half_size-circle_radius,
                          half_size+circle_radius, 5*half_size+circle_radius),
                         fill=(64, 255, 64, 255))
        else:
            draw.ellipse((half_size-circle_radius, 5*half_size-circle_radius,
                          half_size+circle_radius, 5*half_size+circle_radius),
                         fill=(127, 127, 127, 255))

        return image

    @ staticmethod
    def paintArrow(direction: int, size=SIZE, width=SIZE//5, fill=(255, 255, 255, 255)):
        half_size = size//2
        image = Im.new("RGBA", (size, size))
        draw = Imd.Draw(image)
        draw.line((half_size, 0, half_size, size-1), fill=fill, width=width)
        draw.line((half_size, 0, 0, half_size), fill=fill, width=width)
        draw.line((half_size, 0, size-1, half_size), fill=fill, width=width)

        image = image.rotate(90*direction)
        return image

    @ staticmethod
    def paintA(status: int, direction: int, size=SIZE):
        portion = 0.6
        half_size = size//2
        circle_radius = round(portion*size/2)
        image = Im.new("RGBA", (size, 3*size), (0, 0, 0, 128))
        draw = Imd.Draw(image)

        draw.ellipse((half_size-circle_radius, half_size-circle_radius,
                      half_size+circle_radius, half_size+circle_radius),
                     fill=(127, 127, 127, 255))
        draw.ellipse((half_size-circle_radius, 3*half_size-circle_radius,
                      half_size+circle_radius, 3*half_size+circle_radius),
                     fill=(127, 127, 127, 255))
        draw.ellipse((half_size-circle_radius, 5*half_size-circle_radius,
                      half_size+circle_radius, 5*half_size+circle_radius),
                     fill=(127, 127, 127, 255))

        if status & RED:
            target = TrafficLight.paintArrow(
                direction, half_size, round(half_size/5), (255, 64, 64))
            image.paste(target,
                        (half_size-target.size[0]//2, half_size-target.size[1]//2), target)

        if status & YELLOW:
            target = TrafficLight.paintArrow(
                direction, half_size, round(half_size/5), (255, 255, 0))
            image.paste(target,
                        (half_size-target.size[0]//2, 3*half_size-target.size[1]//2), target)

        if status & GREEN:
            target = TrafficLight.paintArrow(
                direction, half_size, round(half_size/5), (64, 255, 64))
            image.paste(target,
                        (half_size-target.size[0]//2, 5*half_size-target.size[1]//2), target)

        return image

    def paint3(self, direction, size=SIZE):
        gap = round(0.05*size)
        image = Im.new("RGBA", (size*3+gap*2, size*3))
        image.paste(TrafficLight.paintA(
            self.leftSignal[direction], TURNLEFT, size), (0, 0))

        if STRAIGHT_CLASSIC:
            image.paste(TrafficLight.paint1(
                self.straightSignal[direction], size), (size+gap, 0))
        else:
            image.paste(TrafficLight.paintA(
                self.straightSignal[direction], FORWARD, size), (size+gap, 0))

        image.paste(TrafficLight.paintA(
            self.rightSignal[direction], TURNRIGHT, size), (size*2+gap*2, 0))
        return image

    @ staticmethod
    def paintdigit(digit: int, color=(255, 255, 255, 255), size=SIZE, width=SIZE//8):
        gap = width//2
        image = Im.new("RGBA", (size, size*2), (0, 0, 0, 0))
        draw = Imd.Draw(image)

        if DIGITS[digit][0]:
            draw.line((size-1-gap, gap, size-1-gap, size-1-gap), color, width)
        if DIGITS[digit][1]:
            draw.line((size-1-gap, size+gap,
                       size-1 - gap, 2*size-1-gap), color, width)
        if DIGITS[digit][2]:
            draw.line((gap, 2*size-1-gap,
                       size-1-gap, 2*size-1-gap), color, width)
        if DIGITS[digit][3]:
            draw.line((gap, size+gap, gap, 2*size-1-gap), color, width)
        if DIGITS[digit][4]:
            draw.line((gap, gap, gap, size-1-gap), color, width)
        if DIGITS[digit][5]:
            draw.line((gap, gap, size-1-gap, gap), color, width)
        if DIGITS[digit][6]:
            draw.line((gap, size-1, size-1-gap, size-1), color, width)

        return image

    @ staticmethod
    def paint2digits(digit: int, color=(255, 255, 255, 255), size=SIZE, width=SIZE//8):
        if digit < 0 or digit >= 100:
            imageL = imageR = TrafficLight.paintdigit('H', color, size, width)
        else:
            digL, digR = divmod(digit, 10)
            imageL = TrafficLight.paintdigit(digL, color, size, width)
            imageR = TrafficLight.paintdigit(digR, color, size, width)

        gap = round(size*0.1)
        image = Im.new('RGBA', size=(2*size+gap, 2*size))
        image.paste(imageL, (0, 0))
        image.paste(imageR, (size+gap, 0))

        return image

    def painttime(self, direction: int, turning: int, size=SIZE):
        if turning is TURNLEFT:
            if self.leftSignal[direction] & RED:
                count = (-self.now_status +
                         self.leftSignals[direction][0]) % self.timeperiod
                return TrafficLight.paint2digits(count, (255, 64, 64, 255), size, round(size/9))
            elif self.leftSignal[direction] & GREEN:
                count = (-self.now_status +
                         self.leftSignals[direction][1]-4) % self.timeperiod
                return TrafficLight.paint2digits(count, (64, 255, 64, 255), size, round(size/9))
            else:
                return Im.new("RGBA", (size*2+round(size*0.1), size*2))

        elif turning is FORWARD:
            if self.straightSignal[direction] & RED:
                count = (-self.now_status +
                         self.straightSignals[direction][0]) % self.timeperiod
                return TrafficLight.paint2digits(count, (255, 64, 64, 255), size, round(size/9))
            elif self.straightSignal[direction] & GREEN:
                count = (-self.now_status +
                         self.straightSignals[direction][1]-4) % self.timeperiod
                return TrafficLight.paint2digits(count, (64, 255, 64, 255), size, round(size/9))
            else:
                return Im.new("RGBA", (size*2+round(size*0.1), size*2))
        else:
            return Im.new("RGBA", (size*2+round(size*0.1), size*2))


class Car:
    cars = []

    def __init__(self, fromdir: int, turning: int, place: Node, trafficlight: TrafficLight, statics=None) -> None:
        self.fromdir = fromdir
        self.turning = turning
        self.tick = 0
        self.place = place
        self.ahead, self.offpos = self.place.coordinate[self.fromdir-TURNBACK]
        self.trafficlight = trafficlight
        self.color = (randint(128, 255), randint(
            128, 255), randint(128, 255), 255)
        self.size = (round(SIZE/7), round(SIZE/7))
        self.image = Im.new("RGBA", self.size, self.color)
        self.statics = statics

        self.place.occupied = self

    def forward(self, direction: int) -> bool:
        direction %= 4
        target = self.place.neighbors[direction]
        if target is None or target.occupied is not None:
            return False
        if self.ahead == -6:
            if self.turning is TURNLEFT:
                if self.trafficlight.leftSignal[self.fromdir] is not GREEN:
                    return True
            elif self.turning is TURNRIGHT:
                if self.trafficlight.rightSignal[self.fromdir] is not GREEN:
                    return True
            elif self.turning is FORWARD:
                if self.trafficlight.straightSignal[self.fromdir] is not GREEN:
                    return True

        self.place.occupied = None
        target.occupied = self
        self.place = target
        # you point to where, reverse needed
        self.ahead, self.offpos = self.place.coordinate[self.fromdir-TURNBACK]
        return True

    def move(self):
        self.tick += 1
        if self.turning is TURNRIGHT:
            # try
            if self.forward(self.fromdir-TURNRIGHT):
                return
            else:
                if self.ahead < -1:
                    if self.forward(self.fromdir-TURNBACK):
                        return
            # you may have got to the destination
            if self.offpos == -ROAD_LENGTH-5:
                if self.statics is not None:
                    self.statics.reachDestination(
                        self.tick, self.fromdir, self.turning)
                Car.cars.remove(self)
                self.place.occupied = None
            return
        elif self.turning is FORWARD:
            if self.offpos <= -3:
                if self.forward(self.fromdir-TURNLEFT):
                    return
            # try
            if self.forward(self.fromdir-TURNBACK):
                return
            else:
                if self.offpos > -3:
                    if self.forward(self.fromdir-TURNRIGHT):
                        return
            # you may have got to the destination
            if self.ahead == ROAD_LENGTH+5:
                if self.statics is not None:
                    self.statics.reachDestination(
                        self.tick, self.fromdir, self.turning)
                Car.cars.remove(self)
                self.place.occupied = None
            return
        elif self.turning is TURNLEFT:
            if self.ahead < 1 and 3*self.ahead - 4*self.offpos <= -9:
                # try to go striaght
                if self.forward(self.fromdir-TURNBACK):
                    return
                else:
                    # backup
                    if self.forward(self.fromdir-TURNLEFT):
                        return
            else:
                # try to go left
                if self.forward(self.fromdir-TURNLEFT):
                    return
                elif self.ahead <= 1:
                    # backup
                    if self.forward(self.fromdir-TURNBACK):
                        return
            # you may have got to the destination
            if self.offpos == ROAD_LENGTH+5:
                if self.statics is not None:
                    self.statics.reachDestination(
                        self.tick, self.fromdir, self.turning)
                Car.cars.remove(self)
                self.place.occupied = None
            return

    def paste(self, image: Im.Image, grid: Grid):
        image.paste(self.image, tuple(
            i-round(PIXELSIZE*0.15) for i in grid.getImagePlace(*self.place.coordinate[-1])))
        return image


class CarStream:
    def __init__(self, main, possibility=POSSIBILITY) -> None:
        "Use show() to generate cars"
        "Format your list here like this: ",\
            [[0, 1, FORWARD, 3], [0, TURNLEFT, 2, 3],
             [any, object, NotImplemented], [0, 1, 2, TURNRIGHT]]

        self.main = main
        self.possibility = possibility
        self.getbool = lambda poss: random() < poss

    def show(self):
        for direction in range(4):
            for turning in [0, 1, 3]:
                track = {0: 1, 1: 0, 3: 2}[turning]
                if self.getbool(self.possibility[turning][direction]):
                    if direction is UP:
                        if self.main.g.nodes[(-track, 25)].occupied is not None:
                            self.main.s.stuckstat[turning][direction] += 1
                            self.main.s.trafficJam(direction, turning)
                            continue
                        Car.cars.append(
                            Car(direction, turning, self.main.g.nodes[(-track, 25)], self.main.t, self.main.s))
                    elif direction is DOWN:
                        if self.main.g.nodes[(track, -25)].occupied is not None:
                            self.main.s.stuckstat[turning][direction] += 1
                            self.main.s.trafficJam(direction, turning)
                            continue
                        Car.cars.append(
                            Car(direction, turning, self.main.g.nodes[(track, -25)], self.main.t, self.main.s))
                    elif direction is LEFT:
                        if self.main.g.nodes[(-25, -track)].occupied is not None:
                            self.main.s.stuckstat[turning][direction] += 1
                            self.main.s.trafficJam(direction, turning)
                            continue
                        Car.cars.append(
                            Car(direction, turning, self.main.g.nodes[(-25, -track)], self.main.t, self.main.s))
                    elif direction is RIGHT:
                        if self.main.g.nodes[(25, track)].occupied is not None:
                            self.main.s.stuckstat[turning][direction] += 1
                            self.main.s.trafficJam(direction, turning)
                            continue
                        Car.cars.append(
                            Car(direction, turning, self.main.g.nodes[(25, track)], self.main.t, self.main.s))
                else:
                    if direction is UP:
                        if self.main.s.stuckstat[turning][direction] and self.main.g.nodes[(-track, 25)].occupied is None:
                            self.main.s.stuckstat[turning][direction] -= 1
                            self.main.s.trafficJam(direction, turning)
                            Car.cars.append(
                                Car(direction, turning, self.main.g.nodes[(-track, 25)], self.main.t, self.main.s))
                    elif direction is DOWN:
                        if self.main.s.stuckstat[turning][direction] and self.main.g.nodes[(track, -25)].occupied is None:
                            self.main.s.stuckstat[turning][direction] -= 1
                            self.main.s.trafficJam(direction, turning)
                            Car.cars.append(
                                Car(direction, turning, self.main.g.nodes[(track, -25)], self.main.t, self.main.s))
                    elif direction is LEFT:
                        if self.main.s.stuckstat[turning][direction] and self.main.g.nodes[(-25, -track)].occupied is None:
                            self.main.s.stuckstat[turning][direction] -= 1
                            self.main.s.trafficJam(direction, turning)
                            Car.cars.append(
                                Car(direction, turning, self.main.g.nodes[(-25, -track)], self.main.t, self.main.s))
                    elif direction is RIGHT:
                        if self.main.s.stuckstat[turning][direction] and self.main.g.nodes[(25, track)].occupied is None:
                            self.main.s.stuckstat[turning][direction] -= 1
                            self.main.s.trafficJam(direction, turning)
                            Car.cars.append(
                                Car(direction, turning, self.main.g.nodes[(25, track)], self.main.t, self.main.s))


class Statics:
    def __init__(self, main) -> None:
        "Use mainloop() to show statics"
        "Format your list here like this: ",\
            [[0, 1, FORWARD, 3], [0, TURNLEFT, 2, 3],
             [any, object, NotImplemented], [0, 1, 2, TURNRIGHT]]
        self.main = main
        self.jamRecords = [[0]*4 for i in range(4)]
        self.passingDurations = [[0]*4 for i in range(4)]
        self.passingNumbers = [[0]*4 for i in range(4)]
        self.stuckstat = [[0]*4 for i in range(4)]
        pass

    def trafficJam(self, from_direction: int, turning: int):
        self.jamRecords[turning][from_direction] += 1

    def reachDestination(self, tick: int, from_direction: int, turning: int):
        self.passingDurations[turning][from_direction] += tick
        self.passingNumbers[turning][from_direction] += 1

    def reset(self):
        self.jamRecords = [[0]*4 for i in range(4)]
        self.passingDurations = [[0]*4 for i in range(4)]
        self.passingNumbers = [[0]*4 for i in range(4)]
        self.stuckstat = [[0]*4 for i in range(4)]

    def report(self) -> str:
        tn_to_dic = {1: 1, 3: 3, 2: 0, 0: 2}
        out = ""

        out += "Passing Effectiency Details:\n\n"
        for fmdr in range(4):
            for tn in [0, 1, 3]:
                temp = DIRECTION_DICT[fmdr]+"->" + \
                    DIRECTION_DICT[(fmdr-tn_to_dic[tn]) % 4]+": "
                while len(temp) < 20:
                    temp += " "
                try:
                    temp += str(round(self.passingDurations[tn][fmdr] /
                                      self.passingNumbers[tn][fmdr], 2))+" ticks\n"
                except ZeroDivisionError:
                    temp += "-- ticks\n"
                out += temp
            out += "\n"

        out += "Traffic Jam Details:\n\n"
        for fmdr in range(4):
            for tn in [0, 1, 3]:
                temp = DIRECTION_DICT[fmdr]+"->" + \
                    DIRECTION_DICT[(fmdr-tn_to_dic[tn]) % 4]+": "
                while len(temp) < 30:
                    temp += " "
                temp += str(self.jamRecords[tn][fmdr])+" ticks"
                while len(temp) < 40:
                    temp += " "
                temp += str(self.stuckstat[tn]
                            [fmdr]) + " cars in queue\n"
                out += temp
            out += "\n"

        return out

    def mainloop(self):
        roll = 0
        text = self.report()+"\n---The end, press any letter key to exit---"
        linenum = text.count("\n")+1
        gap = 32

        image = Im.new('RGBA', (self.main.screensize[0], gap*linenum),
                       (153, 217, 234, 255))
        Imd.Draw(image).text((0, 0), text, (0, 0, 0, 255), FONT_SMALLER)
        surf = img2suf(image)

        self.mainloop_loop = True

        def back():
            self.mainloop_loop = False

        buttonsize = (300, 100)
        button = Button(self.main, *(self.main.screensize[0]-buttonsize[0], 0),
                        *buttonsize, "\n         <<<BACK", (255, 237, 216, 255), func=back)

        while self.mainloop_loop:
            self.main.clock.tick(FPS)
            self.main.window.blit(self.main.background, (0, 0))
            self.main.window.blit(surf, (0, -roll*gap))
            button.show()

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.main.quit()
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_UP:
                        if roll:
                            roll -= 1
                    elif event.key == pg.K_DOWN:
                        if roll < linenum-2:
                            roll += 1
                    elif event.key in range(97, 97+26):
                        return
                    elif event.key in [pg.K_ESCAPE, pg.K_RETURN]:
                        return
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == 4:
                        if roll:
                            roll -= 1
                    elif event.button == 5:
                        if roll < linenum-2:
                            roll += 1
                    button.dealevent(event)

            pg.display.update()


class Button:
    def __init__(self, main, placex: int, placey: int, sizex: int, sizey: int, text="",
                 backgroundcolor=(255, 255, 255, 127), textcolor=(0, 0, 0, 255),
                 func=lambda *args: None, funcargs=(), funckwargs={}):
        self.main = main
        self.place = placex, placey
        self.size = sizex, sizey
        self.text = text
        self.func = lambda: func(*funcargs, **funckwargs)

        self.image = Im.new("RGBA", self.size, backgroundcolor)
        Imd.Draw(self.image).text((0, 0), self.text, textcolor, FONT_SMALLER)
        self.surface = img2suf(self.image)
        pass

    def dealevent(self, event: pg.event.Event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                msx, msy = pg.mouse.get_pos()
                if self.place[0] <= msx < self.place[0]+self.size[0] \
                        and self.place[1] <= msy < self.place[1]+self.size[1]:
                    self.func()
                    return True
        return False

    def show(self):
        self.main.window.blit(self.surface, self.place)


class Slider:
    def __init__(self, main, trafficlight: TrafficLight,
                 direction: int, turning: int, height=100, text="LightX", placey=0,
                 backgroundcolor=(255, 157, 216, 255), textcolor=(0, 0, 0, 255),
                 slidercolor=(127, 127, 127, 216), emphasiscolor=(255, 160, 100, 255),
                 bordercolor=(216, 0, 0, 255), borderemphasiscolor=(255, 216, 127, 255),
                 borderwidth=3, gapx=50, sliderwidth=6, sliderheight=40):
        self.main = main
        self.minimum = 0
        self.maximum = trafficlight.timeperiod
        self.trafficlight = trafficlight
        self.direction = direction
        self.turning = turning
        self.height = height
        self.text = text
        self.placey = placey
        self.gapx = gapx
        self.value = self.getvalue()
        self.chosen0 = False
        self.chosen1 = False
        self.mousedown = False

        self.size = self.main.screensize[0], height

        self.image_0 = Im.new('RGBA', self.size, backgroundcolor)
        dw = Imd.Draw(self.image_0)
        dw.rectangle((0, 0, self.size[0]-1, self.size[1]-1),
                     (0, 0, 0, 0), bordercolor, borderwidth)
        dw.line((self.gapx, round(0.6*self.height),
                 self.size[0]-self.gapx, round(0.6*self.height)),
                fill=(0, 0, 0, 255), width=borderwidth)
        dw.text((0, 0), text, fill=textcolor, font=FONT_SMALLER)
        self.surface_0 = img2suf(self.image_0)

        self.image_1 = Im.new('RGBA', self.size, emphasiscolor)
        dw = Imd.Draw(self.image_1)
        dw.rectangle((0, 0, self.size[0]-1, self.size[1]-1),
                     (0, 0, 0, 0), borderemphasiscolor, borderwidth)
        dw.line((self.gapx, round(0.6*self.height),
                 self.size[0]-self.gapx, round(0.6*self.height)),
                fill=(0, 0, 0, 255), width=borderwidth)
        dw.text((0, 0), text, fill=textcolor, font=FONT_SMALLER)
        self.surface_1 = img2suf(self.image_1)

        self.image_slider0 = Im.new(
            'RGBA', (sliderwidth, sliderheight), slidercolor)
        self.surface_slider0 = img2suf(self.image_slider0)

        self.image_slider1 = deepcopy(self.image_slider0)
        Imd.Draw(self.image_slider1).rectangle(
            (0, 0, self.image_slider1.size[0]-1, self.image_slider1.size[1]-1),
            outline=borderemphasiscolor)
        self.surface_slider1 = img2suf(self.image_slider1)
        pass

    def getvalue(self):
        if self.turning == TURNLEFT:
            return self.trafficlight.leftSignals[self.direction]
        elif self.turning == FORWARD:
            return self.trafficlight.straightSignals[self.direction]
        elif self.turning == TURNRIGHT:
            return self.trafficlight.rightSignals[self.direction]
        else:
            return (None, None)

    def setvalue(self, value: tuple):
        if self.turning == TURNLEFT:
            self.trafficlight.leftSignals[self.direction] = value
        elif self.turning == FORWARD:
            self.trafficlight.straightSignals[self.direction] = value
        elif self.turning == TURNRIGHT:
            self.trafficlight.rightSignals[self.direction] = value

    def value2sliderx(self, value: tuple):
        return tuple(round(self.gapx+(self.size[0]-2*self.gapx)/(self.maximum-self.minimum)*(i-self.minimum)) for i in value)

    def sliderx2value(self, x: int):
        if x < self.gapx:
            return self.minimum
        elif x >= self.size[0]-self.gapx:
            return self.maximum
        return round(self.minimum+(self.maximum-self.minimum)/(self.size[0]-2*self.gapx)*(x-self.gapx))

    def dealevent(self, event, offset):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                mousepos = pg.mouse.get_pos()
                y = self.placey + offset
                if y <= mousepos[1] < y+self.height:
                    sliderxs = self.value2sliderx(self.value)
                    # to choose a slider
                    if not (self.chosen0 or self.chosen1):
                        if abs(mousepos[0] - sliderxs[0]) <= abs(mousepos[0] - sliderxs[1]):
                            self.chosen0 = True
                        else:
                            self.chosen1 = True
                    elif self.chosen0 and not self.chosen1:
                        if abs(mousepos[0] - sliderxs[0]) <= abs(mousepos[0] - sliderxs[1]):
                            self.mousedown = True
                        else:
                            self.chosen1 = True
                            self.chosen0 = False
                    elif not self.chosen0 and self.chosen1:
                        if abs(mousepos[0] - sliderxs[0]) > abs(mousepos[0] - sliderxs[1]):
                            self.mousedown = True
                        else:
                            self.chosen0 = True
                            self.chosen1 = False
                else:
                    self.chosen0 = False
                    self.chosen1 = False

        elif event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                self.mousedown = False
        elif (self.chosen0 or self.chosen1) and event.type == pg.KEYDOWN:
            if event.key == pg.K_LEFT:
                if self.chosen0:
                    if self.value[0]:
                        self.value = self.value[0]-1, self.value[1]
                elif self.chosen1:
                    if self.value[1]:
                        self.value = self.value[0], self.value[1]-1
            if event.key == pg.K_RIGHT:
                if self.chosen0:
                    if self.value[0] < self.maximum:
                        self.value = self.value[0]+1, self.value[1]
                elif self.chosen1:
                    if self.value[1] < self.maximum:
                        self.value = self.value[0], self.value[1]+1

    def show(self, offset):
        # change
        self.maximum = self.trafficlight.timeperiod
        if self.mousedown:
            mouseposx = pg.mouse.get_pos()[0]
            if self.chosen0:
                self.value = self.sliderx2value(mouseposx), self.value[1]
            elif self.chosen1:
                self.value = self.value[0], self.sliderx2value(mouseposx)

        # show
        y = self.placey + offset
        if y < -self.height or y > self.main.screensize[1]:
            return
        xs = self.value2sliderx(self.value)
        ys = y+round(0.6*self.height)-self.image_slider0.size[1]//2
        if not (self.chosen0 or self.chosen1):
            self.main.window.blit(self.surface_0, (0, y))
            self.main.window.blit(self.surface_slider0, (xs[0], ys))
            self.main.window.blit(self.surface_slider0, (xs[1], ys))
        elif not self.chosen0 and self.chosen1:
            self.main.window.blit(self.surface_1, (0, y))
            self.main.window.blit(self.surface_slider0, (xs[0], ys))
            self.main.window.blit(self.surface_slider1, (xs[1], ys))
        elif self.chosen0 and not self.chosen1:
            self.main.window.blit(self.surface_1, (0, y))
            self.main.window.blit(self.surface_slider1, (xs[0], ys))
            self.main.window.blit(self.surface_slider0, (xs[1], ys))
        self.main.window.blit(
            img2suf(make_text(f"{self.value}")), (self.size[0]-150, ys-30))
        pass


class TrafficLightController:
    def __init__(self, main, trafficlight: TrafficLight) -> None:
        self.main = main
        self.trafficlight = trafficlight
        self.sliders = []
        placey = 0
        tn_to_dic = {1: 1, 3: 3, 2: 0, 0: 2}
        for direction in range(4):
            for turning in [0, 1, 3]:
                self.sliders.append(Slider(
                    self.main, self.trafficlight, direction, turning, placey=placey,
                    text=f"{DIRECTION_DICT[direction]}2{DIRECTION_DICT[(direction-tn_to_dic[turning]) % 4]}"))
                placey += 100
        self.mousedown = False
        self.mouseposoffset = None

    def mainloop(self):
        roll = 0
        self.mainloop_loop = True
        background = img2suf(Im.new('RGBA', self.main.screensize,
                                    (255, 197, 216, 255)))

        def back():
            self.mainloop_loop = False
            for slider in self.sliders:
                slider.setvalue(slider.value)
                self.mousedown = False

        buttonsize = (300, 100)
        button = Button(self.main, *(self.main.screensize[0]-buttonsize[0],
                                     self.main.screensize[1]-buttonsize[1]),
                        *buttonsize, "\n         <<<BACK", (255, 237, 216, 255), func=back)

        while self.mainloop_loop:
            self.main.clock.tick(FPS)
            self.main.window.blit(background, (0, 0))
            for slider in self.sliders:
                slider.show(-roll)
            button.show()

            if self.mousedown:
                roll = -pg.mouse.get_pos()[1]+self.mouseposoffset
                if roll < 0:
                    roll = 0

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.main.quit()
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_UP:
                        if roll:
                            roll -= 50
                    elif event.key == pg.K_DOWN:
                        if roll < 650:
                            roll += 50
                    elif event.key in range(97, 97+26):
                        return
                    elif event.key in [pg.K_ESCAPE, pg.K_RETURN]:
                        return
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.mousedown = True
                        self.mouseposoffset = pg.mouse.get_pos()[1]+roll
                    elif event.button == 4:
                        if roll:
                            roll -= 15
                    elif event.button == 5:
                        if roll < 650:
                            roll += 15
                    button.dealevent(event)
                elif event.type == pg.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.mousedown = False
                        self.mouseposoffset = None
                for slider in self.sliders:
                    slider.dealevent(event, -roll)

            pg.display.update()


class Slider2:
    def __init__(self, main, carstream: CarStream,
                 direction: int, turning: int, height=100, text="StreamX", placey=0,
                 backgroundcolor=(140, 255, 210, 255), textcolor=(0, 0, 0, 255),
                 slidercolor=(127, 127, 127, 216), emphasiscolor=(255, 160, 100, 255),
                 bordercolor=(0, 127, 0, 255), borderemphasiscolor=(255, 127, 0, 255),
                 borderwidth=3, gapx=50, sliderwidth=6, sliderheight=40):
        self.main = main
        self.minimum = 0
        self.maximum = 1
        self.carstream = carstream
        self.direction = direction
        self.turning = turning
        self.height = height
        self.text = text
        self.placey = placey
        self.gapx = gapx
        self.value = self.getvalue()
        self.chosen = False
        self.mousedown = False

        self.size = self.main.screensize[0], height

        self.image_0 = Im.new('RGBA', self.size, backgroundcolor)
        dw = Imd.Draw(self.image_0)
        dw.rectangle((0, 0, self.size[0]-1, self.size[1]-1),
                     (0, 0, 0, 0), bordercolor, borderwidth)
        dw.line((self.gapx, round(0.6*self.height),
                 self.size[0]-self.gapx, round(0.6*self.height)),
                fill=(0, 0, 0, 255), width=borderwidth)
        dw.text((0, 0), text, fill=textcolor, font=FONT_SMALLER)
        self.surface_0 = img2suf(self.image_0)

        self.image_1 = Im.new('RGBA', self.size, emphasiscolor)
        dw = Imd.Draw(self.image_1)
        dw.rectangle((0, 0, self.size[0]-1, self.size[1]-1),
                     (0, 0, 0, 0), borderemphasiscolor, borderwidth)
        dw.line((self.gapx, round(0.6*self.height),
                 self.size[0]-self.gapx, round(0.6*self.height)),
                fill=(0, 0, 0, 255), width=borderwidth)
        dw.text((0, 0), text, fill=textcolor, font=FONT_SMALLER)
        self.surface_1 = img2suf(self.image_1)

        self.image_slider0 = Im.new(
            'RGBA', (sliderwidth, sliderheight), slidercolor)
        self.surface_slider0 = img2suf(self.image_slider0)

        self.image_slider1 = deepcopy(self.image_slider0)
        Imd.Draw(self.image_slider1).rectangle(
            (0, 0, self.image_slider1.size[0]-1, self.image_slider1.size[1]-1),
            outline=borderemphasiscolor)
        self.surface_slider1 = img2suf(self.image_slider1)
        pass

    def getvalue(self):
        return self.carstream.possibility[self.turning][self.direction]

    def setvalue(self, value: float):
        self.carstream.possibility[self.turning][self.direction] = value

    def value2sliderx(self, value: float):
        return round(self.gapx+(self.size[0]-2*self.gapx)/(self.maximum-self.minimum)*(value-self.minimum))

    def sliderx2value(self, x: int):
        if x < self.gapx:
            return self.minimum
        elif x >= self.size[0]-self.gapx:
            return self.maximum
        return round(self.minimum+(self.maximum-self.minimum)/(self.size[0]-2*self.gapx)*(x-self.gapx), 3)

    def dealevent(self, event, offset):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                mousepos = pg.mouse.get_pos()
                y = self.placey + offset
                if y <= mousepos[1] < y+self.height:
                    if not self.chosen:
                        self.chosen = True
                    else:
                        self.mousedown = True
                else:
                    self.chosen = False

        elif event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                self.mousedown = False
        elif self.chosen and event.type == pg.KEYDOWN:
            if event.key == pg.K_LEFT:
                self.value -= 0.002
                self.value = round(self.value, 3)
                if self.value < self.minimum:
                    self.value = self.minimum
            if event.key == pg.K_RIGHT:
                self.value += 0.002
                self.value = round(self.value, 3)
                if self.value > self.maximum:
                    self.value = self.maximum

    def show(self, offset):
        # change
        if self.mousedown:
            mouseposx = pg.mouse.get_pos()[0]
            if self.chosen:
                self.value = self.sliderx2value(mouseposx)

        # show
        y = self.placey + offset
        if y < -self.height or y > self.main.screensize[1]:
            return
        xs = self.value2sliderx(self.value)
        ys = y+round(0.6*self.height)-self.image_slider0.size[1]//2
        if not self.chosen:
            self.main.window.blit(self.surface_0, (0, y))
            self.main.window.blit(self.surface_slider0, (xs, ys))
        else:
            self.main.window.blit(self.surface_1, (0, y))
            self.main.window.blit(self.surface_slider1, (xs, ys))
        self.main.window.blit(
            img2suf(make_text(f"{self.value}")), (self.size[0]-150, ys-30))
        pass


class CarController:
    def __init__(self, main, carstream: CarStream):
        self.main = main
        self.carstream = carstream
        self.sliders = []
        placey = 0
        tn_to_dic = {1: 1, 3: 3, 2: 0, 0: 2}
        for direction in range(4):
            for turning in [0, 1, 3]:
                self.sliders.append(Slider2(
                    self.main, self.carstream, direction, turning, placey=placey,
                    text=f"{DIRECTION_DICT[direction]}2{DIRECTION_DICT[(direction-tn_to_dic[turning]) % 4]}"))
                placey += 100
        self.mousedown = False
        self.mouseposoffset = None

    def mainloop(self):
        roll = 0
        self.mainloop_loop = True
        background = img2suf(Im.new('RGBA', self.main.screensize,
                                    (BACKGROUND_COLOR[0], BACKGROUND_COLOR[2], BACKGROUND_COLOR[1], 255)))

        def back():
            self.mainloop_loop = False
            for slider in self.sliders:
                slider.setvalue(slider.value)
                self.mousedown = False

        buttonsize = (300, 100)
        button = Button(self.main, *(self.main.screensize[0]-buttonsize[0],
                                     self.main.screensize[1]-buttonsize[1]),
                        *buttonsize, "\n         <<<BACK", (255, 237, 216, 255), func=back)

        while self.mainloop_loop:
            self.main.clock.tick(FPS)
            self.main.window.blit(background, (0, 0))
            for slider in self.sliders:
                slider.show(-roll)
            button.show()

            if self.mousedown:
                roll = -pg.mouse.get_pos()[1]+self.mouseposoffset
                if roll < 0:
                    roll = 0

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.main.quit()
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_UP:
                        roll -= 50
                        if roll < 0:
                            roll = 0
                    elif event.key == pg.K_DOWN:
                        if roll < 650:
                            roll += 50
                    elif event.key in range(97, 97+26):
                        return
                    elif event.key in [pg.K_ESCAPE, pg.K_RETURN]:
                        return
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.mousedown = True
                        self.mouseposoffset = pg.mouse.get_pos()[1]+roll
                    elif event.button == 4:
                        roll -= 15
                        if roll < 0:
                            roll = 0
                    elif event.button == 5:
                        if roll < 650:
                            roll += 15
                    button.dealevent(event)
                elif event.type == pg.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.mousedown = False
                        self.mouseposoffset = None
                for slider in self.sliders:
                    slider.dealevent(event, -roll)

            pg.display.update()


class TimeFlowController:
    "Controls traffic loop_time, fps , lag_time, straight_classic"

    def __init__(self, main):
        self.main = main
        self.buttons = []
        self.texts = []
        self.textpos = []
        self.values = self.getvalue()

        self.texts.append(img2suf(make_text("TimeFlow Controller",
                                            size=(600, 100), color=(255,)*4, font=FONT)))
        self.textpos.append((0, 0))

        self.texts.append(img2suf(make_text(
            "TimePeriod of TrafficLights(tick)", size=(500, 50), color=(255,)*4)))
        self.textpos.append((0, 100))

        self.texts.append(img2suf(make_text(
            "Frequency of Screen Refresh(Hz)", size=(500, 50), color=(255,)*4)))
        self.textpos.append((0, 200))

        self.texts.append(img2suf(make_text(
            "Frequency of Simulation(tick/s)", size=(500, 50), color=(255,)*4)))
        self.textpos.append((0, 300))

        self.texts.append(img2suf(make_text(
            "Straight Light Classic", size=(500, 50), color=(255,)*4)))
        self.textpos.append((0, 400))

        def v0m(): self.values[0] = max(16, self.values[0]-1)
        self.buttons.append(Button(self.main, 500, 100, 50, 50, "-", func=v0m,
                                   textcolor=(255,)*4, backgroundcolor=(29, 152, 66, 127)))

        def v0p(): self.values[0] += 1
        self.buttons.append(Button(self.main, 570, 100, 50, 50, "+", func=v0p,
                                   textcolor=(255,)*4, backgroundcolor=(155, 0, 0, 127)))

        def v1m(): self.values[1] = max(1, self.values[1]-1)
        self.buttons.append(Button(self.main, 500, 200, 50, 50, "-", func=v1m,
                                   textcolor=(255,)*4, backgroundcolor=(29, 152, 66, 127)))

        def v1p(): self.values[1] += 1
        self.buttons.append(Button(self.main, 570, 200, 50, 50, "+", func=v1p,
                                   textcolor=(255,)*4, backgroundcolor=(155, 0, 0, 127)))

        def v2m(): self.values[2] += 1
        self.buttons.append(Button(self.main, 500, 300, 50, 50, "-", func=v2m,
                                   textcolor=(255,)*4, backgroundcolor=(29, 152, 66, 127)))

        def v2p(): self.values[2] = max(1, self.values[2]-1)
        self.buttons.append(Button(self.main, 570, 300, 50, 50, "+", func=v2p,
                                   textcolor=(255,)*4, backgroundcolor=(155, 0, 0, 127)))

        def v3m(): self.values[3] = False
        self.buttons.append(Button(self.main, 500, 400, 50, 50, "-", func=v3m,
                                   textcolor=(255,)*4, backgroundcolor=(29, 152, 66, 127)))

        def v3p(): self.values[3] = True
        self.buttons.append(Button(self.main, 570, 400, 50, 50, "+", func=v3p,
                                   textcolor=(255,)*4, backgroundcolor=(155, 0, 0, 127)))

        self.buttons.append(Button(self.main, 370, 500, 200,
                            100, "\n  BACK", func=self.savesetting, textcolor=(255,)*4,))

        self.loop = True
        pass

    def getvalue(self):
        return deepcopy([self.main.t.timeperiod, FPS, LAG_TIME, STRAIGHT_CLASSIC])

    def setvalue(self, values: list):
        global FPS, LAG_TIME, STRAIGHT_CLASSIC
        self.main.t.timeperiod = values[0]
        FPS = values[1]
        LAG_TIME = values[2]
        STRAIGHT_CLASSIC = values[3]

    def show(self):
        for i in range(len(self.texts)):
            self.main.window.blit(self.texts[i], self.textpos[i])
        for button in self.buttons:
            button.show()

        self.main.window.blit(img2suf(make_text(
            str(self.values[0]), color=(255,)*4)), (650, 100))
        self.main.window.blit(img2suf(make_text(
            str(self.values[1]), color=(255,)*4)), (650, 200))
        self.main.window.blit(img2suf(make_text(
            str(round(self.values[1]/self.values[2], 3)),
            color=(255,)*4)), (650, 300))
        self.main.window.blit(img2suf(make_text(
            str(self.values[3]), color=(255,)*4)), (650, 400))

    def savesetting(self):
        Lpic = Im.new(
            "RGBA", (self.main.screensize[0]//2, self.main.screensize[1]), (0, 127, 0, 128))
        Ldraw = Imd.Draw(Lpic)
        Ldraw.text((0, self.main.screensize[1]//2-180),
                   "SAVE", fill=(255,)*4, font=FONT)
        Ldraw.text((0, self.main.screensize[1]//2-100),
                   "Press any key in\n the left half keyboard",
                   fill=(255,)*4, font=FONT_SMALLER)
        LSurf = img2suf(Lpic)

        Rpic = Im.new(
            "RGBA", (self.main.screensize[0]//2, self.main.screensize[1]), (127, 127, 0, 128))
        Rdraw = Imd.Draw(Rpic)
        Rdraw.text((0, self.main.screensize[1]//2-180),
                   "DON'T SAVE", fill=(255,)*4, font=FONT)
        Rdraw.text((0, self.main.screensize[1]//2-100),
                   "Press any key in\n the right half keyboard",
                   fill=(255,)*4, font=FONT_SMALLER)
        RSurf = img2suf(Rpic)

        self.main.window.blit(LSurf, (0, 0))
        self.main.window.blit(RSurf, (self.main.screensize[0]//2, 0))
        pg.display.update()

        while True:
            self.main.clock.tick(FPS)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.main.quit()
                if event.type == pg.KEYDOWN:
                    if event.key in [ord(i) for i in "`12345qwertasdfgzxcv"]\
                            + [pg.K_LSHIFT, pg.K_TAB]:
                        self.setvalue(self.values)
                        self.loop = False
                        return True
                    elif event.key in [ord(i) for i in "7890-=uiop[]\\hjkl;'nm,./"]\
                            + [pg.K_RSHIFT, pg.K_BACKSPACE]:
                        self.loop = False
                        return False
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if event.button in [1, 2, 3]:
                        if pg.mouse.get_pos()[0] < self.main.screensize[0]//2:
                            self.setvalue(self.values)
                            self.loop = False
                            return True
                        else:
                            self.loop = False
                            return False

        pass

    def mainloop(self):
        self.extracover = img2suf(
            Im.new('RGBA', self.main.screensize, (0, 0, 0, 100)))
        self.loop = True
        while self.loop:
            self.main.clock.tick(FPS)
            self.main.window.blit(self.main.background, (0, 0))
            self.main.window.blit(self.extracover, (0, 0))
            self.show()
            pg.display.update()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.main.quit()
                if event.type == pg.KEYDOWN:
                    if event.key in range(97, 97+26):
                        self.savesetting()
                    elif event.key in [pg.K_ESCAPE, pg.K_RETURN]:
                        self.savesetting()
                for button in self.buttons:
                    button.dealevent(event)


class Extension:
    def __init__(self, main, light: TrafficLight) -> None:
        self.mainplace = (MAINSIZE, 0)
        self.size = (EXTENTION_WIDTH, MAINSIZE)
        self.surface = None
        self.main = main
        self.light = light

        self.image = Im.new("RGBA", self.size, (255, 255, 255, 127))
        self.draw = Imd.Draw(self.image)
        self.draw.text((0, 0), "SIDE\nPANEL", (0, 0, 0, 216), FONT)

        self.buttons = []
        self.buttons.append(
            Button(self.main, MAINSIZE+7, 130, EXTENTION_WIDTH-2*7, 40,
                   "     PAUSE(P)", func=self.main.pause))
        self.buttons.append(
            Button(self.main, MAINSIZE+7, 180, EXTENTION_WIDTH-2*7, 40,
                   "     CLEAR(C)", func=self.main.restart))
        self.buttons.append(
            Button(self.main, MAINSIZE+7, 230, EXTENTION_WIDTH-2*7, 40,
                   "   STATICS(S)", func=self.main.s.mainloop))
        self.buttons.append(
            Button(self.main, MAINSIZE+7, 280, EXTENTION_WIDTH-2*7, 80,
                   "   SETTING(L)\n   TrafficLights",
                   func=self.main.trafficlightcontroller.mainloop))
        self.buttons.append(
            Button(self.main, MAINSIZE+7, 370, EXTENTION_WIDTH-2*7, 80,
                   "   SETTING(R)\n   CarStream",
                   func=self.main.carcontroller.mainloop))
        self.buttons.append(
            Button(self.main, MAINSIZE+7, 560, EXTENTION_WIDTH-2*7, 40,
                   "   MORE...", func=Caution_and_Warn,
                   funcargs=(self.main, "Not available now!")))
        self.buttons.append(
            Button(self.main, MAINSIZE+7, 460, EXTENTION_WIDTH-2*7, 40,
                   "   TIMEFLOW(T)", func=self.main.timeflowcontroller.mainloop))
        self.buttons.append(
            Button(self.main, MAINSIZE+7, 510, EXTENTION_WIDTH-2*7, 40,
                   "   QUIT(Q)", func=self.main.quit2))

    def dealevent(self, event: pg.event.Event) -> bool:
        for button in self.buttons:
            if button.dealevent(event):
                return True
        if event.type == pg.KEYDOWN:
            if event.key in [pg.K_p]:
                self.main.pause()
                return True
            elif event.key in [pg.K_c]:
                self.main.restart()
                return True
            elif event.key in [pg.K_q, pg.K_ESCAPE]:
                self.main.quit2()
                return True
            elif event.key in [pg.K_s]:
                self.main.s.mainloop()
            elif event.key in [pg.K_l]:
                self.main.trafficlightcontroller.mainloop()
            elif event.key in [pg.K_r]:
                self.main.carcontroller.mainloop()
            elif event.key in [pg.K_t]:
                self.main.timeflowcontroller.mainloop()
        return False

    def show(self,  refresh=True):
        if refresh:
            self.surface = img2suf(self.image)
        self.main.window.blit(self.surface, self.mainplace)
        for button in self.buttons:
            button.show()


class Caution_and_Warn:
    def __init__(self, main, text) -> None:
        image = Im.new('RGBA', main.screensize, (0, 0, 0, 63))
        Imd.Draw(image).text((main.screensize[0]//2-320, main.screensize[1]//2-80),
                             text, (216,)*4, font=FONT, align='center')
        Imd.Draw(image).text((main.screensize[0]//2-320, main.screensize[1]-80),
                             "Click anywhere to continue...\nPress any key to continue...",
                             (216,)*4, font=FONT_SMALLER, align='center')
        image = img2suf(image)
        main.window.blit(image, (0, 0))
        pg.display.update()

        while True:
            main.clock.tick(FPS)

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    main.quit()
                elif event.type == pg.KEYDOWN:
                    return
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        return


class BackGroundClass:
    def __init__(self, screensize):
        self.color0 = (153, 217, 234, 255)
        self.color1 = (255, 163, 60, 255)
        self.color2 = (36, 55, 81, 255)
        self.color = (153, 217, 234, 255)
        self.size = screensize
        self.tick = 0

    @staticmethod
    def mix(color1, color2, portion: float):
        if portion <= 0:
            portion = 0
        elif portion >= 1:
            portion = 1
        return (round(color1[0]*(1-portion)+color2[0]*portion),
                round(color1[1]*(1-portion)+color2[1]*portion),
                round(color1[2]*(1-portion)+color2[2]*portion),
                round(color1[3]*(1-portion)+color2[3]*portion))

    def getcolor(self):
        tick = (self.tick % 4800)
        if 0 <= tick < 1200:
            self.color = self.color0
        elif 1200 <= tick < 1800:
            self.color = BackGroundClass.mix(
                self.color0, self.color1, (tick-1200)/600)
        elif 1800 <= tick < 2400:
            self.color = BackGroundClass.mix(
                self.color1, self.color2, (tick-1800)/600)
        elif 2400 <= tick < 3600:
            self.color = self.color2
        elif 3600 <= tick < 4200:
            self.color = BackGroundClass.mix(
                self.color2, self.color1, (tick-3600)/600)
        elif 4200 <= tick < 4800:
            self.color = BackGroundClass.mix(
                self.color1, self.color0, (tick-4200)/600)

    def getBackgroundSurface(self):
        self.getcolor()
        self.tick += 1
        return img2suf(Im.new('RGBA', self.size, self.color))


class Main:
    def __init__(self) -> None:
        self.g = Grid()
        self.t = TrafficLight()
        self.s = Statics(self)

        self.screensize = (MAINSIZE+EXTENTION_WIDTH, MAINSIZE)
        self.b = BackGroundClass(self.screensize)

        self.window = pg.display.set_mode(self.screensize)
        pg.display.set_caption("Simulation")
        pg.display.set_icon(img2suf(self.t.paint3(UP, 20)))
        self.clock = pg.time.Clock()
        self.background = self.b.getBackgroundSurface()

        self.light3sizeget = lambda size: (size*3+round(size*0.05)*2, size*3)

        self.carstream = CarStream(self)
        self.trafficlightcontroller = TrafficLightController(self, self.t)
        self.carcontroller = CarController(self, self.carstream)
        self.timeflowcontroller = TimeFlowController(self)
        self.extension = Extension(self, self.t)

    def quit(self):
        pg.quit()
        exit()

    def quit2(self, ticking=10):
        Lpic = Im.new(
            "RGBA", (self.screensize[0]//2, self.screensize[1]), (127, 0, 0, 255))
        Ldraw = Imd.Draw(Lpic)
        Ldraw.text((0, self.screensize[1]//2-180),
                   "QUIT", fill=(255,)*4, font=FONT)
        Ldraw.text((0, self.screensize[1]//2-100),
                   "Press any key in\n the left half keyboard, \nOr just wait...",
                   fill=(255,)*4, font=FONT_SMALLER)
        LSurf = img2suf(Lpic)

        Rpic = Im.new(
            "RGBA", (self.screensize[0]//2, self.screensize[1]), (0, 127, 0, 8))
        Rdraw = Imd.Draw(Rpic)
        Rdraw.text((0, self.screensize[1]//2-180),
                   "CANCEL", fill=(255,)*4, font=FONT)
        Rdraw.text((0, self.screensize[1]//2-100),
                   "Press any key in\n the right half keyboard",
                   fill=(255,)*4, font=FONT_SMALLER)
        RSurf = img2suf(Rpic)

        while True:
            self.clock.tick(FPS)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.quit()
                if event.type == pg.KEYDOWN:
                    if event.key in [ord(i) for i in "`12345qwertasdfgzxcv"]\
                            + [pg.K_LSHIFT, pg.K_TAB]:
                        self.quit()
                    elif event.key in [ord(i) for i in "7890-=uiop[]\\hjkl;'nm,./"]\
                            + [pg.K_RSHIFT, pg.K_BACKSPACE]:
                        return
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if event.button in [1, 2, 3]:
                        if pg.mouse.get_pos()[0] < self.screensize[0]//2:
                            self.quit()
                        else:
                            return

            ticking -= 1/FPS
            if ticking <= 0:
                self.quit()

            countdownpic = TrafficLight.paintdigit(
                int(ticking), size=120, width=16)
            countdownsurf = img2suf(countdownpic)

            self.window.blit(LSurf, (0, 0))
            self.window.blit(RSurf, (self.screensize[0]//2, 0))
            self.window.blit(countdownsurf, (20, 320))
            pg.display.update()

        return

    def pause(self):
        image = Im.new('RGBA', self.screensize, (0, 0, 0, 63))
        Imd.Draw(image).text((self.screensize[0]//2-320, self.screensize[1]//2-80),
                             "PAUSED!\nPress(P/SPACE) to continue",
                             (216,)*4, font=FONT, align='center')
        image = img2suf(image)
        self.window.blit(image, (0, 0))

        self.pause_loop = True

        def resume():
            self.pause_loop = False
        button = Button(self, MAINSIZE+7, 130, EXTENTION_WIDTH-2*7, 40,
                        "    RESUME(P)", func=resume, backgroundcolor=(216, 216, 216, 255))
        button.show()
        pg.display.update()

        while self.pause_loop:
            self.clock.tick(FPS)

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.quit()
                elif event.type == pg.KEYDOWN:
                    if event.key in [pg.K_p, pg.K_SPACE, pg.K_ESCAPE]:
                        return
                button.dealevent(event)

    def restart(self):
        Car.cars.clear()
        self.s.reset()
        for position in self.g.nodes:
            self.g.nodes[position].occupied = None

    def mainloop(self):
        tick = 0
        while True:
            self.clock.tick(FPS)

            self.background = self.b.getBackgroundSurface()
            self.window.blit(self.background, (0, 0))
            grid_im = deepcopy(self.g.image)
            for c in Car.cars:
                c.paste(grid_im, self.g)
            self.window.blit(img2suf(grid_im), (0, 0))
            self.window.blit(img2suf(self.t.paint3(UP, 41)), (340, 0))
            self.window.blit(img2suf(self.t.paint3(LEFT, 41)), (0, 150))
            self.window.blit(img2suf(self.t.paint3(RIGHT, 41)), (480, 150))
            self.window.blit(img2suf(self.t.paint3(DOWN, 41)), (340, 480))
            self.window.blit(
                img2suf(self.t.painttime(UP, FORWARD, 25)), (480, 10))
            self.window.blit(
                img2suf(self.t.painttime(RIGHT, FORWARD, 25)), (540, 350))

            self.extension.show(self.window)

            if not tick % LAG_TIME:
                self.t.mainoperate()
                for c in Car.cars:
                    c.move()

                # Generator
                self.carstream.show()

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.quit()
                self.extension.dealevent(event)

            pg.display.update()
            tick += 1

if __name__ == "__main__":
    Main().mainloop()
