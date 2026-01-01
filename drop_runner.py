from base_import import *
from main_window import WidgetBox, MainWindow
from switch_widgets import SwitchButton


class DropRunner(WidgetBox):
    TITLE = "Drop Runner"
    PYTHON_DIR = os.path.dirname(sys.executable)

    def __init__(self, master:MainWindow):
        super().__init__(master, title=self.TITLE)

        self.master = master
        self.label = QLabel("Drop Pythons Here", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont(FONT_NAME, 10))

        self.debug_mode_sublayout = QHBoxLayout()
        self.switch = SwitchButton(self, onchange=self.setDebugMode)
        self.switchText = QLabel("Run mode", self)
        self.switchText.setFont(QFont(FONT_NAME, 10))
        self.debug_mode_sublayout.addWidget(self.switch)
        self.debug_mode_sublayout.addWidget(self.switchText)

        self.layout.addLayout(self.debug_mode_sublayout)
        self.layout.addWidget(self.label)

        self.python_path = os.path.join(self.PYTHON_DIR, 'python.exe')
        self.pythonw_path = os.path.join(self.PYTHON_DIR, 'pythonw.exe')
        self.debug_mode = False

    def setDebugMode(self, debug: bool):
        self.debug_mode = debug
        if self.debug_mode:
            self.switchText.setText("Debug mode")
        else:
            self.switchText.setText("Run mode")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        file_paths = [url.toLocalFile() for url in urls]
        for file_path in file_paths:
            if not os.path.exists(file_path):
                self.push_message("File not exists: " + file_path)
                continue
            if not os.path.isfile(file_path):
                self.push_message("Not a file: " + file_path)
                continue
            while file_path.startswith('"') and file_path.endswith('"'):
                file_path = file_path[1:-1]
            _loop_counter = 0
            while file_path.endswith('.lnk'):
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(file_path)
                file_path = shortcut.Targetpath
                _loop_counter += 1
                if _loop_counter > 1000:
                    break
            if file_path.endswith('.py'):
                self.run(file_path, without_console=False)
            elif file_path.endswith('.pyw'):
                self.run(file_path, without_console=True)
            else:
                self.push_message("Not a Python script: " + file_path)
            
        event.acceptProposedAction()

    def run(self, script_path: str, without_console: bool=False):
        cwd = os.getcwd()
        if self.debug_mode:
            os.chdir(os.path.dirname(script_path))
            subprocess.Popen(f'cmd /k ""{self.python_path}" "{script_path}""', creationflags=subprocess.CREATE_NEW_CONSOLE)
            os.chdir(cwd)
        else:
            app_path = self.pythonw_path if without_console else self.python_path
            def callbackfunc():
                try:
                    os.chdir(os.path.dirname(script_path))
                    proc=subprocess.Popen([app_path, script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                    os.chdir(cwd)
                    ret=proc.wait()
                except KeyboardInterrupt:
                    ret = -1073741510
                finally:
                    os.chdir(cwd)
                if ret>=0x80000000:
                    ret-=0x1_00000000
                message = f'Program "{script_path}" exits with return value {ret}(0x{ret&0xffffffff:08X})'
                self.push_message(message)
            threading.Thread(target=callbackfunc, daemon=True).start()

    def push_message(self, message: str):
        # print(message)
        try:
            self.master.messages.put_nowait(message)
        except Exception:
            import traceback
            traceback.print_exc()
        

if __name__ == "__main__":
    from main_window import MainWindow, WidgetBox
    from start_check import check_started
    app = QApplication(sys.argv)
    check_started()
    MainWindow.TITLE = "Drop Runner Test"
    window = MainWindow(app=app)

    drop_runner = DropRunner(window)
    window.addWidget(drop_runner)

    window.show()
    sys.exit(app.exec_())
