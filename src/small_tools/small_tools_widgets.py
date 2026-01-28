from basic_settings import *
from main_widgets import MainWindow, WidgetBox, PlainText, PushButton
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
            text="Word Counter", 
            width=220, 
            bg_color=QColor(200, 200, 100)
        )
        self.hex_quickview_button = PushButton(
            onclick=self.run_hex_quickview, 
            text="Raw Hex Previewer", 
            width=260, 
            bg_color=QColor(100, 200, 200)
        )
        self.qr_scanner_button = PushButton(
            onclick=self.run_qr_scanner,
            text="QR Code Scanner",
            width=250,
            bg_color=QColor(100, 200, 150)
        )
        self.scdach_calendar_button = PushButton(
            onclick=self.run_scdach_calendar, 
            text="ScdAch Calendar", 
            width=230, 
            bg_color=QColor(150, 100, 250)
        )
        self.schedule_achievements_button = PushButton(
            onclick=self.run_schedule_achievements, 
            text="Schedule Achievements", 
            width=300, 
            bg_color=QColor(200, 100, 200)
        )
        self.bpm_checker_button = PushButton(
            onclick=self.run_bpm_checker, 
            text="Measure BPM", 
            width = 220, 
            bg_color=QColor(150, 100, 200)
        )
        self.quinifier_button = PushButton(
            onclick=self.run_quinifier, 
            text = "Quinify", 
            width = 150, 
            bg_color= QColor(150, 200, 100)
        )

        self.addWidget(self.word_counter_button)
        self.addWidget(self.hex_quickview_button)
        self.addWidget(self.qr_scanner_button)
        self.addWidget(self.scdach_calendar_button)
        self.addWidget(self.schedule_achievements_button)
        self.addWidget(self.bpm_checker_button)
        self.addWidget(self.quinifier_button)

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
    
    def run_bpm_checker(self):
        return run_script(self.master, os.path.join('mini_games', 'bpmfft2.pyw'))

    def run_quinifier(self):
        fp = get_clipboard_file_paths()
        if fp and (fp.endswith('.py') or fp.endswith('.pyw')):
            return run_tool(self.master, 'quinify_quine.py', fp[0])
        return run_tool(self.master, 'quinify_quine.py')

    def close(self):
        if os.path.exists(self.tempfile):
            os.remove(self.tempfile)
        if os.path.exists(self.tempimagefile):
            os.remove(self.tempimagefile)
        return super().close()

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
    
        
