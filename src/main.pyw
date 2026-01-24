from basic_settings import *
from main_widgets import CheckStarted, MainWindow, WidgetBox, PlainText, SwitchButton, PushButton
from common_utilities import StopWatchWidgetBox, DropRunner, KeyDisplayerWidget, ClickerWidget, ClipboardWidget
from small_tools.small_tools_widgets import InlineCalculatorWidget, OtherToolsWidget, HotkeyGuideWidget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    with CheckStarted():
        window = MainWindow(app=app)
        drop_runner = DropRunner(window)
        window.droprunner = drop_runner
        clipboard_widget = ClipboardWidget(parent=window)
        window.clipboard_widget = clipboard_widget
        window.addWidget(InlineCalculatorWidget(parent=window))
        window.addWidget(clipboard_widget)
        window.addWidget(drop_runner)
        window.addWidget(KeyDisplayerWidget(master=window))
        window.addWidget(StopWatchWidgetBox(master=window))
        window.addWidget(ClickerWidget(window))
        window.addWidget(OtherToolsWidget(parent=window))
        window.addWidget(HotkeyGuideWidget(parent=window))
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
