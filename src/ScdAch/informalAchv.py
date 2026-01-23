"""
输出不在成就表格内的成就
"""

from PIL import Image as Im, ImageDraw as Imd, ImageFont as Imft
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


class Achievement:
    def __init__(self, name, rarity, description) -> None:
        self.name=name
        self.rarity=rarity
        self.description=description

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
        self.chosen=[]
        pass

    def prompt(self):
        print("你认为自己达成了什么成就？")

    def getCode(self):
        while True:
            name=input("名称：").strip()
            if not name:
                return -1
            rarity=""
            while True:
                _r=input("稀有度（普通(1)/稀有(2)/传奇(3)）")
                match _r:
                    case '1':
                        rarity="普通"
                        break
                    case '2':
                        rarity="稀有"
                        break
                    case '3':
                        rarity="传奇"
                        break
            description=input("描述：").strip()
            self.chosen.append(Achievement(name, rarity, description))
            return 0
            

    def mainloop(self):
        while True:
            self.prompt()
            i = self.getCode()
            if i == -1:
                return self.chosen
            else:
                pass


def main():
    a = AchvChooser().mainloop()
    b = sorted(a, key=lambda x: x.rarity)
    c = renderIm(b)
    c.show()


if __name__ == "__main__":
    main()
