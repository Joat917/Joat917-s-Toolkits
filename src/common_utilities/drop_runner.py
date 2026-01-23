from basic_settings import *
from main_widgets import MainWindow, WidgetBox, SwitchButton, PushButton, ConfirmationPopup

class DropRunner(WidgetBox):
    TITLE = "Drop Runner"
    PYTHON_DIR = os.path.dirname(sys.executable)

    def __init__(self, master:MainWindow):
        super().__init__(master, title=self.TITLE)

        self.master = master

        self.label = QLabel("Drop Pythons and Cs Here", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont(SETTINGS.font_name, SETTINGS.font_size, QFont.Bold))
        self.label.setStyleSheet(f"color: {SETTINGS.text_color};")

        self.debug_mode_sublayout = QHBoxLayout()
        self.switch = SwitchButton(self, onchange=self.setDebugMode)
        self.switchText = QLabel("Run mode", self)
        self.switchText.setFont(QFont(SETTINGS.font_name, SETTINGS.font_size))
        self.switchText.setStyleSheet(f"color: {SETTINGS.text_color};")
        self.debug_mode_sublayout.addWidget(self.switch)
        self.debug_mode_sublayout.addWidget(self.switchText)

        self.layout.addLayout(self.debug_mode_sublayout)
        self.layout.addWidget(self.label)

        self.python_path = os.path.join(self.PYTHON_DIR, 'python.exe')
        self.pythonw_path = os.path.join(self.PYTHON_DIR, 'pythonw.exe')
        self.debug_mode = False

        self.master.trayWidget.add_action("Restart", self.restartEverything)

        self.last_dropped_files = []
        self.last_dropped_sublayout = QVBoxLayout()
        self._last_dropped_widgets = []
        self.layout.addLayout(self.last_dropped_sublayout)

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
        _additions_to_last_dropped = []

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
                _additions_to_last_dropped.append(file_path)
            elif file_path.endswith('.pyw'):
                self.run(file_path, without_console=True)
                _additions_to_last_dropped.append(file_path)
            elif file_path.endswith('.c'):
                self.run_Ccode(file_path)
                _additions_to_last_dropped.append(file_path)
            elif file_path.endswith('.cpp'):
                self.run_Ccode(file_path, cpp=True)
                _additions_to_last_dropped.append(file_path)
            else:
                self.push_message("Not a Python or C script: " + file_path)
            
        _additions_to_last_dropped=_additions_to_last_dropped[:SETTINGS.droprunner_history_max]
        for file_path in _additions_to_last_dropped:
            if file_path in self.last_dropped_files:
                self.last_dropped_files.remove(file_path)
        self.last_dropped_files=_additions_to_last_dropped+self.last_dropped_files
        self.last_dropped_files=self.last_dropped_files[:SETTINGS.droprunner_history_max]
        self._refresh_last_dropped_display()
            
        event.acceptProposedAction()

    def _refresh_last_dropped_display(self):
        for qobj in self.last_dropped_sublayout.children():
            self.last_dropped_sublayout.removeWidget(qobj)
            qobj.deleteLater()
        for w in self._last_dropped_widgets:
            w.onclick=None
            w.close()
            w.deleteLater()
        self._last_dropped_widgets.clear()
        
        for file_path in self.last_dropped_files:
            def _callback(*, file_path=file_path):
                if not os.path.exists(file_path):
                    self.push_message("File not exists: " + file_path)
                    return
                if not os.path.isfile(file_path):
                    self.push_message("Not a file: " + file_path)
                    return
                if file_path.endswith('.py'):
                    self.run(file_path, without_console=False)
                elif file_path.endswith('.pyw'):
                    self.run(file_path, without_console=True)
                elif file_path.endswith('.c'):
                    self.run_Ccode(file_path)
                elif file_path.endswith('.cpp'):
                    self.run_Ccode(file_path, cpp=True)
                else:
                    self.push_message("Not a Python or C script: " + file_path)
                return
            
            text = os.path.basename(file_path)
            _suffix = os.path.dirname(file_path).replace('\\', '/')
            if len(text) + len(_suffix) > 25:
                _suffix = '...' + _suffix[-(30 - len(text) - 3):]
            text += ' @ ' + _suffix

            label = PushButton(
                text=text,
                parent=self,
                width=450,
                height=40, 
                bg_color=QColor(100, 100, 100),
                alpha=0,  
                onclick=_callback
            )
            self.last_dropped_sublayout.addWidget(label)
            self._last_dropped_widgets.append(label)

    def run(self, script_path: str, without_console: bool=False):
        if self.debug_mode:
            os.chdir(os.path.dirname(script_path))
            subprocess.Popen(f'cmd /k ""{self.python_path}" "{script_path}""', creationflags=subprocess.CREATE_NEW_CONSOLE)
            os.chdir(SETTINGS.working_dir)
        else:
            app_path = self.pythonw_path if without_console else self.python_path
            def callbackfunc():
                try:
                    os.chdir(os.path.dirname(script_path))
                    proc=subprocess.Popen([app_path, script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                    os.chdir(SETTINGS.working_dir)
                    ret=proc.wait()
                except KeyboardInterrupt:
                    ret = -1073741510
                finally:
                    os.chdir(SETTINGS.working_dir)
                if ret>=0x80000000:
                    ret-=0x1_00000000
                message = f'Program "{script_path}" exits with return value {ret}(0x{ret&0xffffffff:08X})'
                self.push_message(message)
            threading.Thread(target=callbackfunc, daemon=True).start()

    def run_Ccode(self, source_path:str, cpp=False):
        source_path = os.path.abspath(source_path)
        exe_path = os.path.splitext(source_path)[0] + '.exe'
        if os.path.exists(exe_path):
            suffix_index = 2
            exe_path = exe_path[:-4] + f'_{suffix_index}.exe'
            while os.path.exists(exe_path):
                suffix_index += 1
                exe_path = exe_path[:-len(f'_{suffix_index-1}.exe')] + f'_{suffix_index}.exe'
        compile_command = f"{'gcc' if not cpp else 'g++'} -O3 \"{source_path}\" -o \"{exe_path}\""
        
        if self.debug_mode:
            os.chdir(os.path.dirname(source_path))
            subprocess.Popen(f'cmd /k {compile_command} && ("{exe_path}" & echo Program exits with return value %errorlevel%)', creationflags=subprocess.CREATE_NEW_CONSOLE)
            os.chdir(SETTINGS.working_dir)
        else:
            def callback_compile():
                try:
                    os.chdir(os.path.dirname(source_path))
                    proc=subprocess.Popen(compile_command, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
                    os.chdir(SETTINGS.working_dir)
                    ret=proc.wait()
                except KeyboardInterrupt:
                    ret = -1073741510
                finally:
                    os.chdir(SETTINGS.working_dir)
                if ret>=0x80000000:
                    ret-=0x1_00000000
                if ret==0:
                    callback_run()
                else:
                    message = f'Compilation Failure: {ret}(0x{ret&0xffffffff:08X})'
                    self.push_message(message)
            def callback_run():
                try:
                    os.chdir(os.path.dirname(source_path))
                    proc=subprocess.Popen([exe_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                    os.chdir(SETTINGS.working_dir)
                    ret=proc.wait()
                except KeyboardInterrupt:
                    ret = -1073741510
                finally:
                    os.chdir(SETTINGS.working_dir)
                if ret>=0x80000000:
                    ret-=0x1_00000000
                message = f'Program "{exe_path}" exits with return value {ret}(0x{ret&0xffffffff:08X})'
                self.push_message(message)
            threading.Thread(target=callback_compile, daemon=True).start()


    def push_message(self, message: str):
        # print(message)
        try:
            self.master.messages.put_nowait(message)
        except Exception:
            traceback.print_exc()

    def restartEverything(self, *, confirm=False):
        if confirm:
            popup = ConfirmationPopup("Restart?")
            popup.show_popup()
            while popup.user_response is None:
                QApplication.processEvents()
                time.sleep(0.05)
            if not popup.user_response:
                return
        os.chdir(SETTINGS.project_dir)
        subprocess.Popen(sys.orig_argv[:]+['--forceKillAllExistingInstances'], creationflags=subprocess.CREATE_NEW_CONSOLE)
        # this process will be killed by the newly started process
        time.sleep(0.01)
        os.chdir(SETTINGS.working_dir)

    def close(self):
        self.master.trayWidget.remove_action("Restart")
        self.deleteLater()
        return super().close()
