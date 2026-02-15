from basic_settings import *
from main_widgets import MainWindow, WidgetBox, PlainText, PushButton, SwitchButton
from common_utilities import get_clipboard_file_paths, get_clipboard_text, get_clipboard_image

def run_tool(master:MainWindow, script_path:str, *args):
    if hasattr(master, 'droprunner'):
        full_path = os.path.join(SETTINGS.src_dir, 'small_tools', script_path)
        master.droprunner.run(full_path, run_dir=SETTINGS.src_dir, arguments=args)
    else:
        master.messages.put_nowait("DropRunner not found in master window.")

def run_script(master:MainWindow, script_path:str, *args):
    if hasattr(master, 'droprunner'):
        full_path = os.path.join(SETTINGS.src_dir, script_path)
        master.droprunner.run(full_path, without_console=True, arguments=args)
    else:
        master.messages.put_nowait("DropRunner not found in master window.")


class InlineCalculatorWidget(WidgetBox):
    def __init__(self, parent:MainWindow=None):
        super().__init__(
            parent=parent,
            title="Inline Calculator",
            widgets=[PushButton(
                onclick=lambda: run_tool(self.master, 'inline_calculator.py'), 
                text="Inline Calculator", 
                width=240, 
                bg_color=QColor(100, 150, 250)
            )]
        )

class OtherToolsWidget(WidgetBox):
    def __init__(self, parent:MainWindow=None):
        super().__init__(
            parent=parent,
            title="Other Tools"
        )
        self.word_counter_button = PushButton(
            onclick=self.run_word_counter, 
            text="WordCount", 
            width=190, 
            bg_color=QColor(200, 200, 100)
        )
        self.hex_quickview_button = PushButton(
            onclick=self.run_hex_quickview, 
            text="RawHex", 
            width=150, 
            bg_color=QColor(100, 200, 200)
        )
        self.qr_scanner_button = PushButton(
            onclick=self.run_qr_scanner,
            text="QRScan",
            width=140,
            bg_color=QColor(100, 200, 150)
        )
        self.scdach_calendar_button = PushButton(
            onclick=self.run_scdach_calendar, 
            text="Calendar", 
            width=160, 
            bg_color=QColor(150, 100, 250)
        )
        self.schedule_achievements_button = PushButton(
            onclick=self.run_schedule_achievements, 
            text="SchAchv", 
            width=160, 
            bg_color=QColor(200, 100, 200)
        )
        self.quinifier_button = PushButton(
            onclick=self.run_quinifier, 
            text = "Quinify", 
            width = 150, 
            bg_color= QColor(150, 200, 100)
        )
        self.mojibake_button = PushButton(
            onclick=self.run_mojibake, 
            text = "Corrupter", 
            width = 150, 
            bg_color= QColor(200, 150, 100)
        )
        self.minifier_button = PushButton(
            onclick=self.run_minifier, 
            text="Minify", 
            width=130, 
            bg_color=QColor(200, 150, 150)
        )
        self.script_generator_button = PushButton(
            onclick=lambda: run_tool(self.master, 'script_generator.py'), 
            text="ScriptGen", 
            width=180, 
            bg_color=QColor(100, 150, 200)
        )

        (
            self
            .addLine(self.word_counter_button, self.hex_quickview_button)
            .addLine(self.qr_scanner_button, self.script_generator_button)
            .addLine(self.schedule_achievements_button, self.scdach_calendar_button)
            .addLine(self.quinifier_button, self.minifier_button, self.mojibake_button)
        )

        self.tempfile = os.path.join(SETTINGS.working_dir, 'other_tools_temp.txt')
        self.tempimagefile = os.path.join(SETTINGS.working_dir, 'other_tools_temp_image.png')

    def run_word_counter(self):
        fp = get_clipboard_file_paths()
        if fp:
            return run_tool(self.master, 'word_counter.py', fp[0])
        texts = get_clipboard_text()
        if texts:
            with open(self.tempfile, 'w', encoding='utf-8') as f:
                f.write(texts)
            return run_tool(self.master, 'word_counter.py', self.tempfile)
        return run_tool(self.master, 'word_counter.py')
    
    def run_hex_quickview(self):
        fp = get_clipboard_file_paths()
        if fp:
            return run_tool(self.master, 'hex_quickview.py', fp[0])
        return run_tool(self.master, 'hex_quickview.py')
    
    def run_qr_scanner(self):
        img_data = get_clipboard_image()
        if img_data:
            img_data.save(self.tempimagefile)
            return run_tool(self.master, 'qrcode_scanner.py', self.tempimagefile)
        fp = get_clipboard_file_paths()
        if fp:
            return run_tool(self.master, 'qrcode_scanner.py', fp[0])
        return run_tool(self.master, 'qrcode_scanner.py')
    
    def run_scdach_calendar(self):
        return run_script(self.master, os.path.join('ScdAch', 'calendarA.py'))
    
    def run_schedule_achievements(self):
        return run_script(self.master, os.path.join('ScdAch', 'mainmenu.py'))

    def run_quinifier(self):
        fp = get_clipboard_file_paths()
        if fp and (fp.endswith('.py') or fp.endswith('.pyw')):
            return run_tool(self.master, 'quinify_quine.py', fp[0])
        return run_tool(self.master, 'quinify_quine.py')
    
    def run_mojibake(self):
        return run_tool(self.master, 'gushen_coder.py')
    
    def run_minifier(self):
        fp = get_clipboard_file_paths()
        if fp and (fp.endswith('.py') or fp.endswith('.pyw')):
            return run_tool(self.master, 'custompyminify.py', '-i', fp[0], '-o', os.path.splitext(fp[0])[0] + '_minified.'+os.path.splitext(fp[0])[1])
        self.master.messages.put_nowait("请将要压缩的Python文件路径复制到剪贴板后再点击此按钮。")

    def close(self):
        if os.path.exists(self.tempfile):
            os.remove(self.tempfile)
        if os.path.exists(self.tempimagefile):
            os.remove(self.tempimagefile)
        return super().close()
    
class ChaoticPendulumWidget(WidgetBox):
    def __init__(self, mainwindow:MainWindow):
        super().__init__(parent=mainwindow, title="Chaotic Pendulum")
        self.pendulum_display = None
        self.toggle_button = SwitchButton(
            onturnon = self.enable_display,
            onturnoff = self.disable_display,
        )
        self.status_label = PlainText(
            text="Disabled", 
            parent=self,
        )
        self.addLine(self.toggle_button, self.status_label)
        self.timer = QTimer(self)

    def enable_display(self):
        self.status_label.setText("Enabled")
        self.timer.timeout.connect(self.check_pendulum)
        self.timer.start(1000)
        if not self.pendulum_started():
            return run_script(self.master, 'small_tools/chaotic_pendulum.py')
    
    def pendulum_started(self):
        lock_file = os.path.join(SETTINGS.working_dir, 'chaotic_pendulum.pid')
        if not os.path.exists(lock_file):
            return False
        try:
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            return psutil.pid_exists(pid)
        except Exception:
            return False
    
    def check_pendulum(self):
        if not self.pendulum_started():
            if self.toggle_button.state:
                self.toggle_button.mousePressEvent(None)  # 自动关闭显示，将自动调用disable_display
    
    def disable_display(self):
        lock_file = os.path.join(SETTINGS.working_dir, 'chaotic_pendulum.pid')
        if not os.path.exists(lock_file):
            return
        try:
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            if psutil.pid_exists(pid):
                os.kill(pid, 9)
        except Exception:
            pass
        self.timer.stop()
        self.timer.timeout.disconnect(self.check_pendulum)
        self.status_label.setText("Disabled")
        # 故意留下pid文件
        return
    
class KillersWidget(WidgetBox):
    def __init__(self, parent:MainWindow=None):
        super().__init__(
            parent=parent,
            title="Killers", 
        )
        self.restart_explorer_button = PushButton(
            onclick=self.restart_explorer, 
            text="Restart Explorer", 
            width=230, 
            bg_color=QColor(250, 100, 100)
        )
        self.suiside_button = PushButton(
            onclick=self.kill_python, 
            text="Kill All Python", 
            width=210,
            bg_color=QColor(250, 150, 150)
        )
        self.addLine(self.restart_explorer_button, self.suiside_button)

    def restart_explorer(self):
        batch_file = os.path.join(SETTINGS.working_dir, 'restart_explorer.bat')
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(
                "chcp 65001\n"
                "echo 按任意键重启资源管理器~\n"
                "pause\n"
                "taskkill /f /im explorer.exe\n"
                "timeout /t 1\n"
                "start explorer.exe\n"
                "pause\n"
            )
        os.startfile(batch_file)

    def kill_python(self):
        batch_file = os.path.join(SETTINGS.working_dir, 'kill_python.bat')
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(
                "chcp 65001\n"
                "echo 按任意键结束所有Python进程~\n"
                "pause\n"
                "taskkill /f /im python.exe\n"
                "taskkill /f /im pythonw.exe\n"
                "pause\n"
            )
        os.startfile(batch_file)


class HotkeyGuideWidget(WidgetBox):
    def __init__(self, parent:MainWindow=None):
        super().__init__(
            parent=parent,
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
        )
    
        
