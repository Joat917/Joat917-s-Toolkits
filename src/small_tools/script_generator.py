import pyautogui as p
import time as t
import pynput
import sys

p.PAUSE = 0.05
p.FAILSAFE = True

def on_click(x, y, button, pressed):
    global start_time
    print('{0} at {1}'.format('Pressed' if pressed else 'Released', (x, y)))

    # Getting which button to press/release
    button = str(button)
    if button[-2] == "f":
        button = "left"
    elif button[-2] == "h":
        button = "right"
    else:
        button = "middle"

    # Click and drag the mouse
    if pressed:
        press_time = t.time()
        sleep_time = press_time - start_time
        start_time = press_time
        with open(name+".pyw", "a", encoding="utf-8") as f_r:
            f_r.write(f"t.sleep({str(sleep_time)})\n")
            f_r.write(f"p.mouseDown({str(x)}, {str(y)}, button=\"{button}\")\n")
        f_r.close()
    else:
        press_time = t.time()
        sleep_time = press_time - start_time
        start_time = press_time
        with open(name + ".pyw", "a", encoding="utf-8") as f_r:
            f_r.write(f"t.sleep({str(sleep_time)})\n")
            f_r.write(f"p.mouseUp({str(x)}, {str(y)}, button=\"{button}\")\n")
        f_r.close()


dy_all = 0


def on_scroll(x, y, dx, dy):
    global start_time
    global dy_all
    if dx != 0:
        return False
    scroll_time = t.time()
    sleep_time = scroll_time - start_time

    # Quick scroll
    if sleep_time < 0.1:
        dy_all += dy
    else:
        dy_all += dy

        start_time = scroll_time
        print('Scrolled {0} at {1}'.format('down' if dy_all < 0 else 'up', (x, y)))
        with open(name + ".pyw", "a", encoding="utf-8") as f_r:
            f_r.write(f"t.sleep({str(sleep_time)})\n")
            f_r.write(f"p.moveTo({str(x)}, {str(y)})\n")
            f_r.write("ctr.scroll({0}, {1})\n".format(str(dx), str(dy_all)))
        f_r.close()
        dy_all = 0


def on_press(key):
    global start_time
    # Stop recording by pressing f8
    if key == pynput.keyboard.Key.f8:
        sys.exit()

    print("key {} is pressed".format(key))
    press_time = t.time()
    sleep_time = press_time - start_time
    start_time = press_time
    if type(key) is not pynput.keyboard.KeyCode:
        with open(name + ".pyw", "a", encoding="utf-8") as f_r:
            f_r.write(f"t.sleep({str(sleep_time)})\n")
            f_r.write(f"keyboard.press(pynput.keyboard.{key})\n")
        f_r.close()
    else:
        with open(name + ".pyw", "a", encoding="utf-8") as f_r:
            f_r.write(f"t.sleep({str(sleep_time)})\n")
            f_r.write(f"keyboard.press({key})\n")
        f_r.close()


enter_release = False


def on_release(key):
    global start_time
    global enter_release
    if enter_release:
        print("key {} is released".format(key))
        press_time = t.time()
        sleep_time = press_time - start_time
        start_time = press_time
        if type(key) is not pynput.keyboard.KeyCode:
            with open(name + ".pyw", "a", encoding="utf-8") as f_r:
                f_r.write(f"t.sleep({str(sleep_time)})\n")
                f_r.write(f"keyboard.release(pynput.keyboard.{key})\n")
            f_r.close()
        else:
            with open(name + ".pyw", "a", encoding="utf-8") as f_r:
                f_r.write(f"t.sleep({str(sleep_time)})\n")
                f_r.write(f"keyboard.release({key})\n")
            f_r.close()

    # Neglecting the first release of "enter"
    if key == pynput.keyboard.Key.enter:
        enter_release = True


def record(name_to_save):
    # Initializing a file
    f_r = open(name_to_save + ".pyw", "w", encoding="utf-8")
    f_r.write('import pyautogui as p\nimport time as t\nimport pynput\n')
    f_r.write("p.PAUSE = 0.05\np.FAILSAFE = True\n")
    f_r.write("ctr = pynput.mouse.Controller()\n")
    f_r.write("keyboard = pynput.keyboard.Controller()\n")
    f_r.close()

    # Collecting events
    mouse_listener = pynput.mouse.Listener(on_click=on_click,
                                           on_release=on_release,
                                           on_scroll=on_scroll)
    mouse_listener.start()
    with pynput.keyboard.Listener(on_press=on_press,
                                  on_release=on_release) as keyboard_listener:
        keyboard_listener.join()


if __name__ == "__main__":
    do = p.confirm(text="请选择操作", title="键盘和鼠标脚本生成器", buttons=["记录", "运行", "取消"])
    if do == "记录":
        name = p.prompt(text="请输入要保存的脚本文件名(无需加后缀)：\n按enter确认",
                        title="鼠标和键盘脚本生成器",
                        default="auto_gui")
        start_time = t.time()
        name = str(name)
        if name != "":
            # time3 = [t.localtime().tm_hour, t.localtime().tm_min, t.localtime().tm_sec]
            record(name)
            p.alert(text="录制已结束。", title="键盘和鼠标脚本生成器")
            with open(name + ".pyw", "a", encoding="utf-8") as f:
                f.write("p.alert(text=\"运行完成。\", title=\"键盘和鼠标控制器\")")
            f.close()
    elif do == "运行":
        path = p.prompt(text="请输入脚本路径", title="鼠标和键盘脚本生成器", default="D:\\")
        while True:
            try:
                f_r = open(path, "r", encoding="utf-8")
                f_lines = f_r.readlines()
                n = 0
                ctr = pynput.mouse.Controller()
                keyboard = pynput.keyboard.Controller()
                for i in f_lines:
                    if n > 6:
                        print(n)
                        eval(i)
                    n = n + 1
                f_r.close()
                break
            except Exception as r:
                print(r)
                path = p.prompt(text="运行出错啦！请重新输入脚本路径",
                                title="鼠标和键盘脚本生成器", default="D:\\")
