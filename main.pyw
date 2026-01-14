from base_import import *
from start_check import CheckStarted
from main_window import MainWindow, WidgetBox, PlainText
from stop_watch import StopWatchMainWindow
from switch_widgets import SwitchButton, PushButton
from drop_runner import DropRunner
from keyboard_displayer import KeyDisplayerManager
from clickclick_clicker import ClickerWidget
from clipboard_widget import ClipboardWidget

class UtilitiesWidget(WidgetBox):
    def __init__(self, master:MainWindow):
        super().__init__(parent=master, title="Utilities")
        self.master = master
        self.keyboard_manager=[]
        self.stopwatch=[]

        self.inline_calculator_button = PushButton(
            onclick=self.droprunner_callback, 
            text="Inline Calculator", 
            width=240, 
            bg_color=QColor(100, 150, 250)
        )

        self.keyboard_displayer_button = SwitchButton(
            onturnon=lambda: self.keyboard_manager.append(KeyDisplayerManager(self.master)), 
            onturnoff=lambda: (self.keyboard_manager.pop().close() if self.keyboard_manager else None), 
            onchange=self.toggle_keyboard_displayer
        )
        self.keyboard_displayer_label = PlainText(
            text="Keyboard Displayer is Disabled",
            parent=self
        )
        self.stopwatch_button = SwitchButton(
            onturnon=lambda: self.stopwatch.append(StopWatchMainWindow(self.master)),
            onturnoff=lambda: (self.stopwatch.pop().close() if self.stopwatch else None), 
            onchange=self.toggle_stopwatch
        )
        self.stopwatch_label = PlainText(
            text="Stopwatch is Disabled",
            parent=self
        )

        self.keyboard_displayer_sublayout = QHBoxLayout()
        self.stopwatch_sublayout = QHBoxLayout()
        self.keyboard_displayer_sublayout.addWidget(self.keyboard_displayer_button)
        self.keyboard_displayer_sublayout.addWidget(self.keyboard_displayer_label)
        self.stopwatch_sublayout.addWidget(self.stopwatch_button)
        self.stopwatch_sublayout.addWidget(self.stopwatch_label)

        self.layout.addWidget(self.inline_calculator_button)
        self.layout.addLayout(self.keyboard_displayer_sublayout)
        self.layout.addLayout(self.stopwatch_sublayout)

    def droprunner_callback(self):
        drop_runner.run(os.path.join(SETTINGS.project_dir, 'inline_calculator.py'))

    def toggle_keyboard_displayer(self, state:bool):
        if state:
            self.keyboard_displayer_label.setText("Keyboard Displayer is Enabled")
        else:
            self.keyboard_displayer_label.setText("Keyboard Displayer is Disabled")

    def toggle_stopwatch(self, state:bool):
        if state:
            self.stopwatch_label.setText("Stopwatch is Enabled")
        else:
            self.stopwatch_label.setText("Stopwatch is Disabled")
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    with CheckStarted():
        window = MainWindow(app=app)

        drop_runner = DropRunner(window)
        window.addWidget(drop_runner)
        window.droprunner = drop_runner

        window.addWidget(ClipboardWidget(parent=window))

        window.addWidget(UtilitiesWidget(master=window))

        clicker = ClickerWidget(window)
        window.addWidget(clicker)

        window.addWidget(WidgetBox(
            parent=window,
            title="Other Tools",
            widgets=[
                PushButton(
                    onclick=lambda: drop_runner.run(os.path.join(SETTINGS.project_dir, 'word_counter.py')), 
                    text="Word Counter", 
                    width=220, 
                    bg_color=QColor(200, 200, 100)
                ), 
                PushButton(
                    onclick=lambda: drop_runner.run(os.path.join(SETTINGS.project_dir, 'hex_quickview.py')), 
                    text="Raw Hex Previewer", 
                    width=260, 
                    bg_color=QColor(100, 200, 200)
                ),
                PushButton(
                    onclick=lambda: drop_runner.run(os.path.join(SETTINGS.project_dir, 'ScdAch', 'mainmenu.py'), without_console=True), 
                    text="Schedule Achievements", 
                    width=300, 
                    bg_color=QColor(200, 100, 200)
                ),
            ]
        ))

        window.addWidget(WidgetBox(
            parent=window,
            title="Hotkey Guide", 
            widgets=[
                PlainText(
                    text="Win+Shift+M: Measure Distance", 
                ), 
                PlainText(
                    text="Win+Shift+C: Color Picker", 
                ), 
                PlainText(
                    text="Win+Shift+T: OCR Text", 
                ), 
                PlainText(
                    text="Hold Win Key to see other hotkeys", 
                )
            ]
        ))

        window.show()
        try:
            ret = app.exec_()
        except Exception as e:
            import traceback
            with open("error_log.txt", "a+", encoding="utf-8") as f:
                f.write(traceback.format_exc())
                f.write("\n\n")
            ret = 1
    
    del app

    print("Exiting...")

    # Ensure all resources are cleaned up properly
    # sys.exit(ret)
    # Just joking
    os._exit(ret)
