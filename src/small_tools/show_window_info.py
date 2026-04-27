"""
独立脚本：展示鼠标指针位置窗口的所有信息

功能说明：
1. 显示鼠标指针所在窗口的句柄、标题、类名、位置和大小等信息，并用绿色边框框出该窗口。
2. 按下F15进入移动模式，鼠标静止超过0.5秒后显示黑色半透明可拖动窗口，强制拖动目标窗口的位置。再次按下F15或者按下ESC退出移动模式。
3. 按下F8退出程序。
4. 当因为权限不足等原因导致目标窗口无法被移动时，在鼠标位置生成一些火花动画。
5. 忽略自身窗口的信息。
"""

import win32gui, win32api, win32con, ctypes
import os, sys
import time, threading
import math
import random
from PyQt5 import QtWidgets, QtCore, QtGui

TITLE_MAX_LENGTH = 50

def repeat_when_fail(func, retries=5):
    def wrapper(*args, **kwargs):
        for attempt in range(retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"Attempt {attempt+1} failed with error: {e}")
        return func(*args, **kwargs) # 最后一次尝试，如果失败了就让异常抛出
    return wrapper

@repeat_when_fail
def get_window_info_at_cursor():
    out = {}
    out['cursor_position'] = cursor_pos = win32api.GetCursorPos()
    out['handle'] = hwnd = win32gui.WindowFromPoint(cursor_pos)

    if not hwnd:
        return out
    out['title'] = win32gui.GetWindowText(hwnd)
    out['title_short'] = out['title'][:TITLE_MAX_LENGTH-3] + "..." if len(out['title']) > TITLE_MAX_LENGTH else out['title']
    out['class_name'] = win32gui.GetClassName(hwnd)
    rect = win32gui.GetWindowRect(hwnd)
    out['position'] = (rect[0], rect[1])
    out['size'] = (rect[2] - rect[0], rect[3] - rect[1])
    return out

def get_window_info_by_handle(hwnd):
    out = {}
    out['handle'] = hwnd
    if not hwnd:
        return out
    try:
        out['title'] = win32gui.GetWindowText(hwnd)
        out['title_short'] = out['title'][:TITLE_MAX_LENGTH-3] + "..." if len(out['title']) > TITLE_MAX_LENGTH else out['title']
        out['class_name'] = win32gui.GetClassName(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        out['position'] = (rect[0], rect[1])
        out['size'] = (rect[2] - rect[0], rect[3] - rect[1])
    except Exception as e:
        print(f"Error occurred while fetching window info for handle {hwnd}: {e}")
    return out


class CursorFollower(QtWidgets.QWidget):
    # 一个显示少量文字的窗口，始终位于鼠标右下角附近
    def __init__(self):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.label = QtWidgets.QLabel(self)

        # 样式：白色文字，存在黑色阴影
        self.label.setStyleSheet("color: white; background-color: transparent; border: none;")
        self.shadow = QtWidgets.QGraphicsDropShadowEffect(self.label)
        self.shadow.setBlurRadius(2)
        self.label.setGraphicsEffect(self.shadow)

        self.label.setText("Cursor Follower Loading...")
        self.label.move(10, 10)
        self.label.adjustSize()
        self.resize(self.label.sizeHint().width() + 20, self.label.sizeHint().height() + 20)

        self._old_cursor_pos = None

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.follow_cursor)
        self.timer.start(50)

        self.monitor_size = (win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1))

        self.show()

    def follow_cursor(self):
        cursor_pos = win32api.GetCursorPos()
        if cursor_pos != self._old_cursor_pos:
            self._old_cursor_pos = cursor_pos
            x, y = cursor_pos[0] + 20, cursor_pos[1] + 20
            if x + self.width() > self.monitor_size[0]:
                x = cursor_pos[0] - self.width() - 30
            if y + self.height() > self.monitor_size[1]:
                y = cursor_pos[1] - self.height() - 30
            self.move(x, y)

    def set_text(self, text):
        self.label.setText(text)
        self.label.adjustSize()
        self.resize(self.label.sizeHint().width() + 20, self.label.sizeHint().height() + 20)


class InfoWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowTitle("Window Info displayer")
        window_info = get_window_info_at_cursor()
        self.setGeometry(window_info['position'][0], window_info['position'][1], window_info['size'][0], window_info['size'][1])

        self.label = QtWidgets.QLabel(self)
        self.label.setStyleSheet("color: white; background-color: transparent; border: none;")
        self.label.setText(f"Handle: {window_info['handle']}\nTitle: {window_info['title_short']}\nClass: {window_info['class_name']}")
        self.label.move(10, 10)
        self.label.adjustSize()

        self.mouse_following_label = CursorFollower()
        self.mouse_following_label.set_text(self.label.text())

        self.background_label = QtWidgets.QLabel(self)
        self.background_label.setStyleSheet("background-color: transparent; border: 4px solid green;")
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.background_label.lower()  # 将背景标签放在最底层

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_info)
        self.timer.start(50)

        self._old_info_tuple = None
        self._last_valid_hwnd = None
        self._moving_enabled = False
        self._toggle_keydown = False
        self._mover = None
        self._force_update = False
        
        self._last_cursor_pos = None
        self._last_moving_time = 0

        self.show()

    def update_info(self):
        # get window info at cursor position
        new_info = get_window_info_at_cursor()
        # refresh only when window changes
        new_info_tuple = (new_info['handle'], new_info['position'], new_info['size'], new_info['title'], new_info['class_name'])
        if new_info_tuple != self._old_info_tuple or self._force_update:
            # ignore self window
            if new_info['handle'] == int(self.winId()):
                new_info.update(get_window_info_by_handle(self._last_valid_hwnd))
                new_info_tuple = (new_info['handle'], new_info['position'], new_info['size'], new_info['title'], new_info['class_name'])
            # don't change handle when moving
            if self._mover is not None and self._mover.is_moving:
                if win32gui.IsWindow(self._mover.hwnd):
                    new_info.update(get_window_info_by_handle(self._mover.hwnd))
                    new_info_tuple = (new_info['handle'], new_info['position'], new_info['size'], new_info['title'], new_info['class_name'])
                else:
                    self._last_valid_hwnd = new_info['handle']
                    self._mover.hwnd = None
                    self._mover.stop_move()
            # ignore desktop
            if new_info['handle'] == 0 and not self._mover.is_moving:
                self.hide()
                self.mouse_following_label.set_text("No window")
            
            self._last_valid_hwnd = new_info['handle']
            if new_info_tuple != self._old_info_tuple or self._force_update:
                self._old_info_tuple = new_info_tuple
                # update window info
                self.setGeometry(new_info['position'][0], new_info['position'][1], new_info['size'][0], new_info['size'][1])
                self.background_label.setGeometry(0, 0, self.width(), self.height())
                self.label.setText(f"Handle: {new_info['handle']}\nTitle: {new_info['title_short']}\nClass: {new_info['class_name']}")
                self.label.adjustSize()
                self.mouse_following_label.set_text(self.label.text())
                self.show()
                self._force_update = False
        if win32api.GetAsyncKeyState(win32con.VK_ESCAPE) < 0:
            print("ESC key pressed.")
            if self.moving_enabled:
                self.moving_enabled = False
        if win32api.GetAsyncKeyState(win32con.VK_F8) < 0:
            print("F8 key pressed.")
            self.mouse_following_label.close()
            self.close()
            app.quit()
        
        if win32api.GetAsyncKeyState(win32con.VK_F15) < 0:
            print("\rF15 key pressed.", end="")
            if not self._toggle_keydown:
                self.moving_enabled = not self.moving_enabled
            self._toggle_keydown = True
        else:
            self._toggle_keydown = False

        if self.moving_enabled:
            if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) < 0:
                self._last_clicked_time = time.perf_counter()
                if self._mover.is_moving:
                    self._mover.move()
                    self._force_update = True
                else:
                    self._mover.hwnd = self._last_valid_hwnd
                    self._mover.start_move()
                    self.activateWindow()
            else:
                self._mover.stop_move()
                pass
        
        if self.moving_enabled:
            _time_since_moving = time.perf_counter() - self._last_moving_time
            # print(_time_since_moving, end="\r")
            if _time_since_moving > 0.5:
                self.background_label.setStyleSheet("background-color: rgba(0,0,0,128); border: 4px solid red;")
                self.activateWindow()
            elif not self._mover.is_moving:
                self.background_label.setStyleSheet("background-color: transparent; border: 4px solid red;")
        new_cursor_pos = new_info['cursor_position']
        if new_cursor_pos != self._last_cursor_pos:
            self._last_moving_time = time.perf_counter()
            self._last_cursor_pos = new_cursor_pos

    @property
    def moving_enabled(self):
        return self._moving_enabled
    
    @moving_enabled.setter
    def moving_enabled(self, value):
        if value and not self.moving_enabled:
            self._moving_enabled=True
            self.background_label.setStyleSheet("background-color: rgba(0,0,0,128); border: 4px solid red;")
            if self._mover is None:
                self._mover = WindowMover(0)
            self._mover.enabled = True
            self.activateWindow()
        elif not value and self.moving_enabled:
            self._moving_enabled=False
            self.background_label.setStyleSheet("background-color: transparent; border: 4px solid green;")
            self._mover.enabled = False


class WindowMover:
    def __init__(self, hwnd=None, enabled=True):
        self.hwnd = hwnd
        self.enabled = enabled
        self.offset = None

    @property
    def enabled(self):
        return self._enabled
    
    @property
    def is_moving(self):
        return self.offset is not None
    
    @enabled.setter
    def enabled(self, value):
        self._enabled = bool(value)
        if not self._enabled:
            self.stop_move()

    def start_move(self, cursor_pos=None):
        if not self.enabled:
            print("Moving not enabled.")
            return
        if cursor_pos is None:
            cursor_pos = win32api.GetCursorPos()
        if not self.hwnd:
            print("No window to move.")
            return
        try:
            rect = win32gui.GetWindowRect(self.hwnd)
            self.offset = (cursor_pos[0] - rect[0], cursor_pos[1] - rect[1])
        except Exception as e:
            self.hwnd = None
            self.offset = None
        
    
    def move(self, cursor_pos=None):
        if not self.enabled or not self.is_moving:
            return
        if not self.hwnd:
            print("No window to move.")
            return
        if cursor_pos is None:
            cursor_pos = win32api.GetCursorPos()
        new_x = cursor_pos[0] - self.offset[0]
        new_y = cursor_pos[1] - self.offset[1]
        print(f"Moving window {self.hwnd} to ({new_x}, {new_y})")
        try:
            window_size = win32gui.GetWindowRect(self.hwnd)
        except Exception as e:
            self.stop_move()
            return 
        if new_x == window_size[0] and new_y == window_size[1]:
            return
        try:
            hparent = win32gui.GetParent(self.hwnd)
            if hparent:
                target_x, target_y = win32gui.ScreenToClient(hparent, (new_x, new_y))
            else:
                target_x, target_y = new_x, new_y
            win32gui.MoveWindow(self.hwnd, target_x, target_y, window_size[2] - window_size[0], window_size[3] - window_size[1], True)
        except Exception as e:
            for _ in range(5):
                SparkIgnite(cursor_pos).show()
            print(f"Failed to move window: {e}")

    def stop_move(self):
        self.offset = None

class SparkIgnite(QtWidgets.QWidget):
    instances = []
    def __init__(self, position, size=10):
        super().__init__()
        self.velocity = (random.uniform(-20, 20), random.uniform(-20, 20)) # px/50ms
        self.temperature = random.uniform(1, 3)
        self._position = position
        self._size = size

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setGeometry(position[0]-size, position[1]-size, size*2, size*2)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(20)

        self.show()
        self.instances.append(self)

    def _set_position(self, pos):
        pos = (round(pos[0]), round(pos[1]))
        self._position = pos
        self.setGeometry(pos[0]-self._size, pos[1]-self._size, self._size*2, self._size*2)

    def update_animation(self):
        if self.temperature <= 0:
            # print("Spark extinguished.")
            self.timer.stop()
            self.timer.deleteLater()
            self.timer = None
            self.close()
            self.instances.remove(self)
            return
        new_x = self._position[0] + self.velocity[0]
        new_y = self._position[1] + self.velocity[1]
        self._set_position((new_x, new_y))
        self.velocity = self.velocity[0], self.velocity[1] + 1.0
        self.temperature -= 0.1
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        speed = math.hypot(*self.velocity)
        rect_width = max(self._size, self._size*speed)
        rect_height = 2
        points_rel = [
            QtCore.QPointF(0, -rect_height/2),  # 上
            QtCore.QPointF(rect_width, 0),       # 右
            QtCore.QPointF(0, rect_height/2),   # 下
            QtCore.QPointF(-rect_width, 0)       # 左
        ]

        left_middle = QtCore.QPointF(self.width() / 2, self.height() / 2)
        cos_a, sin_a = (0, 0) if speed == 0 else (self.velocity[0] / speed, self.velocity[1] / speed)
        points = [QtCore.QPointF(left_middle.x() + p.x()*cos_a - p.y()*sin_a, left_middle.y() + p.x()*sin_a + p.y()*cos_a) for p in points_rel]
        points = [QtCore.QPoint(round(p.x()), round(p.y())) for p in points]

        polygon = QtGui.QPolygon(points)
        r,g,b,a = self.temperature_to_color(self.temperature)
        painter.setBrush(QtGui.QBrush(QtGui.QColor(r, g, b, a)))
        painter.drawPolygon(polygon)

    @staticmethod
    def temperature_to_color(temperature):
        if temperature <= 0:
            return 0, 0, 0, 0
        if temperature <= 1:
            return round(temperature * 128), 0, 0, round(temperature * 255)
        if temperature <= 2:
            eta = temperature - 1
            return round(128 + eta * 127), round(eta * 255), 0, 255
        if temperature <= 3:
            eta = temperature - 2
            return 255, 255, round(eta * 255), 255
        return 255, 255, 255, 255


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for i in range(1, len(sys.argv)-1):
            if sys.argv[i] == '--lock-file':
                lock_file = sys.argv[i+1]
                if os.path.exists(lock_file):
                    with open(lock_file, 'r') as f:
                        existing_pid = f.read().strip()
                    if existing_pid and existing_pid.isdigit():
                        try:
                            os.kill(int(existing_pid), 0)
                            print(f"Another instance (PID {existing_pid}) is already running. Exiting.")
                            sys.exit(0)
                        except OSError:
                            print(f"Stale lock file found with PID {existing_pid}. Removing it.")
                            os.remove(lock_file)
                try:
                    with open(lock_file, 'x') as f:
                        f.write(str(os.getpid()))
                except FileExistsError:
                    print("Another instance is already running. Exiting.")
                    sys.exit(0)
                break
        for arg in sys.argv:
            if arg == '--verbose':
                print("Verbose mode enabled.")
                break
        else:
            sys.stdout = open(os.devnull, 'w')
    app = QtWidgets.QApplication(sys.argv)
    info_window = InfoWindow()
    sys.exit(app.exec_())





