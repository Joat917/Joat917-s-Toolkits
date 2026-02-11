"""
文件: puzzle15game.py
作者: XQ S
创建日期: Jan 3 2025
修改日期: Feb 11 2026
版本: 2.1
描述:
  此模块实现了经典的拼图游戏“数字华容道”，也被称为15拼图游戏。该游戏使用Pygame库来创建图形用户界面，
  并允许玩家通过移动方块来尝试解决拼图。此文件包含了游戏逻辑、UI组件、动画效果等功能。
  此模块实现了对该游戏的解决方案，在不同的阶段使用不同的算法促使拼图解决。

使用方法:
  运行此文件将启动游戏。游戏提供了开始菜单、游戏界面和结束菜单三个主要页面，玩家可以在这些页面之间切换。
  游戏支持窗口大小调整，并且在不同状态下提供适当的响应。 
  滑动滑动条改变难度，支持2x2到16x16。
  按键盘上下左右、WASD、IJKL移动滑块，也可以鼠标单击滑块以移动一个或多个滑块。
  按H键在棋盘上输出提示。
  按F键进行一步建议的操作，长按F键持续自动进行游戏操作。
"""

import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from abc import ABC
import random
import heapq
from collections import deque
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

screen_width=400
screen_height=500

FPS = 30
ANIMATION=True
ANIMATION_DURATION=0.3
AUTO_CONSOLE_HINT=False
PRINT_CAUGHT_EXCEPTION=False

class Main:
    "主函数，初始化显示模块并包含了游戏各个模块之间的切换。"

    def __init__(self):
        "初始化pygame环境，设置屏幕、背景颜色、标题等基础属性。"
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
        self.bgColor=Color('#222')
        pygame.display.set_caption("数字华容道")
        self.clock = pygame.time.Clock()
        self.default_size = 3
        self.state = "start_menu"
        self.page = StartMenu(self)
        self.callbacks=[]
        self._executing_callbacks=[]

    def start_menu(self):
        "设置当前状态为开始菜单，并更新页面。"
        self.state = "start_menu"
        self.page.delete()
        self.page = StartMenu(self)

    def start_game(self):
        "设置当前状态为游戏进行中，并初始化拼图游戏页面。"
        self.state = "playing"
        self.page.delete()
        self.page = PuzzleGame(self, self.default_size)

    def end_menu(self):
        "设置当前状态为结束菜单，并显示胜利后的菜单页面。"
        self.state = "end_menu"
        self.page.delete()
        self.page = EndMenu(self)

    def mainloop(self):
        "游戏的主循环，处理事件、刷新屏幕以及执行回调函数。"
        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type==pygame.WINDOWRESIZED:
                    global screen_width, screen_height
                    screen_width=self.screen.get_width()
                    screen_height=self.screen.get_height()
                    self.page.window_resized()
                else:
                    self.page.handle_event(event)
            self._executing_callbacks.extend(self.callbacks)
            self.callbacks.clear()
            for func in self._executing_callbacks:
                func()
            self._executing_callbacks.clear()

            self.screen.fill(self.bgColor.tup)
            self.page.draw()
            pygame.display.flip()


class Page(ABC):
    "页面的母类，为所有的页面切换提供接口。"

    def __init__(self, main: Main):
        super().__init__()
        self.main = main
        self.widgets = {}

    def window_resized(self):
        "当窗口大小改变时调用，调整页面上的控件位置。"
        for w in list(self.widgets.values()):
            w.window_resized()

    def handle_event(self, event):
        "处理用户输入事件，如鼠标点击或键盘按键。"
        for w in list(self.widgets.values()):
            w.handle_event(event)

    def draw(self):
        "绘制页面上的所有控件。"
        for w in list(self.widgets.values()):
            w.draw(self.main.screen)

    def delete(self):
        "清除页面上的所有资源，准备释放。"
        self.main=None
        self.widgets.clear()


class Widget(ABC):
    "组件的母类，为所有的组件操作提供接口。"

    def __init__(self):
        super().__init__()

    def draw(self, screen: pygame.Surface):
        pass

    def handle_event(self, event: pygame.event.Event):
        pass

    def window_resized(self):
        pass


class StartMenu(Page):
    def __init__(self, main: Main):
        "创建开始菜单上的控件，如启动按钮和难度选择滑动条。"
        super().__init__(main)
        w=min(int(screen_width*0.6), 400)
        h=int(w*0.4)
        self.widgets["button"] = Button(
            pygame.Rect((screen_width-w) // 2, (screen_height-h) // 2 - 20, w, h),
            Color.get_random(), "Start Game", self.main.start_game)
        self.widgets["slider"] = Slider(
            pygame.Rect((screen_width-w) // 2, (screen_height+h) // 2 + 50, w, 20),
            2, 16, self.main.default_size, callback=self.set_value)
        self.widgets["sidehint"]=Text("Size: {}x{}".format(self.main.default_size, self.main.default_size), screen_height//2+60)

    def set_value(self, value):
        "设置由滑动条选择的游戏难度值。"
        self.main.default_size = value
        self.widgets["sidehint"].refresh("Size: {}x{}".format(value, value))

    def window_resized(self):
        "重置并重新创建控件以适应新的窗口尺寸。"
        w=min(int(screen_width*0.6), 400)
        h=int(w*0.4)
        self.widgets.clear()
        self.widgets["button"] = Button(
            pygame.Rect((screen_width-w) // 2, (screen_height-h) // 2 - 20, w, h),
            Color.get_random(), "Start Game", self.main.start_game)
        self.widgets["slider"] = Slider(
            pygame.Rect((screen_width-w) // 2, (screen_height+h) // 2 + 50, w, 20),
            2, 16, self.main.default_size, callback=self.set_value)
        self.widgets["sidehint"]=Text("Size: 3x3", screen_height//2+60)
        return super().window_resized()



class EndMenu(Page):
    def __init__(self, main):
        "创建结束菜单上的控件，提供重新开始或返回主菜单选项。"
        super().__init__(main)
        w=min(screen_width//2-60, 400)
        h=int(w*0.4)
        self.widgets = {
            "Restart": Button(
                pygame.Rect(screen_width//2-w-30, (screen_height-h)//2, w, h),
                Color.get_random(), "Restart", self.main.start_game),
            "Mainmenu": Button(
                pygame.Rect(screen_width//2+30, (screen_height-h)//2, w, h),
                Color.get_random(), "Main Menu", self.main.start_menu),
            "Caption": Text("You Win!", screen_height//2-100)
        }

    def window_resized(self):
        w=min(screen_width//2-60, 400)
        h=int(w*0.4)
        self.widgets.clear()
        self.widgets = {
            "Restart": Button(
                pygame.Rect(30, (screen_height-h)//2, w, h),
                Color.get_random(), "Restart", self.main.start_game),
            "Mainmenu": Button(
                pygame.Rect(screen_width//2+30, (screen_height-h)//2, w, h),
                Color.get_random(), "Main Menu", self.main.start_menu),
            "Caption": Text("You Win!", screen_height//2-100)
        }
        return super().window_resized()


class Color:
    "颜色类，通过各种方式输入颜色并输出对应RGB数值。"
    A = {
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'gray': (180, 180, 180),
        'white': (255, 255, 255),
        'black': (0, 0, 0)
    }

    def __init__(self, hint=None):
        self.tup = (0, 0, 0)
        if isinstance(hint, str):
            if hint[0] == '#':
                if len(hint) == 7:
                    self.tup = (int(hint[1:3], 16), int(hint[3:5], 16), int(hint[5:7], 16))
                if len(hint) == 4:
                    self.tup = (int(hint[1], 16)*0x11, int(hint[2], 16)*0x11, int(hint[3], 16)*0x11)
                else:
                    raise ValueError("use #rrggbb to represent color")
            elif hint.lower() in self.A:
                self.tup = self.A[hint.lower()]
            else:
                raise ValueError("unrecognizable string")
        elif isinstance(hint, int):
            assert 0 <= hint <= 255
            self.tup = (hint, hint, hint)
        elif isinstance(hint, tuple):
            if len(hint) == 3:
                assert all(0 <= i <= 255 for i in hint)
                self.tup = hint
            else:
                raise ValueError("tuple length must be 3")
        elif hint is None:
            pass
        else:
            raise TypeError("hint wrong type")

    @staticmethod
    def from_hsv(hsv):
        return Color(hint=tuple(cv2.cvtColor(np.array([[hsv]], np.uint8), cv2.COLOR_HSV2RGB)[0, 0, :]))

    def to_hsv(self):
        return tuple(cv2.cvtColor(np.array([[self.tup]], np.uint8), cv2.COLOR_RGB2HSV)[0, 0, :])

    def darken(self):
        "返回一个变暗的颜色实例。"
        h, s, v = self.to_hsv()
        v -= 20
        s -= 5
        if v < 0:
            v = 0
        if s < 0:
            s = 0
        return Color.from_hsv((h, s, v))

    def opposite_black_or_white(self):
        "根据当前颜色亮度返回对比色（黑或白）"
        _, _, v = self.to_hsv()
        if v > 128:
            return Color('black')
        else:
            return Color('white')
        
    @staticmethod
    def get_random(s=100, v=200):
        "生成随机颜色"
        return Color.from_hsv((random.randint(0, 255), s, v))


def get_button_image(size: tuple, text: str, color: Color, radius=20, text_size=20, text_resize=True, outline=None, outline_width=0):
    "获取一个带有文本的圆角矩形图像，用作按钮图片。根据提供的参数生成相应图像。"
    image = Image.new('RGBA', size)
    draw = ImageDraw.Draw(image)
    text_color = color.opposite_black_or_white()

    radius = min(radius, size[0]//2, size[1]//2)
    draw.rounded_rectangle([0, 0, size[0], size[1]], fill=color.tup, 
                           outline=outline, width=outline_width, radius=radius)

    try:
        font = ImageFont.truetype("arial.ttf", text_size)
    except IOError:
        font = ImageFont.load_default()
    text_img = Image.new('RGBA', (500, 300))
    draw = ImageDraw.Draw(text_img).text((0, 0), text, fill=text_color.tup, font=font)
    text_img = text_img.crop(text_img.getbbox())

    if text_resize:
        text_scale = min(image.width/text_img.width, image.height/text_img.height)*0.8
        text_img = text_img.resize((int(text_img.width*text_scale), int(text_img.height*text_scale)), Image.Resampling.LANCZOS)
    position = ((image.width - text_img.width) // 2, (image.height - text_img.height) // 2)
    image.paste(text_img, position, text_img)

    return image


def im2sf(im: Image.Image):
    "将PIL图像转换为Pygame Surface对象。"
    return pygame.image.frombuffer(im.tobytes(), im.size, im.mode)


def smooth_mix(t, x0, x1):
    "为动画定制的平滑移动函数，基于时间进度计算两个点之间的插值"
    return x0+(x1-x0)*np.sin(np.pi/2*t)

def smooth_mix_2(t, x0, x1, x2):
    "基于时间进度计算三个点之间的插值"
    if t<0.5:
        return x0+(x1-x0)*np.sin(np.pi*t)
    else:
        return x1+(x2-x1)*(1+np.cos(2*np.pi*t))/2


class Button(Widget):
    def __init__(self, rect: pygame.Rect, color: Color, text: str, callback=None):
        super().__init__()
        self.rect = rect
        self.image1=im2sf(get_button_image(self.rect.size, text, color))
        self.image2=im2sf(get_button_image(self.rect.size, text, color.darken()))
        self.callback = callback

    def draw(self, screen):
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            screen.blit(self.image2, self.rect)
        else:
            screen.blit(self.image1, self.rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()


class Slider(Widget):
    def __init__(self, rect: pygame.Rect, min_value: int, max_value: int, initial_value=None, callback=None, color1=None, color2=None):
        super().__init__()
        self.rect = rect
        self.min_value = min_value
        self.max_value = max_value
        if initial_value is None:
            self.value = min_value
        else:
            self.value = initial_value
        self.callback = callback
        self.dragging = False
        if color1 is None:
            self.color1 = Color.get_random()
        else:
            self.color1=color1
        if color2 is None:
            self.color2=Color("#ddd")
        else:
            self.color2 = color2

    def draw(self, screen):
        pygame.draw.rect(screen, self.color1.tup, self.rect)
        # Calculate the position of the slider knob
        knob_x = self.v2x(self.value)
        # Draw the knob
        pygame.draw.circle(screen, self.color2.tup, (int(
            knob_x), self.rect.y + self.rect.height // 2), self.rect.height // 2)

    def x2v(self, x):
        return int((x - self.rect.x) / self.rect.width * (self.max_value - self.min_value)) + self.min_value

    def v2x(self, v):
        return self.rect.x + (v - self.min_value) / (self.max_value - self.min_value) * self.rect.width

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                new_value = max(min(self.max_value, self.x2v(event.pos[0])), self.min_value)
                if new_value != self.value:
                    self.value = new_value
                    if self.callback:
                        self.callback(self.value)


class Text(Widget):
    def __init__(self, text, y):
        super().__init__()
        self.text=text
        self.y=y
        self.image=pygame.font.SysFont(None, 48).render(self.text, True, (255,255,255))
        self.rect=self.image.get_rect(center=(screen_width/2, self.y))

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def refresh(self, text):
        "更新文本内容并重新渲染"
        self.text=text
        self.image=pygame.font.SysFont(None, 48).render(self.text, True, (255,255,255))
        self.rect=self.image.get_rect(center=(screen_width/2, self.y))


class PuzzleTile(Widget):
    def __init__(self, game, index: int, size: int, color: Color, pos: tuple):
        "创建一个拼图块，它可以在网格上移动"
        super().__init__()
        self.game = game
        self.main = game.main
        self.index = index
        self.size = size
        self.color = color
        self.image = im2sf(get_button_image((self.size, self.size), str(self.index), self.color, 
                                            text_size=int(self.size*0.7*min(1, 2/len(str(self.index)))), 
                                            text_resize=False, outline_width=5, outline=color.darken().tup))

        self.pos=pos
        coord=self.game.pos2coord(*self.pos)
        self.rect=pygame.Rect(coord[0], coord[1], self.size, self.size)
        
        # prevent multiple animation in effect
        self.animation_level=0
        pass

    def moveTo(self, pos, *, ban_animation=False):
        "移动拼图块到新位置，可以选择是否禁用动画"
        self.pos=pos
        if not ANIMATION or ban_animation:
            self.rect.left, self.rect.top=self.game.pos2coord(*self.pos)
        else:
            targetx, targety=self.game.pos2coord(*self.pos)
            total=int(FPS*ANIMATION_DURATION)
            self.animation_level+=1
            def _animation_callback(process, total, startx, starty, targetx, targety, animation_level):
                if animation_level<self.animation_level or self.main is None:
                    return # discard this animation process
                if process==total:
                    self.rect.left, self.rect.top=targetx, targety
                    self.game.check_win()
                else:
                    self.rect.left=smooth_mix(process/total, startx, targetx)
                    self.rect.top=smooth_mix(process/total, starty, targety)
                    self.main.callbacks.append(lambda:_animation_callback(process+1, total, startx, starty, targetx, targety, animation_level))
            self.main.callbacks.append(lambda:_animation_callback(0, total, self.rect.left, self.rect.top, targetx, targety, self.animation_level))

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def handle_event(self, event):
        if event.type==pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if self.game.blank_pos[0]==self.pos[0]:
                    if self.game.blank_pos[1]>self.pos[1]:
                        while self.game.blank_pos[1]>self.pos[1]:
                            self.game.moveTowards((0, -1))
                    elif self.game.blank_pos[1]<self.pos[1]:
                        while self.game.blank_pos[1]<self.pos[1]:
                            self.game.moveTowards((0, 1))
                if self.game.blank_pos[1]==self.pos[1]:
                    if self.game.blank_pos[0]>self.pos[0]:
                        while self.game.blank_pos[0]>self.pos[0]:
                            self.game.moveTowards((-1, 0))
                    elif self.game.blank_pos[0]<self.pos[0]:
                        while self.game.blank_pos[0]<self.pos[0]:
                            self.game.moveTowards((1, 0))

    def window_resized(self):
        self.size=self.game.tile_size
        self.image = im2sf(get_button_image((self.size, self.size), str(self.index), self.color, 
                                            text_size=int(self.size*0.7*min(1, 2/len(str(self.index)))), 
                                            text_resize=False, outline_width=5, outline=self.color.darken().tup))
        coord=self.game.pos2coord(*self.pos)
        self.rect=pygame.Rect(coord[0], coord[1], self.size, self.size)
        return super().window_resized()


class PuzzleGame(Page):
    def __init__(self, main: Main, size=3):
        super().__init__(main)
        self.clock = main.clock
        self.size = size
        self.board = np.zeros((self.size, self.size))
        self.tile_size = min(screen_width,screen_height) // self.size
        for row in range(self.size):
            for col in range(self.size):
                index = row*self.size+col+1
                self.board[row, col] = index
                if index != self.size*self.size:
                    self.widgets[index] = PuzzleTile(self, index, self.tile_size, Color('#da8'), (row, col))
        self.blank_pos = (self.size - 1, self.size - 1)
        self.board[self.blank_pos] = 0
        self.shuffle()
        self.check_win_checked=False
        if AUTO_CONSOLE_HINT:
            print(PuzzleProgressSolver(self.board).getHints(True))

    def shuffle(self, seed=None):
        "打乱拼图板上的方块"
        rng = np.random.Generator(np.random.PCG64(seed=seed))
        self.board=np.arange(self.size*self.size).reshape((self.size,self.size))
        while True:
            rng.shuffle(self.board.reshape(-1))
            if self._check_win_boolean():
                continue
            solver = PuzzleProgressSolver(self.board)
            if solver.solvable():
                break
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row, col] == 0:
                    self.blank_pos=(row, col)
                else:
                    self.widgets[self.board[row, col]].moveTo((row, col), ban_animation=True)


    def moveTowards(self, direction, *, no_exception=False, ban_animation=False):
        "将空白位置向指定方向移动一格"
        assert any(direction == t for t in [(0, 1), (1, 0), (0, -1), (-1, 0)])
        self.check_win_checked=False
        new_blank_pos = (self.blank_pos[0] + direction[0], self.blank_pos[1] + direction[1])
        if 0 <= new_blank_pos[0] < self.size and 0 <= new_blank_pos[1] < self.size:
            self.widgets[self.board[new_blank_pos]].moveTo(self.blank_pos, ban_animation=ban_animation)
            self.board[new_blank_pos], self.board[self.blank_pos] = self.board[self.blank_pos], self.board[new_blank_pos]
            self.blank_pos = new_blank_pos

            if not ANIMATION:
                self.check_win()
        else:
            if not no_exception:
                raise ValueError("touches edge")

    def pos2coord(self, row, col):
        "将拼图板上的行列坐标转换为屏幕坐标。"
        return (screen_width-self.size*self.tile_size)//2+col*self.tile_size, \
            (screen_height-self.size*self.tile_size)//2+row*self.tile_size

    def _check_win_boolean(self):
        "检查拼图是否完成"
        if self.board[self.size - 1, self.size - 1] != 0:
            return False
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row, col] == row * self.size + col + 1:
                    continue
                if row != self.size-1 or col != self.size-1:
                    return False
        return True
    
    def check_win(self):
        "如果拼图完成，则切换到结束菜单"
        if self.main is None or self.check_win_checked:
            return
        self.check_win_checked=True
        if self._check_win_boolean():
            self.main.end_menu()
            self.delete()
        elif AUTO_CONSOLE_HINT:
            print(PuzzleProgressSolver(self.board).getHints(True))

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.moveTowards((1,0), no_exception=True)
            elif event.key == pygame.K_DOWN:
                self.moveTowards((-1,0), no_exception=True)
            elif event.key == pygame.K_LEFT:
                self.moveTowards((0,1), no_exception=True)
            elif event.key == pygame.K_RIGHT:
                self.moveTowards((0,-1), no_exception=True)
            elif event.key==pygame.K_h:
                self.display_hint()
            elif event.key==pygame.K_f:
                self.implement_hint()
                def _holdkey_callback(cooldown):
                    if not pygame.key.get_pressed()[pygame.K_f] or self.main is None:
                        return
                    if cooldown>0:
                        self.main.callbacks.append(lambda:_holdkey_callback(cooldown-1))
                    else:
                        self.implement_hint()
                        self.main.callbacks.append(lambda:_holdkey_callback(int(0.1*FPS)))
                self.main.callbacks.append(lambda:_holdkey_callback(int(1*FPS)))
            # elif event.key==pygame.K_v:
            #     # 测试新功能用
            #     pz=PuzzleProgressSolver(self.board)
            #     print(pz.getHints(True))
            else:
                return
            
    def window_resized(self):
        self.tile_size = min(screen_width,screen_height) // self.size
        return super().window_resized()

    def display_hint(self, *, eta=0.3):
        if not ANIMATION:
            return
        l=PuzzleProgressSolver(self.board).getHints()
        if not l:
            return
        p=l[0]
        target_tile=(self.blank_pos[0]+p[0], self.blank_pos[1]+p[1])
        s=self.widgets[self.board[target_tile]]
        s.animation_level+=1
        total=int(FPS*ANIMATION_DURATION)
        end_point=self.pos2coord(*target_tile)
        mid_point=self.pos2coord(*self.blank_pos)
        mid_point=(mid_point[0]*eta+end_point[0]*(1-eta), mid_point[1]*eta+end_point[1]*(1-eta))
        def _animation_callback(s,process, total, x1,y1,x2,y2,x3,y3, animation_level):
            if animation_level<s.animation_level or s.main is None:
                return # discard this animation process
            if process==total:
                s.rect.left, s.rect.top=x3,y3
            else:
                s.rect.left=smooth_mix_2(process/total, x1,x2,x3)
                s.rect.top=smooth_mix_2(process/total, y1,y2,y3)
                s.main.callbacks.append(lambda:_animation_callback(s,process+1,total,x1,y1,x2,y2,x3,y3,animation_level))
        self.main.callbacks.append(lambda:_animation_callback(s,0,total,s.rect.left,s.rect.top,mid_point[0],mid_point[1],end_point[0],end_point[1],s.animation_level))

    def implement_hint(self):
        l=PuzzleProgressSolver(self.board).getHints(no_exception=True)
        if l:
            self.moveTowards(l[0])


class PuzzleProgressSolver:
    "判断下一步需要把哪一个或者两个数字归位，并提供归位所需的步骤。"
    def __init__(self, board):
        self.board=board
        self.size=board.shape[0]
        self.fixed_numbers=set()
        assert board.shape[0]==board.shape[1]
        return
    
    def solvable(self):
        board_flattened=[x for x in self.board.flatten() if x!=0]
        inversions = sum(board_flattened[i] > board_flattened[j] for i in range(len(board_flattened)) for j in range(i+1, len(board_flattened)))
        if self.size%2==1:
            # 逆序数为偶数时可解
            return inversions % 2 == 0
        
        new_board = self.board.copy()
        space_position = np.argwhere(new_board == 0)[0]
        if space_position[1]!=self.size-1:
            new_board[space_position[0], space_position[1]:-1] = new_board[space_position[0], space_position[1]+1:]
            new_board[space_position[0], -1] = 0
            space_position[1] = self.size-1
            assert new_board[space_position[0], space_position[1]]==0
        if space_position[0]!=self.size-1:
            new_board[space_position[0]:-1, space_position[1]] = new_board[space_position[0]+1:, space_position[1]]
            new_board[-1, space_position[1]] = 0
            space_position[0] = self.size-1
            assert new_board[space_position[0], space_position[1]]==0
        # 当空格位置与逆序数的奇偶性相同时可解
        board_flattened=new_board.flatten()[:-1]
        inversions = sum(board_flattened[i] > board_flattened[j] for i in range(len(board_flattened)) for j in range(i+1, len(board_flattened)))
        return inversions % 2 == 0

    def _placeDone(self, row, col, ind):
        "假定这个位置的左上全部归位，判断这个位置是否归位。"
        if row>=self.size-2:
            if col>=self.size-2:
                return self.board[row,col]==ind and self.board[row+1, col]==ind+self.size and self.board[row,col+1]==ind+1
            else:
                return self.board[row,col]==ind and self.board[row+1,col]==ind+self.size
        else:
            if col>=self.size-2:
                return self.board[row,col]==ind and self.board[row,col+1]==ind+1
            else:
                return self.board[row,col]==ind
            
    def donePlaces(self):
        "把所有已经归位的数字放入fixed_numbers，并返回下一步可能归位的数字的列表"
        out1=[]
        out2=[]
        current_row_aligned_count=self.size-1
        for row in range(self.size-1):
            for col in range(current_row_aligned_count):
                ind=row*self.size+col+1
                if self._placeDone(row, col, ind):
                    out1.append(ind)
                else:
                    current_row_aligned_count=col
                    out2.append(ind)
                    break
        self.fixed_numbers=set(out1)
        return out2
    
    def findNumber(self, number, topleft=None, gridsize=None):
        "找到某个数字的位置"
        if topleft is None:
            for row in range(self.size-1,-1,-1):
                for col in range(self.size-1,-1,-1):
                    if self.board[row,col]==number:
                        return row,col
            raise ValueError("not found")
        else:
            for row in range(topleft[0], topleft[0]+gridsize[0]):
                for col in range(topleft[1], topleft[1]+gridsize[1]):
                    if self.board[row,col]==number:
                        return row,col
            raise ValueError("not found")
    
    def targetPlace(self, number):
        "某个数字的最终目标位置"
        return divmod(number-1, self.size)
    
    @staticmethod
    def astar(size, start:tuple, end:set, avoiding:set):
        "通过AStar寻路算法避开障碍物抵达指定区域。"
        if start in end:
            return [start]
        if not end.difference(avoiding):
            raise ValueError("no available destination")
        def neighbors(point):
            out=set()
            if point[0]<size-1:
                out.add((point[0]+1, point[1]))
            if point[1]<size-1:
                out.add((point[0], point[1]+1))
            if point[0]>0:
                out.add((point[0]-1, point[1]))
            if point[1]>0:
                out.add((point[0], point[1]-1))
            return out.difference(avoiding)
        def distance(p1, p2):
            return abs(p1[0]-p2[0])+abs(p1[1]-p2[1])
        def distance_end(p):
            return min(distance(p,e) for e in end)
        explored={start:distance_end(start)}
        frontier=[(explored[start], start, 0)]
        last={start:None}
        while frontier:
            _, base, stepcount=heapq.heappop(frontier)
            for battlefield in neighbors(base):
                if battlefield in explored:
                    continue
                explored[battlefield]=stepcount+1+distance_end(battlefield)
                heapq.heappush(frontier, (explored[battlefield], battlefield, stepcount+1))
                last[battlefield]=base
                if battlefield in end:
                    t=battlefield
                    out=deque()
                    while t is not None:
                        out.appendleft(t)
                        t=last[t]
                    return out
        raise RuntimeError("destination unreachable")            
    
    def findPath(self, start, targetTL, targetSize=(1,1), avoiding=set()):
        "找到一条通路，并避开已经确定的部分数字。包含起点和终点。"
        if targetSize==(1,1):
            end={targetTL}
        else:
            end={(targetTL[0]+i, targetTL[1]+j) for i in range(targetSize[0]) for j in range(targetSize[1])}
        avoiding=avoiding.union(map(self.targetPlace, self.fixed_numbers))
        return self.astar(self.size, start, end, avoiding)
    
    @staticmethod
    def pathPoint2Operation(pathPoints):
        "把一条收尾相接路径转化为操作。"
        pathPoints=iter(pathPoints)
        last=next(pathPoints)
        out=[]
        try:
            while True:
                current=next(pathPoints)
                out.append((current[0]-last[0], current[1]-last[1]))
                last=current
        except StopIteration:
            return out

    def stepOperations(self, number, textify=False):
        "给定需要归位的数字，给出将其归位需要的下一部分步骤。可选把指令诠释为文本"
        if textify:
            try:
                operations=self.stepOperations(number=number, textify=False)
                return '、'.join(map({(1,0):"上",(-1,0):"下",(0,1):"左",(0,-1):"右"}.get, operations))
            except Exception as exc:
                return str(exc)
        
        row,col=self.targetPlace(number)
        if row<self.size-2:
            if col<self.size-2:
                return self.stepOperation1(number)
            else:
                return self.stepOperation2(number, number+1)
        else:
            if col<self.size-2:
                return self.stepOperation2(number, number+self.size)
            else:
                return self.final22Operations()
            
    def _spaceCandidates(self, start, end):
        "为了把数字从起始位置移动到最终位置，空格所有可能的目的地"
        out=[]
        if end[0]>start[0]:
            out.append((start[0]+1, start[1]))
        if end[0]<start[0]:
            out.append((start[0]-1, start[1]))
        if end[1]>start[1]:
            out.append((start[0], start[1]+1))
        if end[1]<start[1]:
            out.append((start[0], start[1]-1))
        return set(out).difference(map(self.targetPlace, self.fixed_numbers))

    def stepOperation1(self, number):
        "给定需要归位的单个数字，给出将其归位需要的下一部分步骤。"
        start=self.findNumber(number)
        end=self.targetPlace(number)
        if start==end:
            raise ValueError("number already in its place")
        next_space_candidates=self._spaceCandidates(start, end)
        space_start=self.findNumber(0)
        space_path=self.astar(self.size, space_start, set(next_space_candidates), avoiding={start}.union(map(self.targetPlace, self.fixed_numbers)))
        if len(space_path)>1:
            return self.pathPoint2Operation(space_path)
        else:
            return self.pathPoint2Operation([space_start, start])

    def stepOperation2(self, number1, number2):
        "给定需要归位的两个数字，将它们和空格一起移入可操作2x3方格中。"
        targetTL=self.targetPlace(number1)
        if number2-number1==1:
            targetSize=(3,2)
        elif number2-number1==self.size:
            targetSize=(2,3)
        else:
            raise ValueError("inappropriate number2")
        # move number 1
        start=self.findNumber(number1)
        number_path=self.findPath(start, targetTL, targetSize)
        if len(number_path)>1:
            space_start=self.findNumber(0)
            space_path=self.findPath(space_start, number_path[1], avoiding={start})
            if len(space_path)>1:
                return self.pathPoint2Operation(space_path)
            else:
                return self.pathPoint2Operation([space_start, start])
            
        # move number 2
        avoiding={start}
        start=self.findNumber(number2)
        number_path=self.findPath(start, targetTL, targetSize)
        space_start=self.findNumber(0)
        if len(number_path)>1:
            space_path=self.findPath(space_start, number_path[1], avoiding={start}.union(avoiding))
            if len(space_path)>1:
                return self.pathPoint2Operation(space_path)
            else:
                return self.pathPoint2Operation([space_start, start])
            
        # move space
        avoiding.add(start)
        space_path=self.findPath(space_start, targetTL, targetSize, avoiding=avoiding)
        if len(space_path)>1:
            return self.pathPoint2Operation(space_path)
        else:
            return self.final23Operations(targetTL, targetSize, number1, number2)

    def final23Operations(self, gridLeftTop, gridSize, number1, number2):
        "给定可操作2x3方格的位置和需要归位的数字，将这些数字归位。"
        current_state=self.board[gridLeftTop[0]:gridLeftTop[0]+gridSize[0],gridLeftTop[1]:gridLeftTop[1]+gridSize[1]]
        if gridSize==(2,3):
            def isok(state):
                return state[0,0]==number1 and state[1,0]==number2
        elif gridSize==(3,2):
            def isok(state):
                return state[0,0]==number1 and state[0,1]==number2
        else:
            raise ValueError
        operations, intermediate_states=self.bfs(current_state, isok)
        return operations

    def final22Operations(self):
        "只有右下角四个数字需要操作的时候，给出将其归位需要的所有步骤。"
        current_state=self.board[-2:,-2:]
        n1=self.size*(self.size-1)-1
        n2=n1+1
        n3=n1+self.size
        def isok(state):
            return state[0,0]==n1 and state[0,1]==n2 and state[1,0]==n3 and state[1,1]==0
        operations, intermediate_states=self.bfs(current_state, isok)
        return operations
    
    class State:
        def __init__(self, ndarray):
            self.data=ndarray

        def findZero(self):
            for row in range(self.data.shape[0]):
                for col in range(self.data.shape[1]):
                    if self.data[row,col]==0:
                        return row,col
            raise ValueError("not found")
        
        def neighbors(self):
            out={}
            zero_place=self.findZero()
            if zero_place[0]>0:
                new_place=zero_place[0]-1, zero_place[1]
                new_state=self.data.copy()
                new_state[zero_place], new_state[new_place]=self.data[new_place], self.data[zero_place]
                out[(-1,0)]=self.__class__(new_state)
            if zero_place[0]<self.data.shape[0]-1:
                new_place=zero_place[0]+1, zero_place[1]
                new_state=self.data.copy()
                new_state[zero_place], new_state[new_place]=self.data[new_place], self.data[zero_place]
                out[(1,0)]=self.__class__(new_state)
            if zero_place[1]>0:
                new_place=zero_place[0], zero_place[1]-1
                new_state=self.data.copy()
                new_state[zero_place], new_state[new_place]=self.data[new_place], self.data[zero_place]
                out[(0,-1)]=self.__class__(new_state)
            if zero_place[1]<self.data.shape[1]-1:
                new_place=zero_place[0], zero_place[1]+1
                new_state=self.data.copy()
                new_state[zero_place], new_state[new_place]=self.data[new_place], self.data[zero_place]
                out[(0,1)]=self.__class__(new_state)
            return out
        
        def __getitem__(self, index):
            return self.data[index]
        
        @staticmethod
        def xor(iterable):
            result=0
            for i in iterable:
                result^=i
            return result
        
        def __hash__(self):
            return self.xor(hash(tuple(line)) for line in self.data)
        
        def __eq__(self, other):
            return np.all(self.data==other.data)
        
        def __repr__(self):
            return repr(self.data)
    
    @classmethod
    def bfs(cls, init_state, check_function):
        "BFS from init state to satisfy check function. return operations and intermediate states(including init state)"
        init_state=cls.State(init_state)
        if check_function(init_state):
            return [], [init_state]
        frontier=deque([init_state])
        past={init_state: None}
        while frontier:
            base=frontier.popleft()
            for operation, battlefield in base.neighbors().items():
                if battlefield in past:
                    continue
                past[battlefield]=(base, operation)
                frontier.append(battlefield)
                if check_function(battlefield):
                    out_op=deque([])
                    out_im=deque([battlefield])
                    t=battlefield
                    while True:
                        _packed=past[t]
                        if _packed is None:
                            break
                        t, _op=_packed
                        out_op.appendleft(_op)
                        out_im.appendleft(t)
                    return out_op, out_im
        raise ValueError("bfs: no path found")
    
    def getHints(self, textify=False, no_exception=False):
        if textify:
            operations=self.getHints(textify=False, no_exception=no_exception)
            if operations:
                return '、'.join(map({(1,0):"上",(-1,0):"下",(0,1):"左",(0,-1):"右"}.get, operations))
            else:
                return '暂无提示'
        if no_exception:
            try:
                return self.getHints(textify=textify, no_exception=False)
            except Exception as exc:
                if PRINT_CAUGHT_EXCEPTION:
                    import traceback
                    traceback.print_exc()
                return []
        nums=self.donePlaces()
        for n in nums:
            return self.stepOperations(n)
        return []
    

if __name__ == "__main__":
    main=Main()
    main.mainloop()

