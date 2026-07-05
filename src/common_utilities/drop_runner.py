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

        self.add(self.debug_mode_sublayout)
        self.add(self.label)

        self.python_path = os.path.join(self.PYTHON_DIR, 'python.exe')
        self.pythonw_path = os.path.join(self.PYTHON_DIR, 'pythonw.exe')
        self.debug_mode = False

        self.master.trayWidget.add_action("Restart", self.restartEverything)

        self.last_dropped_files = []
        self.last_dropped_sublayout = QVBoxLayout()
        self._last_dropped_widgets = []
        self.add(self.last_dropped_sublayout)

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
            try:
                file_path = self.shortcut_decoder(file_path)
            except Exception as e:
                self.push_message(f"Error decoding shortcut {file_path}: {e}")
                continue

            # try to run file
            try:
                self.run_from_filename(file_path)
            except Exception as e:
                self.push_message(f"Error running file {file_path}: {e}")
                continue
            
            # Files to be added to last dropped list (may repeat with existing ones)
            _additions_to_last_dropped.append(file_path)
        # Update the last dropped files list (may repeat)
        _new_last_dropped_files = _additions_to_last_dropped + self.last_dropped_files
        # drop duplicates (modify in place)
        _seen = set()
        i = 0
        while i < len(_new_last_dropped_files):
            file_path = _new_last_dropped_files[i]
            if file_path in _seen:
                _new_last_dropped_files.pop(i)
            else:
                _seen.add(file_path)
                i += 1
        # truncate to max history length
        _new_last_dropped_files = _new_last_dropped_files[:SETTINGS.droprunner_history_max]
        # refresh
        self.last_dropped_files = _new_last_dropped_files
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
                self.run_from_filename(file_path)
            
            text = self._text_truncator_in_display(
                text=os.path.basename(file_path), 
                suffix=os.path.dirname(file_path).replace('\\', '/'), 
                max_width=450
            )

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

    @classmethod
    def _text_truncator_in_display(cls, text, suffix, max_width):
        """
        将`text @ suffix` 的文本截断为`text @ ...fix`，使得其在显示时不超过`max_width`的宽度。
        """
        font = QFont(SETTINGS.font_name, SETTINGS.font_size)
        metrics = QFontMetrics(font)

        raw_text = text + ' @ ' + suffix
        if metrics.width(raw_text) <= max_width:
            return raw_text

        for i in range(1,len(suffix)+1):
            truncated_suffix = '...' + suffix[i:]
            truncated_text = text + ' @ ' + truncated_suffix
            if metrics.width(truncated_text) <= max_width:
                return truncated_text
        
        truncated_text = text
        if metrics.width(truncated_text) <= max_width:
            return truncated_text
        for i in range(1,len(text)+1):
            truncated_text = text[:-i] + '...'
            if metrics.width(truncated_text) <= max_width:
                return truncated_text

        return '...'  # 如果所有尝试都失败，返回一个简单的省略号
    

    def run_from_filename(self, filename: str):
        """
        给定一个脚本文件名，根据其后缀名选择运行方式。
        本方法不允许输入快捷方式文件。
        如果运行失败，直接报错，不推送消息。
        返回None
        """
        if not os.path.exists(filename):
            raise ValueError("File not exists: " + filename)
        if not os.path.isfile(filename):
            raise ValueError("Not a file: " + filename)
        if filename.endswith('.py'):
            self.run(filename, without_console=False)
        elif filename.endswith('.pyw'):
            self.run(filename, without_console=True)
        elif filename.endswith('.c'):
            self.run_Ccode(filename)
        elif filename.endswith('.cpp'):
            self.run_Ccode(filename, cpp=True)
        else:
            raise ValueError("Not a Python or C script: " + filename)
        return
    
    @staticmethod
    def shortcut_decoder(shortcut_path: str) -> str:
        """
        解码一个Windows快捷方式文件，返回其指向的目标文件路径。
        如果快捷方式指向的文件仍然是快捷方式，继续解码，直到得到一个非快捷方式文件路径为止。
        如果不是快捷方式，返回原路径。
        本方法会在文件不存在时报错。
        """
        file_path = shortcut_path
        while file_path.startswith('"') and file_path.endswith('"'):
            file_path = file_path[1:-1]
        if not os.path.exists(file_path):
            raise ValueError("File not exists: " + shortcut_path)
        if not os.path.isfile(file_path):
            raise ValueError("Not a file: " + shortcut_path)
        
        _loop_counter = 0
        while file_path.endswith('.lnk'):
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(file_path)
            file_path = shortcut.Targetpath
            _loop_counter += 1
            if _loop_counter > 1000:
                raise ValueError("Too many levels of shortcut indirection: " + shortcut_path)
        return file_path


    def run(self, script_path: str, without_console: bool=False, run_dir=None, arguments:tuple[str] = ()):
        """
        运行一个Python脚本。
        如果自身处于debug模式，则在新控制台中运行，运行结束后控制台窗口仍然打开；
        如果处于正常模式，则根据without_console选项选择是否打开控制台，并在程序运行完成后关闭控制台。

        Args:
            script_path (str): Python脚本的路径
            without_console (bool, optional): 是否不显示控制台窗口。默认为False
            run_dir (str, optional): 运行目录。默认为None，表示使用脚本文件所在目录
            arguments (tuple[str], optional): 传递给脚本的命令行参数。默认为空
        """
        if run_dir is None:
            run_dir = os.path.dirname(script_path)
        script_path = os.path.abspath(script_path)
        if self.debug_mode:
            os.chdir(run_dir)
            etc = ' '.join(f'"{arg}"' for arg in arguments)
            subprocess.Popen(f'cmd /k ""{self.python_path}" "{script_path}" {etc}"', creationflags=subprocess.CREATE_NEW_CONSOLE)
            os.chdir(SETTINGS.working_dir)
        else:
            app_path = self.pythonw_path if without_console else self.python_path
            def callbackfunc():
                try:
                    os.chdir(run_dir)
                    etc = ' '.join(f'"{arg}"' for arg in arguments)
                    proc=subprocess.Popen(f'"{app_path}" "{script_path}" {etc}', creationflags=subprocess.CREATE_NEW_CONSOLE)
                    os.chdir(SETTINGS.working_dir)
                    ret=proc.wait()
                except KeyboardInterrupt:
                    ret = -1073741510
                except Exception as e:
                    with open(SETTINGS.error_log_file, 'a+', encoding='utf-8') as f:
                        f.write(f"Error running script {script_path}:\n{traceback.format_exc()}\n")
                    ret = -1
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
