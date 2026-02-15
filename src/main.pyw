from basic_settings import *
from main_widgets import CheckStarted, MainWindow, WidgetBox, PlainText, SwitchButton, PushButton
from common_utilities import StopWatchWidgetBox, DropRunner, KeyDisplayerWidget, ClickerWidget, ClipboardWidget
from small_tools.small_tools_widgets import InlineCalculatorWidget, OtherToolsWidget, HotkeyGuideWidget, ChaoticPendulumWidget, KillersWidget
from mini_games.mini_games_widgets import MiniGamesWidget
from musical_lite.musical_widgets import MusicalLiteWidget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    with CheckStarted():
        window = MainWindow(app=app)
        window.add(
            InlineCalculatorWidget(parent=window), 
            window.clipboard_widget,
            window.droprunner,
            KeyDisplayerWidget(master=window),
            StopWatchWidgetBox(master=window),
            ClickerWidget(window),
            ChaoticPendulumWidget(mainwindow=window),
            KillersWidget(window),
            OtherToolsWidget(parent=window),
            MusicalLiteWidget(parent=window),
            MiniGamesWidget(parent=window),
            HotkeyGuideWidget(parent=window)
        )
        window.show()
        try:
            ret = app.exec_()
        except Exception as e:
            import traceback
            with open(SETTINGS.error_log_file, "a+", encoding="utf-8") as f:
                f.write(traceback.format_exc())
                f.write("\n\n")
            ret = 1
    print("Exiting...")
    os._exit(ret)
