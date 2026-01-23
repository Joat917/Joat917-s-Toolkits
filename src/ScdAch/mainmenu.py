from tkwindow import *
from eventEditor import *
from labelCalendar import *


def mainmenu():
    r = TKWindow(500, 240, rooted=True)
    r.widgets.append(TKButton(
        r.root, 200, 40, 20, 40,
        TKPrompt.text2im("事件编辑器", "simkai.ttf"),
        onclick=EventEditorWindow))
    r.widgets.append(CalendarStarter(
        r.root, x=20, y=90))
    tk.mainloop()


if __name__ == "__main__":
    mainmenu()
