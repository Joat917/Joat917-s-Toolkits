from base_import import *
from start_check import check_started
from main_window import MainWindow, WidgetBox
from stop_watch import StopWatchMainWindow
from switch_widgets import SwitchButton
from drop_runner import DropRunner
from keyboard_displayer import KeyDisplayerManager

if __name__ == "__main__":
    app = QApplication(sys.argv)
    check_started()
    MainWindow.TITLE = "Joat917's Toolkit"
    window = MainWindow(app=app)

    stopwatch = []
    window.addWidget(WidgetBox(
        parent=window, 
        title="Stopwatch", 
        widgets=[SwitchButton(
            onturnon=lambda: stopwatch.append(StopWatchMainWindow(window)), 
            onturnoff=lambda: (stopwatch.pop().close() if stopwatch else None)
        )]
    ))

    keyboard_manager = []
    window.addWidget(WidgetBox(
        parent=window, 
        title="Keyboard Displayer", 
        widgets=[SwitchButton(
            onturnon=lambda: keyboard_manager.append(KeyDisplayerManager(window)), 
            onturnoff=lambda: (keyboard_manager.pop().close() if keyboard_manager else None)
        )]
    ))

    drop_runner = DropRunner(window)
    window.addWidget(drop_runner)

    window.show()
    sys.exit(app.exec_())

