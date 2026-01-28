"""
这是一个负责任的测量bpm的程序。应用上所有输入而不只是首尾的两个。收敛极快。支持漏拍，漏拍并不会造成任何误差。
优化：减少了不必要的CPU消耗。
"""

import pygame as pg
from PIL import Image as Im, ImageDraw as Imd, ImageFont as Imf
from time import time
from math import *
import numpy as np


SCREENSIZE = (540, 360)
BACKGROUND = pg.image.frombuffer(
    Im.new('RGBA', SCREENSIZE, (0, 0, 0, 255)).tobytes(), SCREENSIZE, 'RGBA')


def covalue(a, b, sigma=1/64):
    return exp(-(b-a)**2/(2*sigma)**2)


def deal_with_sample(sample, gap=1/256):
    "return max freq"
    t0 = sample[0]
    t1 = sample[-1]
    vl = []
    t = t0
    while t < t1:
        v = 0
        for i in sample:
            if abs(i-t) < 1/8:
                v += covalue(i, t)
        vl.append(v)
        t += gap

    vl = np.array(vl, dtype=np.float64)
    vl -= np.mean(vl)
    sm = abs(np.fft.fft(vl))
    sm = sm.tolist()
    tm = np.fft.fftfreq(len(vl), gap)
    freq = tm.tolist()[sm.index(max(sm))]
    return abs(freq)


def getapprox(sample):
    return len(sample)/(sample[-1]-sample[0])


def getbpm(sample):
    freq1 = deal_with_sample(sample)
    freqs = getapprox(sample)
    times = max(round(freq1/freqs), 1)
    return freq1*60/times


class Text:
    def __init__(self, text: str, pos=(0, 0), color=(255, 255, 255, 255), font=Imf.truetype('arial.ttf', 96)) -> None:
        self.text = text
        self.pos = pos
        self.color = color
        self.font = font
        self.image = Im.new('RGBA', SCREENSIZE)
        Imd.Draw(self.image).text((0, 0), self.text, self.color, self.font)
        self.cover = pg.image.frombuffer(
            self.image.tobytes(), SCREENSIZE, 'RGBA')

    def show(self, window):
        window.blit(self.cover, self.pos)

    def refresh(self, text):
        if text == self.text:
            return False
        else:
            self.text = text
            self.image = Im.new('RGBA', SCREENSIZE)
            Imd.Draw(self.image).text((0, 0), self.text, self.color, self.font)
            self.cover = pg.image.frombuffer(
                self.image.tobytes(), SCREENSIZE, 'RGBA')
            return True


class Instance:
    def __init__(self) -> None:
        self.sample = []
        self._buffer_sample = None
        self._buffer_text = None

    def record(self):
        self.sample.append(time())
        if len(self.sample) > 1000:
            self.sample = self.sample[1:]

    def get_textbpm(self):
        if len(self.sample) <= 1:
            # bpm==0
            return "--.--"
        if self.sample[-1] == self._buffer_sample:
            # donot change
            return self._buffer_text
        else:
            self._buffer_text = str(round(getbpm(self.sample), 2))
            while len(self._buffer_text[self._buffer_text.index("."):]) < 3:
                self._buffer_text += "0"
            self._buffer_sample = self.sample[-1]
            return self._buffer_text

    def clear(self):
        self.sample.clear()
        self._buffer_sample = None
        self._buffer_text = None


def main():
    window = pg.display.set_mode(SCREENSIZE)
    count = 0
    texts = [Text("BPM:\n--.--", (50, 50)), Text(
        "RECORD[CLICK/SPACE/ENTER/ZXCVBNM]\nCLEAR[Q/ESC]", (100, 280), font=Imf.truetype('arial.ttf', 20)),
        Text("count:%i" % count, (350, 40), font=Imf.truetype('arial.ttf', 25))]
    ins = Instance()
    clock = pg.time.Clock()
    _refresh = True

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                raise SystemExit
            elif event.type == pg.KEYDOWN:
                if event.key in [pg.K_SPACE, pg.K_RETURN]+[ord(i) for i in 'zxcvbnmasdfghjkl,./;\'']:
                    ins.record()
                    count += 1
                    texts[2].refresh("count:%i" % count)
                    _refresh = True
                elif event.key in [pg.K_q, pg.K_ESCAPE, pg.K_DELETE]:
                    ins.clear()
                    count = 0
                    texts[2].refresh("count:%i" % count)
                    _refresh = True
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button in [1, 2, 3]:
                    ins.record()
                    count += 1
                    texts[2].refresh("count:%i" % count)
                    _refresh = True
        if _refresh:
            texts[0].refresh("BPM:\n"+ins.get_textbpm())
            window.blit(BACKGROUND, (0, 0))
            for text in texts:
                text.show(window)
            _refresh = False
            pg.display.update()
        clock.tick(40)


if __name__ == "__main__":
    main()
