from basic_settings import *
from main_widgets import MainWindow, WidgetBox, PlainText, PushButton, has_lib
from common_utilities import get_clipboard_file_paths

def run(master:MainWindow, path:str, *, without_console=True, arguments=()):
    if hasattr(master, 'droprunner'):
        full_path = os.path.join(SETTINGS.src_dir, 'musical_lite', path)
        master.droprunner.run(full_path, arguments=arguments, without_console=without_console)
    else:
        master.messages.put_nowait("DropRunner not found in master window.")

class MusicalLiteWidget(WidgetBox):
    def __init__(self, parent:MainWindow=None):
        super().__init__(
            parent=parent,
            title="Musical Lite"
        )
        self.player_button = PushButton(
            onclick=self.run_player,
            text="Player",
            width=110,
            bg_color=QColor(150, 200, 100)
        )
        self.reverser_button = PushButton(
            onclick=lambda:QTimer.singleShot(0, self.audio_reverse_nonblocking),
            text="Reverse", 
            width=120,
            bg_color=QColor(200, 100, 150)
        )
        self.piano_button = PushButton(
            onclick=lambda:run(self.master, 'pygpiano.py'),
            text="Piano",
            width=110,
            bg_color=QColor(100, 150, 250)
        )
        self.bpm_button = PushButton(
            onclick=lambda:run(self.master, 'pygbpm.py'),
            text="BPMCount",
            width=160,
            bg_color=QColor(250, 150, 100)
        )
        self.extract_audio_button = PushButton(
            onclick=lambda:QTimer.singleShot(0, self.extract_audio_nonblocking),
            text="Extract Audio",
            width=220,
            bg_color=QColor(250, 150, 150)
        )
        self.audio_decompose_button = PushButton(
            onclick=self.audio_decompose, 
            text = "Extract Vocals",
            width=220, 
            bg_color=QColor(150, 250, 150)
        )
        if has_lib("pygame", 'pydub', 'scipy'):
            self.addLine(
                # self.player_button,
                self.reverser_button,
                self.piano_button,
                self.bpm_button,
            ).addLine(
                self.extract_audio_button, 
                self.audio_decompose_button if has_lib('torch', 'torchaudio', 'torchcodec') else PlainText("Install Torch!")
            )
        else:
            self.addLine(PlainText("Install Pygame, Pydub and Scipy!"))

    def run_player(self):
        fps = get_clipboard_file_paths()
        for fp in fps:
            if fp and fp.lower().endswith(('.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a')):
                return run(self.master, 'pygplayer.py', arguments=(fp,))
        file_dialog = QFileDialog(directory=os.path.join(os.path.expanduser("~"), "Music"))
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Audio Files (*.mp3 *.wav *.flac *.ogg *.aac *.m4a)")
        if file_dialog.exec_():
            audio_path = file_dialog.selectedFiles()[0]
            return run(self.master, 'pygplayer.py', arguments=(audio_path,))
        
    def audio_reverse(self):
        def _get_output_path(audio_path):
            output_path = os.path.splitext(audio_path)[0] + "_reversed" + os.path.splitext(audio_path)[1]
            if os.path.exists(output_path):
                extension_marker_int = 2
                while True:
                    output_path = os.path.splitext(audio_path)[0] + f"_reversed({extension_marker_int})" + os.path.splitext(audio_path)[1]
                    if not os.path.exists(output_path):
                        break
                    extension_marker_int += 1
            return output_path
        from musical_lite.musicallitelib import Converter
        fps = get_clipboard_file_paths()
        for fp in fps:
            if fp and fp.lower().endswith(('.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a')):
                audio_path = fp
                output_path = _get_output_path(audio_path)
                Converter.reverse_audio(audio_path, output_path)
                self.master.messages.put_nowait(f"Reversed audio saved to: {output_path}")
                return
        file_dialog = QFileDialog(directory=os.path.join(os.path.expanduser("~"), "Music"))
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Audio Files (*.mp3 *.wav *.flac *.ogg *.aac *.m4a)")
        if file_dialog.exec_():
            audio_path = file_dialog.selectedFiles()[0]
            output_path = _get_output_path(audio_path)
            Converter.reverse_audio(audio_path, output_path)
            self.master.messages.put_nowait(f"Reversed audio saved to: {output_path}")

    def audio_reverse_nonblocking(self):
        import threading
        threading.Thread(target=self.audio_reverse).start()
    
    def extract_audio(self):
        from musical_lite.musicallitelib import Converter
        fps = get_clipboard_file_paths()
        for fp in fps:
            if fp and fp.lower().endswith(('.mp4', '.avi', '.mkv', '.flv', '.mov')):
                converter = Converter()
                audio_path = os.path.splitext(fp)[0] + "_audio.mp3"
                converter.video_to_mp3(fp, audio_path)
                self.master.messages.put_nowait(f"Audio extracted to: {audio_path}")
                return
        file_dialog = QFileDialog(directory=os.path.join(os.path.expanduser("~"), "Videos"))
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Video Files (*.mp4 *.avi *.mkv *.flv *.mov)")
        if file_dialog.exec_():
            video_path = file_dialog.selectedFiles()[0]
            converter = Converter()
            audio_path = os.path.splitext(video_path)[0] + "_audio.mp3"
            converter.video_to_mp3(video_path, audio_path)
            self.master.messages.put_nowait(f"Audio extracted to: {audio_path}")

    def extract_audio_nonblocking(self):
        import threading
        threading.Thread(target=self.extract_audio).start()

    def audio_decompose(self):
        fps = get_clipboard_file_paths()
        for fp in fps:
            if fp and fp.lower().endswith(('.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a')):
                return run(self.master, 'audio_decompose.py', arguments=(fp,), without_console=False)
        file_dialog = QFileDialog(directory=os.path.join(os.path.expanduser("~"), "Music"))
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Audio Files (*.mp3 *.wav *.flac *.ogg *.aac *.m4a)")
        if file_dialog.exec_():
            audio_path = file_dialog.selectedFiles()[0]
            return run(self.master, 'audio_decompose.py', arguments=(audio_path,))
        