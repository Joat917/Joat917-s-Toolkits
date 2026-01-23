import tkinter as tk
from PIL import Image as Im, ImageDraw as Imd, ImageTk as Imtk, ImageFont as Imft, ImageColor as ImClr
import cv2
import numpy as np

TRANSPARENT_CLR = '#7b7d7f'
WINDOW_BG_CLR = '#dddddd'
WINDOW_BG_CLR_DARKER = '#aaaaaa'
WINDOW_BD_CLR = 'black'

POPUP_WDP = 0  # pop up a new propmt to show message of widget destroy


class ColorUtils:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def rgb2hsv(rgb_color):
        rgb_color = np.array(rgb_color, dtype=np.uint8)
        hsv_color = cv2.cvtColor(
            rgb_color.reshape((1, 1, 3)), cv2.COLOR_RGB2HSV)
        return tuple(hsv_color[0, 0])

    @staticmethod
    def hsv2rgb(hsv_color):
        hsv_color = np.array(hsv_color, dtype=np.uint8)
        rgb_color = cv2.cvtColor(
            hsv_color.reshape((1, 1, 3)), cv2.COLOR_HSV2RGB)
        return tuple(rgb_color[0, 0])

    @staticmethod
    def darken(clr):
        if isinstance(clr, str):
            clrtup = ImClr.getrgb(clr)[:3]
        elif isinstance(clr, tuple):
            clrtup = clr
        else:
            raise ValueError
        hsvclr = ColorUtils.rgb2hsv(clrtup)
        hsvclr2 = hsvclr[0], hsvclr[1], round(hsvclr[2]*0.7)
        return ColorUtils.hsv2rgb(hsvclr2)


class TKWindow:
    def __init__(self, width: int, height: int, rooted=True, title=None):
        self.width = width
        self.height = height
        self.rooted = rooted

        if isinstance(title, str):
            self.title = title
        elif title is None:
            if rooted:
                self.title = "ROOT"
            else:
                self.title = "TK_WINDOW"
        else:
            raise TypeError("title should be string")

        if self.rooted:
            global ROOT
            ROOT = self.root = tk.Tk()
            WDPs.init()
        else:
            self.root = tk.Toplevel(ROOT)
        self.root.geometry("{}x{}+{}+{}".format(
            width, height,
            (self.root.winfo_screenwidth()-width)//2,
            (self.root.winfo_screenheight()-height)//2))
        self.root.wm_attributes('-transparentcolor', TRANSPARENT_CLR)
        self.root.wm_attributes('-topmost', True)
        self.root.config(borderwidth=0)

        self.root.overrideredirect(True)
        self.root.bind('<B1-Motion>', self.moveWindow)
        self.root.bind('<Button-1>', self._moveStart)
        self.root.bind('<ButtonRelease-1>', self._moveEnd)

        self._load_resources()

        self.bg_widget = tk.Label(self.root, image=self.bg_image_tk)
        self.bg_widget.place(relwidth=1, relheight=1)

        self.button_close = tk.Label(
            self.root, width=20, height=20, bg=WINDOW_BG_CLR)
        self.button_close.place(x=width-30, y=10)
        self.button_close.config(
            image=self.button_close_image_tk, borderwidth=0)
        self.button_close.bind('<Button-1>', self.destroy)

        def _button_close_enter(event):
            self.button_close.config(image=self.button_close_image2_tk)

        def _button_close_leave(event):
            self.button_close.config(image=self.button_close_image_tk)
        self.button_close.bind('<Enter>', _button_close_enter)
        self.button_close.bind('<Leave>', _button_close_leave)

        self.button_min = tk.Label(
            self.root, width=20, height=20, bg=WINDOW_BG_CLR)
        self.button_min.place(x=width-60, y=10)
        self.button_min.config(
            image=self.button_min_image_tk, borderwidth=0)
        self.button_min.bind('<Button-1>', self.hide)

        def _button_min_enter(event):
            self.button_min.config(image=self.button_min_image2_tk)

        def _button_min_leave(event):
            self.button_min.config(image=self.button_min_image_tk)
        self.button_min.bind('<Enter>', _button_min_enter)
        self.button_min.bind('<Leave>', _button_min_leave)

        self.title_label = tk.Label(
            self.root, width=self.title_image_tk.width(), height=20,
            image=self.title_image_tk, borderwidth=0, bg=WINDOW_BG_CLR)
        self.title_label.place(x=20, y=0)

        self._last_mouseX = None
        self._last_mouseY = None

        self.widgets = []  # put widgets here to delete it on destroy

    def moveWindow(self, event: tk.Event):
        if self._last_mouseX and self._last_mouseY:
            self.root.geometry('+{}+{}'.format(
                event.x_root-self._last_mouseX,
                event.y_root-self._last_mouseY
            ))

    def _moveStart(self, event: tk.Event):
        if event.y_root-self.root.winfo_rooty() < 40:
            self._last_mouseX = event.x_root-self.root.winfo_rootx()
            self._last_mouseY = event.y_root-self.root.winfo_rooty()

    def _moveEnd(self, *args):
        self._last_mouseX = None
        self._last_mouseY = None

    def hide(self, *args):
        self.root.wm_attributes('-alpha', 0.0)
        self._tray = TKTray(self)

    def show(self, *args):
        self.root.wm_attributes('-alpha', 1.0)
        tgt_x = max(self._tray.root.winfo_x()-self.width+70, 0)
        tgt_y = self._tray.root.winfo_y()
        if self.root.winfo_x() != tgt_x or self.root.winfo_y() != tgt_y:
            self.root.geometry("+{}+{}".format(tgt_x, tgt_y))
            if POPUP_WDP:
                TKPrompt("ERR:Cannot GM from +{}+{} to +{}+{}".format(
                    self.root.winfo_x(), self.root.winfo_y(), tgt_x, tgt_y))
            else:
                print("ERR:Cannot GM from +{}+{} to +{}+{}".format(
                    self.root.winfo_x(), self.root.winfo_y(), tgt_x, tgt_y))

    def destroy(self, *args):
        WDPs.inst.countAdd('window')
        self.root.destroy()
        for wig in self.widgets:
            try:
                wig.manualDeletion()
                del wig
            except AttributeError:
                pass

    def _load_resources(self):
        bg_image = Im.new('RGB', (self.width, self.height), TRANSPARENT_CLR)
        Imd.Draw(bg_image).rounded_rectangle(
            (0, 0, self.width-2, self.height-2), 20, WINDOW_BG_CLR, WINDOW_BD_CLR, width=2)
        self.bg_image_tk = Imtk.PhotoImage(bg_image)

        button_close_image = Im.new('RGBA', (20, 20))
        Imd.Draw(button_close_image).ellipse((0, 0, 19, 19), '#ff0000')
        self.button_close_image_tk = Imtk.PhotoImage(button_close_image)
        button_close_image2 = Im.new('RGBA', (20, 20))
        _d2 = Imd.Draw(button_close_image2)
        _d2.ellipse((0, 0, 19, 19), '#cc0000')
        _d2.line((4, 4, 15, 15), '#cccccc', width=3)
        _d2.line((4, 15, 15, 4), '#cccccc', width=3)
        self.button_close_image2_tk = Imtk.PhotoImage(button_close_image2)

        button_min_image = Im.new('RGBA', (20, 20))
        Imd.Draw(button_min_image).ellipse((0, 0, 19, 19), '#ffcc00')
        self.button_min_image_tk = Imtk.PhotoImage(button_min_image)
        button_min_image2 = Im.new('RGBA', (20, 20))
        _d2 = Imd.Draw(button_min_image2)
        _d2.ellipse((0, 0, 19, 19), '#cc9900')
        _d2.line((4, 9, 15, 9), '#cccccc', width=3)
        self.button_min_image2_tk = Imtk.PhotoImage(button_min_image2)

        button_max_image = Im.new('RGBA', (20, 20))
        Imd.Draw(button_max_image).ellipse((0, 0, 19, 19), '#44dd66')
        self.button_max_image_tk = Imtk.PhotoImage(button_max_image)
        button_max_image2 = Im.new('RGBA', (20, 20))
        _d2 = Imd.Draw(button_max_image2)
        _d2.ellipse((0, 0, 19, 19), '#229944')
        _d2.line((4, 9, 15, 9), '#cccccc', width=3)
        _d2.line((9, 4, 9, 15), '#cccccc', width=3)
        self.button_max_image2_tk = Imtk.PhotoImage(button_max_image2)

        title_image_pre = TKPrompt.text2im(self.title, fontSize=20)
        title_image = Im.new('RGB', (title_image_pre.width, 20), WINDOW_BG_CLR)
        Imd.Draw(title_image).rectangle(
            (-5, 0, title_image.width+5, 25), outline=WINDOW_BD_CLR, width=2)
        title_image.paste(title_image_pre, (0, 3),
                          title_image_pre.getchannel('A'))
        self.title_image_tk = Imtk.PhotoImage(title_image)


class TKTray(TKWindow):
    def __init__(self, target_window: TKWindow):
        self.target_window = target_window
        super().__init__(70, 40, rooted=False)
        self.root.geometry('+{}+{}'.format(
            self.target_window.root.winfo_x()+self.target_window.width-70,
            self.target_window.root.winfo_y()))
        self.button_min.config(image=self.button_max_image_tk)

        self.button_min.unbind_all('<Button-1>')
        self.button_min.unbind_all('<Enter>')
        self.button_min.unbind_all('<Leave>')

        def _button_min_click(event):
            tgt_x = self.root.winfo_x()-self.target_window.width+70
            tgt_y = self.root.winfo_y()
            self.target_window.show()
            self.target_window.root.geometry('+{}+{}'.format(tgt_x, tgt_y))
            # TKPrompt('+{}+{}:+{}+{}'.format(
            #     tgt_x, tgt_y,
            #     self.target_window.root.winfo_x(),
            #     self.target_window.root.winfo_y()))

            TKWindow.destroy(self)

        def _button_min_enter(event):
            self.button_min.config(image=self.button_max_image2_tk)

        def _button_min_leave(event):
            self.button_min.config(image=self.button_max_image_tk)

        self.button_min.bind('<Button-1>', _button_min_click)
        self.button_min.bind('<Enter>', _button_min_enter)
        self.button_min.bind('<Leave>', _button_min_leave)

        self.title_label.destroy()

    def destroy(self, *args):
        self.target_window.destroy()
        TKWindow.destroy(self)


class TKPrompt:
    prompts = []

    def __init__(self, text="tk.prompt.", timeout=3., topDownBorder=4):
        pre_image = self.text2im(text)
        image = Im.new('RGB', (pre_image.width+pre_image.height,
                       pre_image.height+2*topDownBorder), TRANSPARENT_CLR)
        imd = Imd.Draw(image)
        imd.rectangle((pre_image.height/2, 0,
                       pre_image.width+pre_image.height/2, image.height),
                      WINDOW_BG_CLR)
        imd.ellipse((0, 0, pre_image.height, image.height),
                    WINDOW_BG_CLR)
        imd.ellipse((pre_image.width, 0,
                     pre_image.width+pre_image.height, image.height),
                    WINDOW_BG_CLR)
        image.paste(pre_image, (pre_image.height//2, topDownBorder),
                    pre_image.getchannel('A'))
        self.image = image
        self.imagetk = Imtk.PhotoImage(self.image)
        self.window = tk.Toplevel(ROOT)
        self.window.overrideredirect(True)
        self.window.geometry("{}x{}+{}+{}".format(
            self.image.width, self.image.height,
            (ROOT.winfo_screenwidth()-self.image.width)//2,
            ROOT.winfo_screenheight()-100))
        self.window.config(borderwidth=0)
        self.window.wm_attributes("-transparentcolor", TRANSPARENT_CLR)
        self.window.wm_attributes("-alpha", 0.8)
        self.window.wm_attributes("-topmost", True)
        self.label = tk.Label(self.window, image=self.imagetk)
        self.label.place(relheight=1, relwidth=1)
        self.prompts.append(self)
        self.timeout = timeout
        self.fadeInCount = 16
        self.fadeOutCount = 16
        self.fadeIn()

    def fadeIn(self, *args):
        if self.fadeInCount:
            self.fadeInCount -= 1
            self.window.wm_attributes("-alpha", 0.8-0.05*self.fadeInCount)
            self.window.geometry("+{}+{}".format(
                (ROOT.winfo_screenwidth()-self.image.width)//2,
                ROOT.winfo_screenheight()-100+2*self.fadeInCount))
            self.window.after(20, self.fadeIn)
        else:
            self.window.after(round(self.timeout*1000), self.fadeOut)

    def fadeOut(self, *args):
        if self.fadeOutCount:
            self.fadeOutCount -= 1
            self.window.wm_attributes("-alpha", 0.05*self.fadeOutCount)
            self.window.after(20, self.fadeOut)
        else:
            self.destroy()

    def destroy(self, *args):
        self.window.destroy()
        delattr(self, "image")
        delattr(self, "imagetk")
        try:
            self.prompts.remove(self)
        except ValueError:
            return

    @staticmethod
    def text2im(text, fontFp="bahnschrift.ttf", fontSize=20, fontIndex=0, canvasSize=(400, 40), textColor="black"):
        font = Imft.truetype(fontFp, fontSize, fontIndex)
        canvas = Im.new('RGBA', canvasSize)
        Imd.Draw(canvas).text((0, 0), text, textColor, font)
        for row in range(canvas.height):
            for col in range(canvas.width):
                if canvas.getpixel((col, row))[3]:
                    top = row
                    break
            else:
                continue
            break
        else:
            raise RuntimeError("Empty text!")
        for col in range(canvas.width):
            for row in range(canvas.height):
                if canvas.getpixel((col, row))[3]:
                    left = col
                    break
            else:
                continue
            break
        else:
            raise RuntimeError("Empty text!")
        for row in range(canvas.height-1, -1, -1):
            for col in range(canvas.width):
                if canvas.getpixel((col, row))[3]:
                    bottom = row
                    break
            else:
                continue
            break
        else:
            raise RuntimeError("Empty text!")
        for col in range(canvas.width-1, -1, -1):
            for row in range(canvas.height):
                if canvas.getpixel((col, row))[3]:
                    right = col
                    break
            else:
                continue
            break
        else:
            raise RuntimeError("Empty text!")
        del font
        return canvas.crop((left, top, right+1, bottom+1))


class TKButton:
    def __init__(self, master: tk.Toplevel | tk.Tk, width: int, height: int,
                 x: int, y: int, pasted: Im.Image, onclick=lambda: None,
                 bgColor="#febadc", bgColor2="#ba7698"):
        self.master = master
        self.width = width
        self.height = height
        self._onclick = onclick
        self.bgColor = bgColor
        self.bgColor2 = bgColor2
        self.x = x
        self.y = y

        self.image = Im.new('RGB', (self.width, self.height), WINDOW_BG_CLR)
        Imd.Draw(self.image).rounded_rectangle(
            (0, 0, self.width, self.height), 20, self.bgColor)
        self.image.paste(pasted, ((self.width-pasted.width)//2,
                                  (self.height-pasted.height)//2),
                         pasted.getchannel('A'))
        self.image_tk = Imtk.PhotoImage(self.image)

        self.image2 = Im.new('RGB', (self.width, self.height), WINDOW_BG_CLR)
        Imd.Draw(self.image2).rounded_rectangle(
            (0, 0, self.width, self.height), 20, self.bgColor2)
        self.image2.paste(pasted, ((self.width-pasted.width)//2,
                                   (self.height-pasted.height)//2),
                          pasted.getchannel('A'))
        self.image2_tk = Imtk.PhotoImage(self.image2)

        self.widget = tk.Label(self.master, image=self.image_tk, borderwidth=0)
        self.widget.bind('<Enter>', self.onEnter)
        self.widget.bind('<Leave>', self.onLeave)
        self.widget.bind('<Button-1>', self.onClick)
        self.widget.place(x=self.x, y=self.y)

    def onEnter(self, *args):
        self.widget.config(image=self.image2_tk)

    def onLeave(self, *args):
        self.widget.config(image=self.image_tk)

    def onClick(self, *args):
        self._onclick()

    def manualDeletion(self):
        "Since TKButton objects cannot delete on itself, THIS FUNCTION MUST BE CALLED TO AVOID MEMORY LEAKAGE!!!"
        try:
            self.widget.destroy()
        except Exception:
            pass
        # delattr(self, "image")
        # delattr(self, "image2")
        # delattr(self, "image_tk")
        # delattr(self, "image2_tk")
        for _name in dir(self):
            if _name.startswith('__'):
                continue
            try:
                delattr(self, _name)
            except AttributeError:
                pass

    def __del__(self):
        WDPs.inst.countAdd('widget')
        try:
            self.widget.destroy()
        except Exception:
            pass


class TKCheckBox:
    def __init__(self, master: tk.Toplevel | tk.Tk, width: int, height: int,
                 x: int, y: int, pasted: Im.Image, onCheck=lambda: None, onUncheck=lambda: None,
                 bgColorCheck="#febadc", bgColorCheck2="#ba7698",
                 bgColorUncheck=WINDOW_BG_CLR, bgColorUncheck2=WINDOW_BG_CLR_DARKER, checked=False):
        self.master = master
        self.width = width
        self.height = height
        self._onCheck = onCheck
        self._onUncheck = onUncheck
        self.bgColorCheck = bgColorCheck
        self.bgColorCheck2 = bgColorCheck2
        self.bgColorUncheck = bgColorUncheck
        self.bgColorUncheck2 = bgColorUncheck2
        self.x = x
        self.y = y
        self.checked = checked

        def _getImg(clr):
            im = Im.new('RGB', (self.width, self.height), WINDOW_BG_CLR)
            Imd.Draw(im).rounded_rectangle(
                (0, 0, self.width, self.height), 20, clr)
            im.paste(pasted, ((self.width-pasted.width)//2,
                              (self.height-pasted.height)//2),
                     pasted.getchannel('A'))
            return Imtk.PhotoImage(im)

        self.imtkCheck = _getImg(self.bgColorCheck)
        self.imtkCheck2 = _getImg(self.bgColorCheck2)
        self.imtkUncheck = _getImg(self.bgColorUncheck)
        self.imtkUncheck2 = _getImg(self.bgColorUncheck2)

        if self.checked:
            self.widget = tk.Label(
                self.master, image=self.imtkCheck, borderwidth=0)
        else:
            self.widget = tk.Label(
                self.master, image=self.imtkUncheck, borderwidth=0)
        self.widget.bind('<Enter>', self.onEnter)
        self.widget.bind('<Leave>', self.onLeave)
        self.widget.bind('<Button-1>', self.onClick)
        self.widget.place(x=self.x, y=self.y)

    def onEnter(self, *args):
        if self.checked:
            self.widget.config(image=self.imtkCheck2)
        else:
            self.widget.config(image=self.imtkUncheck2)

    def onLeave(self, *args):
        if self.checked:
            self.widget.config(image=self.imtkCheck)
        else:
            self.widget.config(image=self.imtkUncheck)

    def onClick(self, *args):
        if self.checked:
            self._onUncheck()
            self.widget.config(image=self.imtkUncheck2)
            self.checked = False
        else:
            self._onCheck()
            self.widget.config(image=self.imtkCheck2)
            self.checked = True

    def manualDeletion(self):
        self.widget.destroy()
        for _name in dir(self):
            if not _name.startswith('__'):
                try:
                    delattr(self, _name)
                except AttributeError:
                    pass

    def __del__(self):
        WDPs.inst.countAdd('widget')
        try:
            del self.imtkCheck, self.imtkCheck2, self.imtkUncheck, self.imtkUncheck2
            self.widget.destroy()
        except Exception:
            pass


class TKMultiSelect:
    def __init__(self, master: tk.Toplevel | tk.Tk, width: int, height: int,
                 x: int, y: int, pastes: list[Im.Image], onClick=lambda: None,
                 optFuncs=[], optColors=[], optColors2=None, defaultIndex=0):
        self.master = master
        self.width = width
        self.height = height
        self._onClick = onClick
        self.optFuncs = optFuncs
        self.optColors = optColors
        if optColors2 is not None:
            self.optColors2 = optColors2
        else:
            self.optColors2 = [ColorUtils.darken(i) for i in self.optColors]
        if not len(self.optFuncs) == len(self.optColors) == len(self.optColors2) == len(pastes):
            raise ValueError("option parameters mustbe in same length")
        self.length = len(self.optFuncs)
        self.x = x
        self.y = y
        self.ind = defaultIndex % self.length

        def _getim(clr, pasted):
            im = Im.new('RGB', (self.width, self.height), WINDOW_BG_CLR)
            Imd.Draw(im).rounded_rectangle(
                (0, 0, self.width, self.height), 20, clr)
            im.paste(pasted, ((self.width-pasted.width)//2,
                              (self.height-pasted.height)//2),
                     pasted.getchannel('A'))
            return Imtk.PhotoImage(im)

        self.imtks = []
        self.imtks2 = []
        for _i in range(self.length):
            self.imtks.append(_getim(self.optColors[_i], pastes[_i]))
            self.imtks2.append(_getim(self.optColors2[_i], pastes[_i]))

        self.widget = tk.Label(
            self.master, image=self.imtks[self.ind], borderwidth=0)

        self.widget.bind('<Enter>', self.onEnter)
        self.widget.bind('<Leave>', self.onLeave)
        self.widget.bind('<Button-1>', self.onClick)
        self.widget.place(x=self.x, y=self.y)

    def onEnter(self, *args):
        self.widget.config(image=self.imtks2[self.ind])

    def onLeave(self, *args):
        self.widget.config(image=self.imtks[self.ind])

    def onClick(self, *args):
        self.ind = (self.ind+1) % self.length
        self.widget.config(image=self.imtks2[self.ind])
        self._onClick()
        self.optFuncs[self.ind]()

    def manualDeletion(self):
        self.widget.destroy()
        for _name in dir(self):
            if not _name.startswith('__'):
                try:
                    delattr(self, _name)
                except AttributeError:
                    pass

    def __del__(self):
        WDPs.inst.countAdd('widget')
        try:
            self.widget.destroy()
        except Exception:
            pass


class WDPs:
    "Widget Destroyed Prompts"
    inst = None

    def __init__(self, refreshTimeout=1):
        if WDPs.inst is None:
            WDPs.inst = self
        else:
            raise RuntimeError("WDP instance already exists")
        self.data = {}
        self.refreshTimeout = refreshTimeout

        ROOT.after(self.refreshTimeout*1000, self.showClearInfo)

    @classmethod
    def init(cls):
        if cls.inst:
            return cls.inst
        else:
            return cls()

    def __getitem__(self, ind):
        try:
            return self.data[ind]
        except KeyError:
            return 0

    def __setitem__(self, ind, val):
        self.data[ind] = val

    def countAdd(self, ind):
        try:
            self.data[ind] += 1
        except KeyError:
            self.data[ind] = 1

    def countClear(self):
        self.data.clear()

    def showClearInfo(self):
        ROOT.after(self.refreshTimeout*1000, self.showClearInfo)
        if not self.data:
            return
        o = "Cleared "+', '.join(
            '{} {}'.format(_v, _k) for _k, _v in self.data.items() if _v)
        if POPUP_WDP:
            TKPrompt(o)
        else:
            print(o)
        self.countClear()
        return


class Scroller:
    def __init__(self, master: tk.Toplevel | tk.Tk, width: int, height: int,
                 x: int, y: int):
        self.master = master
        self.root = tk.Frame(
            master=master, width=width+14, height=height,
            borderwidth=0, bg=WINDOW_BG_CLR)
        self.root.place(x=x, y=y)
        self.width = width
        self.height = height

        self._widgets = []
        self.widget_ys = []
        self.widget_gap = 6
        self.widget_heights = -self.widget_gap

        self._scroll_offset = 0

        self._widgets: list[ScrollerWidget]
        self.widget_ys: list[int]

        self.mouseScrollerActive = False
        self.root.bind('<Enter>', self.onEnter)
        self.root.bind('<Leave>', self.onLeave)
        self.root.master.bind('<MouseWheel>', self.onScroll)

        self._scroll_control_bar = ScrollControlBar(self)
        return

    @property
    def scroll_offset(self):
        return self._scroll_offset

    @staticmethod
    def get_bg_imtk(width, height, borderColor=WINDOW_BD_CLR):
        im = Im.new('RGB', (width, height), WINDOW_BG_CLR)
        Imd.Draw(im).rounded_rectangle(
            (0, 0, width, height), 20,
            WINDOW_BG_CLR, borderColor, 2)
        return Imtk.PhotoImage(im)

    @scroll_offset.setter
    def scroll_offset(self, new_offset):
        if new_offset > self.widget_heights-self.height:
            new_offset = self.widget_heights-self.height
        if new_offset < 0:
            new_offset = 0
        if self._scroll_offset != new_offset:
            self._scroll_offset = new_offset
            for i in range(len(self._widgets)):
                self._widgets[i].root.place(
                    y=self.widget_ys[i]-self._scroll_offset)
        self._scroll_control_bar.onMotion()

    def appendWidget(self, widget):
        if not isinstance(widget, ScrollerWidget):
            raise TypeError
        self._widgets.append(widget)
        self.widget_ys.append(self.widget_heights+self.widget_gap)
        self.widget_heights += widget.height+self.widget_gap
        widget.root.place(
            x=0, y=self.widget_ys[-1]-self.scroll_offset)
        self._scroll_control_bar.onRefresh()
        return

    def removeWidget(self, widget):
        if not isinstance(widget, ScrollerWidget):
            raise TypeError
        i = self._widgets.index(widget)
        self._widgets[i].root.destroy()
        for wig in self._widgets[i].widgets:
            try:
                wig.manualDeletion()
            except AttributeError:
                pass
        dh = self._widgets.pop(i).height+self.widget_gap

        self.widget_heights -= dh
        if self.scroll_offset > self.widget_heights:
            self.scroll_offset = self.widget_heights
        if self.scroll_offset < 0:
            self.scroll_offset = 0

        for j in range(i, len(self._widgets)-1):
            self.widget_ys[j] = self.widget_ys[j+1]-dh
            self._widgets[j].root.place(
                y=self.widget_ys[j]-self.scroll_offset)
        self.widget_ys.pop()
        self._scroll_control_bar.onRefresh()
        return

    def onEnter(self, event: tk.Event):
        self.mouseScrollerActive = True

    def onLeave(self, event: tk.Event):
        self.mouseScrollerActive = False

    def onScroll(self, event: tk.Event):
        if self.mouseScrollerActive:
            self.scroll_offset -= event.delta//8

    def manualDeletion(self):
        for scwig in self._widgets:
            scwig.root.destroy()
            for wig in scwig.widgets:
                try:
                    wig.manualDeletion()
                except AttributeError:
                    pass
        self.root.destroy()
        self._scroll_control_bar.wig

    def __del__(self):
        WDPs.inst.countAdd('scroller')


class ScrollControlBar:
    def __init__(self, scroller: Scroller):
        self.scroller = scroller
        self.wig = tk.Label(scroller.root, borderwidth=0,
                            width=12, height=self.scroller.height,
                            bg=WINDOW_BG_CLR)
        self.wig.place(x=self.scroller.width, y=0)
        self.enabled = (
            self.scroller.widget_heights <= self.scroller.height)
        self.onRefresh()

        self._mouse_in = False
        self._mouse_last_y_off = None

        self.wig.bind('<Enter>', self.onEnter)
        self.wig.bind('<Leave>', self.onLeave)
        self.wig.bind('<B1-Motion>', self.onMotion)
        self.wig.bind('<Button-1>', self.onClick)
        self.wig.bind('<ButtonRelease-1>', self.onRelease)
        return

    def onRefresh(self, *args):
        if self.scroller.widget_heights <= self.scroller.height:
            if self.enabled:
                self.enabled = False
                self.beta = None
                self.imtk = self.imtkRoundBar(
                    12, self.scroller.height, 'white')
                self.wig.config(image=self.imtk, height=self.scroller.height)
                self.wig.place(y=0)
        else:
            new_beta = self.scroller.height/self.scroller.widget_heights
            if not self.enabled or self.beta != new_beta:
                self.enabled = True
                self.beta = new_beta
                self.imtk = self.imtkRoundBar(
                    12, self.beta*self.scroller.height, 'white')
                self.wig.config(image=self.imtk, height=self.imtk.height())
                self.wig.place(y=self.scroller.scroll_offset*self.beta)

    def onClick(self, event: tk.Event):
        if self.enabled and self._mouse_in:
            self._mouse_last_y_off = -event.y_root+self.scroller.scroll_offset

    def onRelease(self, e):
        self._mouse_last_y_off = None

    def onMotion(self, event: tk.Event = None):
        if event is None:
            if self.beta is not None:
                self.wig.place(y=self.scroller.scroll_offset*self.beta)
            else:
                self.wig.place(y=0)
            return
        if self._mouse_last_y_off:
            self.scroller.scroll_offset = (
                event.y_root+self._mouse_last_y_off)/self.beta
            self.wig.place(y=self.scroller.scroll_offset*self.beta)

    def onEnter(self, e):
        self._mouse_in = True

    def onLeave(self, e):
        self._mouse_in = False

    @staticmethod
    def imtkRoundBar(width: int | float, height: int | float, color: str | tuple):
        width = round(width)
        height = round(height)
        im = Im.new('RGB', (width, height), WINDOW_BG_CLR)
        Imd.Draw(im).rounded_rectangle(
            (0, 0, width, height), radius=width//2, fill=color)
        return Imtk.PhotoImage(im)

    def __del__(self):
        WDPs.inst.countAdd('widget')


class ScrollerWidget:
    def __init__(self, scroller: Scroller, height: int, borderColor=WINDOW_BD_CLR):
        self.width = scroller.width
        self.height = height
        self.root = tk.Frame(
            scroller.root, width=self.width, height=self.height)

        self.imtk_bg = Scroller.get_bg_imtk(
            self.width, self.height, borderColor)
        self.bg_widget = tk.Label(self.root, image=self.imtk_bg, borderwidth=0)
        self.bg_widget.place(relheight=1, relwidth=1)

        self.widgets = []

    def __del__(self):
        WDPs.inst.countAdd('widget')


if __name__ == "__main__":
    def main():
        a = TKWindow(150, 60)
        b = TKWindow(300, 400, False)
        c = TKButton(b.root, 110, 30, 26, 47, TKPrompt.text2im(
            "!Button!"), lambda: TKPrompt("Button Clicked!"))
        d = TKCheckBox(b.root, 110, 30, 36, 85,
                       TKPrompt.text2im("CheckIt~"),
                       lambda: TKPrompt("CheckBox on"),
                       lambda: TKPrompt("CheckBox off"))
        e = TKMultiSelect(b.root, 110, 30, 43, 131,
                          [TKPrompt.text2im("Status%i" % i)
                           for i in range(1, 7)],
                          optFuncs=[(lambda: TKPrompt("Switched to Status%i" % i))
                                    for i in range(1, 7)],
                          optColors=[ColorUtils.hsv2rgb((i*30, 0x66, 0xff)) for i in range(6)])

        b2 = Scroller(b.root, 200, 150, 20, 180)
        c2 = ScrollerWidget(b2, 120, 'black')
        b2.appendWidget(c2)
        d2 = ScrollerWidget(b2, 120, 'blue')
        b2.appendWidget(d2)
        e2 = TKButton(d2.root, 110, 30, 20, 20, TKPrompt.text2im(
            ">Button<"), lambda: TKPrompt("Button Clicked>_<"))
        d2.widgets.append(e2)
        tk.mainloop()

    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        input("...")
