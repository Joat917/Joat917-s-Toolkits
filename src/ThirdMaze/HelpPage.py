from BaseImport import *
from Menu import ScrollWindow, Row, Button

GAP = 10

PAGES = [Im.open(MediaPath/f'helppage{i+1}.jpg').convert('RGBA')
         for i in range(15)]
for i in range(15):
    PAGES[i] = PAGES[i].resize(
        (SCREEN_SIZE[0]-4*GAP, round((SCREEN_SIZE[0]-4*GAP)*PAGES[i].height/PAGES[i].width)))


def _get_scrollwindow():
    def _exit(): raise GameExit
    return ScrollWindow((GAP, GAP), (SCREEN_SIZE[0]-GAP*2, SCREEN_SIZE[1]-GAP*2),
                        [Row((0, 0), (SCREEN_SIZE[0]-4*GAP, round((SCREEN_SIZE[0]-4*GAP)*PAGES[0].height/PAGES[0].width)),
                             PAGES[0])]
                        + [Row((0, 0), (SCREEN_SIZE[0]-4*GAP, 60), (0,)*4, [Button(
                            None, (0, 0), (SCREEN_SIZE[0]-4*GAP, 60), (0,)*4,
                            "Exit help mode", (255, 0, 0, 255), _exit)])]
                        + [Row((0, 0), (SCREEN_SIZE[0]-4*GAP, round((SCREEN_SIZE[0]-4*GAP)*PAGES[i].height/PAGES[i].width)),
                               PAGES[i]) for i in range(1, 8)]
                        + [Row((0, 0), (SCREEN_SIZE[0]-4*GAP, 60), (0,)*4, [Button(
                            None, (0, 0), (SCREEN_SIZE[0]-4*GAP, 60), (0,)*4,
                            "Exit help mode", (255, 0, 0, 255), _exit)])]
                        + [Row((0, 0), (SCREEN_SIZE[0]-4*GAP, round((SCREEN_SIZE[0]-4*GAP)*PAGES[i].height/PAGES[i].width)),
                               PAGES[i]) for i in range(8, 15)]
                        + [Row((0, 0), (SCREEN_SIZE[0]-4*GAP, 60), (0,)*4, [Button(
                            None, (0, 0), (SCREEN_SIZE[0]-4*GAP, 60), (0,)*4,
                            "Exit help mode", (255, 0, 0, 255), _exit)])],
                        (255, 137, 201, 100), gap=10)


def helppage(window: pg.Surface, background: pg.Surface):
    sc = _get_scrollwindow()
    clock = pg.time.Clock()
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                raise SystemExit
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    raise GameExit
            if sc.handleEvent(event):
                continue
            if event.type == pg.KEYDOWN:
                if event.key in [pg.K_DOWN, pg.K_RIGHT, pg.K_PAGEDOWN]:
                    sc.scrollindex += round((SCREEN_SIZE[0]-4*GAP)
                                            * PAGES[0].height/PAGES[0].width)
                    if sc.scrollindex > sc.scolllimit:
                        sc.scrollindex = sc.scolllimit
                elif event.key in [pg.K_UP, pg.K_LEFT, pg.K_PAGEUP]:
                    sc.scrollindex -= round((SCREEN_SIZE[0]-4*GAP)
                                            * PAGES[0].height/PAGES[0].width)
                    if sc.scrollindex < 0:
                        sc.scrollindex = 0
                elif event.key in [pg.K_HOME]:
                    sc.scrollindex = 0
                elif event.key in [pg.K_END]:
                    sc.scrollindex = sc.scolllimit
        window.blit(background, (0, 0))
        sc.show(window, (10, 10))
        pg.display.flip()
        clock.tick(FPS)
