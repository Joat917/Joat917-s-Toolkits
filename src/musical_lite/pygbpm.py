import os
import time
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "shutup"

import pygame as pg
from PIL import Image as Im, ImageDraw as Imd, ImageFont as Imf
from musicallitelib import BPMDetectors
import threading

SCREENSIZE = (540, 360)
ICON_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'icon.png')
EVENT_FPS = 1024
REFRESH_FPS = 32

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

        self._fft_bpm_refresh_time = 0
        self._fft_calculating_count = 0
        self._fft_calculating_count_lock = threading.Lock()

        self._reg_bpm_refresh_time = 0

    def record(self):
        self.sample.append(time.perf_counter())
        if len(self.sample) > 1000:
            self.sample = self.sample[1:]

    def get_textbpms(self):
        if len(self.sample) <= 1:
            # bpm==0
            return ("--.--",)*4
        if self.sample[-1] == self._buffer_sample:
            # donot change
            return self._buffer_text
        else:
            _bpm_simple = BPMDetectors.get_bpm_simple(self.sample)
            _bpm_tangent = 60/(self.sample[-1]-self.sample[-2])
            threading.Thread(target=self.calc_async_bpm_reg).start()
            threading.Thread(target=self.calc_async_bpm_fft).start()
            self._buffer_text = (
                "%.2f" % _bpm_simple,
                "%.2f" % _bpm_tangent,
                self._buffer_text[2] if self._buffer_text else "--.--",
                self._buffer_text[3] if self._buffer_text else "--.--"
            )
            self._buffer_sample = self.sample[-1]
            return self._buffer_text
        
    def calc_async_bpm_reg(self):
        current_refresh_time = self.sample[-1]
        if current_refresh_time <= self._reg_bpm_refresh_time:
            return
        _bpm_reg = BPMDetectors.get_bpm_regression(self.sample)[0]
        if current_refresh_time <= self._reg_bpm_refresh_time:
            return
        self._reg_bpm_refresh_time = current_refresh_time
        self._buffer_text = (
            self._buffer_text[0] if self._buffer_text else "--.--",
            self._buffer_text[1] if self._buffer_text else "--.--",
            "%.2f" % _bpm_reg,
            self._buffer_text[3] if self._buffer_text else "--.--"
        )

        
    def calc_async_bpm_fft(self):
        current_refresh_time = self.sample[-1]
        if self._fft_calculating_count > 10:
            return
        if current_refresh_time <= self._fft_bpm_refresh_time + 0.5*self._fft_calculating_count:
            return
        
        with self._fft_calculating_count_lock:
            self._fft_calculating_count+=1
        _bpm_simple = BPMDetectors.get_bpm_simple(self.sample)
        _bpm_fft = BPMDetectors.get_bpm_fft(self.sample)      
        with self._fft_calculating_count_lock:
            self._fft_calculating_count-=1
          
        if current_refresh_time <= self._fft_bpm_refresh_time:
            return
        if _bpm_fft > 1.5*_bpm_simple:
            _bpm_fft /= max(round(_bpm_fft/_bpm_simple), 1)
        elif _bpm_fft < 0.7*_bpm_simple:
            _bpm_fft *= max(round(_bpm_simple/_bpm_fft), 1)
        if current_refresh_time <= self._fft_bpm_refresh_time:
            return
        self._fft_bpm_refresh_time = current_refresh_time
        self._buffer_text = (
            self._buffer_text[0] if self._buffer_text else "--.--",
            self._buffer_text[1] if self._buffer_text else "--.--",
            self._buffer_text[2] if self._buffer_text else "--.--",
            "%.2f" % _bpm_fft
        )

        if self._fft_calculating_count == 0 and self._fft_bpm_refresh_time < self.sample[-1]:
            threading.Thread(target=self.calc_async_bpm_fft).start()

    def clear(self):
        self.sample.clear()
        self._buffer_sample = None
        self._buffer_text = None


class CustomClock:
    def __init__(self) -> None:
        self.start_time = time.perf_counter()

    def tick(self, fps):
        current_time = time.perf_counter()
        elapsed_time = current_time - self.start_time
        wait_time = max(1.0/fps - elapsed_time, 0)
        time.sleep(wait_time)
        self.start_time = time.perf_counter()


def main():
    pg.display.set_caption("BPM Counter")
    pg.display.set_icon(pg.image.load(ICON_PATH))
    window = pg.display.set_mode(SCREENSIZE)
    count = 0
    texts = [
        Text("BPM:", (50, 30), font=Imf.truetype('arial.ttf', 72)), 
        Text("RECORD[CLICK/SPACE/ENTER/ZXCVBNM]\nCLEAR[Q/ESC]", (50, 280), font=Imf.truetype('arial.ttf', 20)),
        Text("count:%i" % count, (350, 40), font=Imf.truetype('arial.ttf', 25)), 
        Text("[Sec]", (50, 100), font=Imf.truetype('arial.ttf', 25)),
        Text("[Tan]", (300, 100), font=Imf.truetype('arial.ttf', 25)),
        Text("[Reg]", (50, 200), font=Imf.truetype('arial.ttf', 25)),
        Text("[FFT]", (300, 200), font=Imf.truetype('arial.ttf', 25)), 
        Text("--.--", (80, 120), font=Imf.truetype('arial.ttf', 60)),
        Text("--.--", (330, 120), font=Imf.truetype('arial.ttf', 60)),
        Text("--.--", (80, 220), font=Imf.truetype('arial.ttf', 60)),
        Text("--.--", (330, 220), font=Imf.truetype('arial.ttf', 60))
    ]
    ins = Instance()
    clock = CustomClock()
    _refresh = True

    while True:
        for _ in range(EVENT_FPS//REFRESH_FPS):
            clock.tick(EVENT_FPS)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    raise SystemExit
                elif event.type == pg.KEYDOWN:
                    if event.key in [pg.K_SPACE, pg.K_RETURN]+[ord(i) for i in 'zxcvbnmasdfghjkl,./;\'']:
                        ins.record()
                        count += 1
                        _refresh|=texts[2].refresh("count:%i" % count)
                    elif event.key in [pg.K_q, pg.K_ESCAPE, pg.K_DELETE]:
                        ins.clear()
                        count = 0
                        _refresh|=texts[2].refresh("count:%i" % count)
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if event.button in [1, 2, 3]:
                        ins.record()
                        count += 1
                        _refresh|=texts[2].refresh("count:%i" % count)
        _texts = ins.get_textbpms()
        for i in range(4):
            _refresh|=texts[7+i].refresh(_texts[i])
        if _refresh:
            window.fill((0, 0, 0))
            for text in texts:
                text.show(window)
            _refresh = False
            pg.display.update()


if __name__ == "__main__":
    main()
