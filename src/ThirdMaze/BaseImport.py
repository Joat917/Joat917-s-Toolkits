
from random import randint, choice, random
from sys import exit, argv
from cmath import phase, polar
from math import cos, sin, radians, sqrt
from traceback import print_exc

from PIL import Image as Im, ImageDraw as Imd, ImageFont as Imf
import os, sys
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame as pg

pg.display.init()
if 0:
    root = pg.display.set_mode(flags=pg.FULLSCREEN)
    SCREEN_SIZE = pg.display.get_window_size()
else:
    SCREEN_SIZE = (1200, 600)
    root = pg.display.set_mode(SCREEN_SIZE)

ZOOMMAX = 60
FPS = 20

ROLE_HORIZON = 5
TORCH_RANGE = 7

FONTSIZE = 24
HPBAR_SIZE = [(40, 40), (200, 20)]
ITEMBAR_SIZE = [(800, 150), (60, 60)]

ROCKER_RADIUS = 50
ROCKER_HANDLE_RADIUS = 20

MINI_HPBAR_SIZE = (50, 10)


R = 0b100
TR = 0b110
TL = 0b010
L = 0b011
BL = 0b001
BR = 0b101
SQRT3 = 1.7320508075688772

BACKGROUND = Im.new('RGBA', SCREEN_SIZE, (128, 0, 0, 255))


def im2pg(im: Im.Image, mode='RGBA'):
    return pg.image.frombuffer(im.tobytes(), im.size, mode)


def display_init():
    pg.display.set_caption("Thirdmaze_beta")
    pg.display.set_icon(im2pg(Im.open(MediaPath/"icon.png").convert('RGBA')))
    return root


class Death(RuntimeError):
    "raised when the hero dies"


class GameExit(RuntimeError):
    "raised to return to the mainmenu"


class _MediaPath:
    def __init__(self):
        _ROOT = os.path.abspath(os.path.dirname(__file__))
        while 'src' not in os.listdir(_ROOT):
            _ROOT = os.path.dirname(_ROOT)
            if os.path.dirname(_ROOT) == _ROOT:
                raise FileNotFoundError("Cannot find 'src' directory.")
        self.IMAGE_ROOT = os.path.abspath(os.path.join(_ROOT, 'assets', 'thirdmaze', 'img'))
        self.DLL_ROOT = os.path.abspath(os.path.join(_ROOT, 'assets', 'thirdmaze', 'dll'))
        self.FIREWORK_ROOT = os.path.abspath(os.path.join(_ROOT, 'assets', 'numguess'))
        sys.path.append(self.DLL_ROOT)
        pass

    def __truediv__(self, filename: str):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            if filename.lower().startswith('firework'):
                return os.path.abspath(os.path.join(self.FIREWORK_ROOT, filename))
            return os.path.abspath(os.path.join(self.IMAGE_ROOT, filename))
        elif filename.lower().endswith(('.dll', '.so', '.dylib')):
            return os.path.abspath(os.path.join(self.DLL_ROOT, filename))
        else:
            raise ValueError("Unsupported file type for MediaPath")
        
class _SavePath:
    SAVE_ROOT = os.path.abspath(os.path.join(os.environ['APPDATA'], 'PyScriptX', 'MyToolkits', 'ThirdMaze', 'saves'))
    def __init__(self):
        os.makedirs(self.SAVE_ROOT, exist_ok=True)
        pass
    
    def __truediv__(self, filename: str):
        ret_path = os.path.abspath(os.path.join(self.SAVE_ROOT, filename))
        os.makedirs(os.path.dirname(ret_path), exist_ok=True)
        return ret_path

MediaPath = _MediaPath()
SavePath = _SavePath()
