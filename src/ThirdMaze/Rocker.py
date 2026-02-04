from BaseImport import *


class Media:
    def __init__(self):
        self.background = Im.new('RGB', (1000, 1000), (200, 191, 231))
        self.backgroundcover = self.im2pg(self.background, 'RGB')
        self.img = Im.new("RGBA", (ROCKER_RADIUS*2+2, ROCKER_RADIUS*2+2))
        draw = Imd.Draw(self.img)
        draw.ellipse((0, 0, ROCKER_RADIUS*2, ROCKER_RADIUS*2),
                     fill=(128, 128, 128, 64), outline=(255, 255, 255, 216), width=5)
        self.imgcover = self.im2pg(self.img)

        self.handle = Im.new('RGBA', (ROCKER_HANDLE_RADIUS*2+2,
                                      ROCKER_HANDLE_RADIUS*2+2))
        Imd.Draw(self.handle).ellipse((0, 0, ROCKER_HANDLE_RADIUS*2, ROCKER_HANDLE_RADIUS*2),
                                      fill=(255, 255, 255, 216))
        self.handlecover = self.im2pg(self.handle)

    @staticmethod
    def im2pg(im: Im.Image, format='RGBA'):
        return pg.image.frombuffer(im.tobytes(), im.size, format)


media = Media()


class Rocker:
    def __init__(self, main, x, y):
        self.main = main
        self.x = x
        self.y = y
        self.top = self.y-ROCKER_RADIUS
        self.left = self.x-ROCKER_RADIUS
        self.mousedown = False
        self.handle_pos = self.x, self.y

    def __contains__(self, pos: tuple):
        return (pos[0]-self.x)**2+(pos[1]-self.y)**2 <= ROCKER_RADIUS**2

    def dealevent(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                if pg.mouse.get_pos() in self:
                    self.mousedown = True
                else:
                    self.mousedown = False
        elif event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                self.mousedown = False

    def show(self):
        if self.mousedown:
            self.handle_pos = pg.mouse.get_pos()
            if not self.handle_pos in self:
                phi = phase(complex(self.handle_pos[0]-self.x,
                                    self.handle_pos[1]-self.y))
                self.handle_pos = ROCKER_RADIUS*cos(phi)+self.x, \
                    ROCKER_RADIUS*sin(phi)+self.y
        else:
            self.handle_pos = self.x, self.y
        self.main.window.blit(media.handlecover,
                              (self.handle_pos[0]-ROCKER_HANDLE_RADIUS, self.handle_pos[1]-ROCKER_HANDLE_RADIUS))
        self.main.window.blit(media.imgcover, (self.left, self.top))

    def getdirection(self):
        if not self.mousedown or abs(complex(self.handle_pos[0]-self.x,
                                             self.handle_pos[1]-self.y)) <= 20:
            return 0
        else:
            out = 0
            phi = phase(complex(self.handle_pos[0]-self.x,
                                self.handle_pos[1]-self.y))
            if cos(phi) >= 0:
                out |= R
            if cos(phi-radians(120)) >= 0:
                out |= TL
            if cos(phi+radians(120)) >= 0:
                out |= BL
            return out


class Main:
    def __init__(self) -> None:
        self.window = pg.display.set_mode((480, 480))
        self.clock = pg.time.Clock()
        self.rocker = Rocker(self, 220, 220)

    def mainloop(self):
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    raise SystemExit
                self.rocker.dealevent(event)

            self.window.blit(media.backgroundcover, (0, 0))
            self.rocker.show()
            print('\r%i' % self.rocker.getdirection(), end='')

            pg.display.update()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Main().mainloop()
