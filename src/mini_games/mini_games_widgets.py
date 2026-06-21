from basic_settings import *
from main_widgets import MainWindow, WidgetBox, PlainText, PushButton, has_lib
cl=PushButton.color_shorthand

def run_game(master:MainWindow, game_path:str, without_console=True, *args):
    if hasattr(master, 'droprunner'):
        full_path = os.path.join(SETTINGS.src_dir, 'mini_games', game_path)
        master.droprunner.run(full_path, arguments=args, without_console=without_console)
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
            bg_color=cl(311)
        )
        self.spherical_minesweeper_button = PushButton(
            onclick=lambda: run_game(self.master, 'msw_spherical.py'),
            text="... on Sphere",
            bg_color=cl(312)
        )
        self.flightchess_button = PushButton(
            onclick=lambda: run_game(self.master, 'flightChess.py'),
            text="Flight Chess",
            bg_color=cl(124)
        )
        self.autoflightchess_button = PushButton(
            onclick=lambda: run_game(self.master, 'flightchesslib.py'),
            text="... AutoPlay", 
            bg_color=cl(134)
        )
        self.point24game_button = PushButton(
            onclick=lambda: run_game(self.master, 'Point24Game.py'),
            text="24-Point", 
            bg_color=cl(421)
        )
        self.point24solver_button = PushButton(
            onclick=lambda: run_game(self.master, 'point24calculator_tk.pyw'),
            text="24-Point Solver", 
            bg_color=cl(422)
        )
        self.numguess_button = PushButton(
            onclick=lambda: run_game(self.master, 'NUMGUESS410_GUI.pyw'),
            text="4-dig Number Guessing",
            bg_color=cl(321)
        )
        self.numguess_solver_button = PushButton(
            onclick=lambda: run_game(self.master, 'NUMGUESS410_attack.py', without_console=False),
            text="... Solver",
            bg_color=cl(322)
        )
        self.rushhour_button = PushButton(
            onclick=lambda: run_game(self.master, 'CrossRushHour.pyw'),
            text="Rush-hour Simulator",
            bg_color=cl(231)
        )
        self.fireshow_button = PushButton(
            onclick=lambda: run_game(self.master, 'fireshow.py'),
            text="Fire Show",
            bg_color=cl(223)
        )
        self.thirdmaze_button = PushButton(
            onclick=lambda: self.master.droprunner.run(os.path.join(SETTINGS.src_dir, 'ThirdMaze', 'MainMenu.py'), run_dir=SETTINGS.src_dir, without_console=True),
            text="ThirdMaze",
            bg_color=cl(331)
        )
        self.fstimer_button = PushButton(
            onclick=lambda: self.master.droprunner.run(os.path.join(SETTINGS.src_dir, 'FSTimer', 'FSTimer3.pyw'), run_dir=SETTINGS.src_dir, without_console=True),
            text="FSTimer",
            bg_color=cl(431)
        )
        self.fsviewer_button = PushButton(
            onclick=lambda: self.master.droprunner.run(os.path.join(SETTINGS.src_dir, 'FSTimer', 'FSViewer3.pyw'), run_dir=SETTINGS.src_dir, without_console=True),
            text="FSViewer",
            bg_color=cl(431)
        )
        self.klotski_button = PushButton(
            onclick=lambda: run_game(self.master, 'puzzle15game.py'),
            text="Digital Klotski",
            bg_color=cl(322)
        )

        if has_lib("pygame"):(
            self
            .addLine(self.minesweeper_button, 
                     self.spherical_minesweeper_button if has_lib("scipy", "networkx") else None
                    )
            .addLine(self.flightchess_button,
                     self.autoflightchess_button if has_lib("cv2") else None
                     )
            .addLine(self.point24game_button, self.point24solver_button)
            .addLine(self.numguess_button, self.numguess_solver_button)
            .addLine(self.rushhour_button, self.fireshow_button)
            .addLine(self.fstimer_button, self.fsviewer_button)
            .addLine(self.thirdmaze_button, self.klotski_button if has_lib("cv2") else None)
        )
        else:
            self.addLine(PlainText("Install Pygame to unlock mini games!"))
        
