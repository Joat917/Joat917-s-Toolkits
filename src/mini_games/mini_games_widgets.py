from basic_settings import *
from main_widgets import MainWindow, WidgetBox, PlainText, PushButton

def run_game(master:MainWindow, game_path:str, *args):
    if hasattr(master, 'droprunner'):
        full_path = os.path.join(SETTINGS.src_dir, 'mini_games', game_path)
        master.droprunner.run(full_path, arguments=args, without_console=True)
    else:
        master.messages.put_nowait("DropRunner not found in master window.")

class MiniGamesWidget(WidgetBox):
    def __init__(self, parent:MainWindow=None):
        super().__init__(
            parent=parent,
            title="Mini Games"
        )
        self.minesweeper_button = PushButton(
            onclick=lambda: run_game(self.master, 'msw8.py'),
            text="Minesweeper",
            width=200,
            bg_color=QColor(150, 200, 100)
        )
        self.flightchess_button = PushButton(
            onclick=lambda: run_game(self.master, 'flightChess.py'),
            text="Flight Chess",
            width=180,
            bg_color=QColor(100, 150, 250)
        )
        self.point24game_button = PushButton(
            onclick=lambda: run_game(self.master, 'Point24Game.py'),
            text="24-Point", 
            width=160,
            bg_color=QColor(250, 150, 100)
        )
        self.point24solver_button = PushButton(
            onclick=lambda: run_game(self.master, 'point24calculator_tk.pyw'),
            text="24-Point Solver", 
            width=220,
            bg_color=QColor(250, 150, 150)
        )
        self.rushhour_button = PushButton(
            onclick=lambda: run_game(self.master, 'CrossRushHour.pyw'),
            text="Rush-hour Simulator",
            width=260,
            bg_color=QColor(200, 100, 250)
        )
        self.fireshow_button = PushButton(
            onclick=lambda: run_game(self.master, 'fireshow.py'),
            text="Fire Show",
            width=160,
            bg_color=QColor(250, 200, 50)
        )

        self.line1 = QHBoxLayout()
        self.line1.addWidget(self.minesweeper_button)
        self.line1.addWidget(self.flightchess_button)

        self.line2 = QHBoxLayout()
        self.line2.addWidget(self.point24game_button)
        self.line2.addWidget(self.point24solver_button)

        self.line3 = QHBoxLayout()
        self.line3.addWidget(self.rushhour_button)
        self.line3.addWidget(self.fireshow_button)

        self.layout.addLayout(self.line1)
        self.layout.addLayout(self.line2)
        self.layout.addLayout(self.line3)
