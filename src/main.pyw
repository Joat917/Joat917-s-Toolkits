from basic_settings import *
from main_widgets import CheckStarted, MainWindow, WidgetBox, PlainText, SwitchButton, PushButton
from common_utilities import StopWatchWidgetBox, DropRunner, KeyDisplayerWidget, ClickerWidget, ClipboardWidget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    with CheckStarted():
        window = MainWindow(app=app)

        drop_runner = DropRunner(window)
        window.droprunner = drop_runner

        window.addWidget(WidgetBox(
            parent=window,
            title="Inline Calculator",
            widgets=[PushButton(
                onclick=lambda: drop_runner.run(os.path.join(SETTINGS.src_dir, 'inline_calculator.py')), 
                text="Inline Calculator", 
                width=240, 
                bg_color=QColor(100, 150, 250)
            )]
        ))

        window.addWidget(ClipboardWidget(parent=window))

        window.addWidget(drop_runner)

        window.addWidget(KeyDisplayerWidget(master=window))
        window.addWidget(StopWatchWidgetBox(master=window))
        window.addWidget(ClickerWidget(window))

        window.addWidget(WidgetBox(
            parent=window,
            title="Other Tools",
            widgets=[
                PushButton(
                    onclick=lambda: drop_runner.run(os.path.join(SETTINGS.src_dir, 'word_counter.py')), 
                    text="Word Counter", 
                    width=220, 
                    bg_color=QColor(200, 200, 100)
                ), 
                PushButton(
                    onclick=lambda: drop_runner.run(os.path.join(SETTINGS.src_dir, 'hex_quickview.py')), 
                    text="Raw Hex Previewer", 
                    width=260, 
                    bg_color=QColor(100, 200, 200)
                ),
                PushButton(
                    onclick=lambda: drop_runner.run(os.path.join(SETTINGS.src_dir, 'ScdAch', 'mainmenu.py'), without_console=True), 
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
