from base_import import *
from start_check import check_started
from main_window import MainWindow, WidgetBox, PlainText
from stop_watch import StopWatchMainWindow
from switch_widgets import SwitchButton, PushButton
from drop_runner import DropRunner
from keyboard_displayer import KeyDisplayerManager
from popup_window import FadingPopup
from clickclick_clicker import ClickerWidget

if __name__ == "__main__":
    app = QApplication(sys.argv)
    check_started()
    MainWindow.TITLE = "Joat917's Toolkit"
    window = MainWindow(app=app)

    drop_runner = DropRunner(window)

    window.addWidget(WidgetBox(
        parent=window,
        title="Inline Calculator",
        widgets=[PushButton(
            onclick=lambda: drop_runner.run(os.path.abspath('inline_calculator.py')), 
            text="Inline Calculator", 
            width=240, 
            bg_color=QColor(100, 150, 250)
        )]
    ))

    window.addWidget(WidgetBox(
        parent=window,
        title="Clipboard Utilities",
        widgets=[PushButton(
            text="Clipboard Clear Format", 
            width=320, 
            bg_color=QColor(150, 100, 250),
            onclick=lambda: (pyperclip.copy(pyperclip.paste()), FadingPopup("Clipboard format cleared!").fadeIn())
        ), 
        PushButton(
            text="Clipboard Clear Content", 
            width=320, 
            bg_color=QColor(250, 150, 100),
            onclick=lambda: (pyperclip.copy(""), FadingPopup("Clipboard cleared!").fadeIn())
        ), 
        PushButton(
            text = "Advanced ClipboardReader",
            width=320,
            bg_color=QColor(100, 250, 150),
            onclick=lambda: drop_runner.run(os.path.abspath('clipboard_reader.py'), without_console=True)
        ), 
        PlainText(
            text="Press Win+V to View Clipboard History", 
        ), 
        PlainText(
            text="Press Win+Shift+V to Open Advanced Paster", 
        ), 
        PlainText(
            text="Press Win+Ctrl+Alt+V to Paste as Plain Text", 
        )
        ]
    ))

    window.addWidget(WidgetBox(
        parent=window,
        title="Hotkey Guide", 
        widgets=[
            PlainText(
                text="Win+Shift+M: Measure Screen Distance", 
            ), 
            PlainText(
                text="Win+Shift+C: Open Color Picker", 
            ), 
            PlainText(
                text="Win+Shift+T: OCR Text from Screen", 
            ), 
            PlainText(
                text="Hold Win Key to see other hotkeys", 
            )
        ]
    ))

    window.addWidget(drop_runner)

    keyboard_manager = []
    window.addWidget(WidgetBox(
        parent=window, 
        title="Keyboard Displayer", 
        widgets=[SwitchButton(
            onturnon=lambda: keyboard_manager.append(KeyDisplayerManager(window)), 
            onturnoff=lambda: (keyboard_manager.pop().close() if keyboard_manager else None)
        )]
    ))

    stopwatch = []
    window.addWidget(WidgetBox(
        parent=window, 
        title="Stopwatch", 
        widgets=[SwitchButton(
            onturnon=lambda: stopwatch.append(StopWatchMainWindow(window)), 
            onturnoff=lambda: (stopwatch.pop().close() if stopwatch else None)
        )]
    ))

    clicker = ClickerWidget(window)
    window.addWidget(clicker)

    window.show()
    sys.exit(app.exec_())

