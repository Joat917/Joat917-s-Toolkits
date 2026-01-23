"""
在posterer.py代码文件“烂尾”的情况下，提供一个简单的方法输出成就达成后显示的图片。
"""

from PIL import Image as Im, ImageDraw as Imd, ImageFont as Imft
from achmReader import *
import msvcrt


def rarity2clr(rarity: str):
    match rarity:
        case "普通":
            return '#fff'
        case "稀有":
            return '#f0f'
        case "传奇":
            return '#f80'
        case _:
            raise ValueError("Unknown rarity type")
    raise


def text2im(text, fontFp="C:/Windows/Fonts/simyou.ttf", fontSize=20, fontIndex=0, canvasSize=(600, 100), textColor="black"):
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


def renderIm(achievements: list[Achievement]):
    parts = []
    width = 600
    gap = 20

    for achv in achievements:
        im0 = text2im(achv.name, textColor=rarity2clr(
            achv.rarity), fontSize=50)
        im1 = text2im(achv.description, textColor='#aaa', fontSize=20)
        im2 = Im.new('RGBA', (width, im0.height+im1.height+gap))
        im2.paste(im0, (gap, 0))
        im2.paste(im1, (width-im1.width-gap, im0.height))
        parts.append(im2)
    im_o = Im.new('RGBA', (width, sum(map(lambda x: x.height, parts))))
    for i, im in enumerate(parts):
        im_o.paste(im, (0, sum(map(lambda x: x.height, parts[:i]))))
    return im_o


class AchvChooser:
    def __init__(self) -> None:
        content = AchvmReader().contents
        self.data = []
        for _l in content.values():
            self.data.extend(_l)
        self.chosen = set()
        pass

    @staticmethod
    def alp2code(ab):
        assert isinstance(ab, str) and len(ab) == 2
        tplt = 'asdfghjkl'
        ab = ab.lower()
        return tplt.index(ab[0])*len(tplt)+tplt.index(ab[1])

    @staticmethod
    def code2alp(i):
        assert isinstance(i, int) and i >= 0
        tplt = 'asdfghjkl'
        return tplt[i//len(tplt)]+tplt[i % len(tplt)]

    def prompt(self):
        print("你认为自己达成了哪些成就？")
        print("输入选项前代号进行选择/取消，确认键确定并退出")
        for i, a in enumerate(self.data):
            if a in self.chosen:
                print("- [%s]" % self.code2alp(i)+a.description)
            else:
                print("  [%s]" % self.code2alp(i)+a.description)
        print()

    def getCode(self):
        while True:
            c = msvcrt.getch()
            if c in [b'\000', b'\xe0']:
                msvcrt.getch()
            elif c in [b'\r']:
                return -1
            elif c in b'asdfghjkl':
                print(c.decode(), end='', flush=True)
                d = msvcrt.getch()
                if d in [b'\000', b'\xe0']:
                    msvcrt.getch()
                elif d in b'asdfghjkl':
                    print('\r  \r', end='')
                    return self.alp2code(c.decode()+d.decode())
                else:
                    print('\r  \r', end='')

    def mainloop(self):
        while True:
            self.prompt()
            i = self.getCode()
            if i == -1:
                return self.chosen
            else:
                try:
                    a = self.data[i]
                    if a in self.chosen:
                        self.chosen.remove(a)
                    else:
                        self.chosen.add(a)
                except IndexError:
                    print("[%s]不是有效的代码" % self.code2alp(i))


def main():
    a = AchvChooser().mainloop()
    b = sorted(a, key=lambda x: x.rarity)
    c = renderIm(b)
    c.show()


if __name__ == "__main__":
    main()
