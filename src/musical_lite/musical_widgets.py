from basic_settings import *
from main_widgets import MainWindow, WidgetBox, PlainText, PushButton
from common_utilities import get_clipboard_file_paths

def run(master:MainWindow, path:str, without_console=True, *args):
    if hasattr(master, 'droprunner'):
        full_path = os.path.join(SETTINGS.src_dir, 'musical_lite', path)
        master.droprunner.run(full_path, arguments=args, without_console=without_console)
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
            onclick=self.extract_audio, 
            text="Extract Audio",
            width=240,
            bg_color=QColor(250, 150, 150)
        )
        self.addLine(
            self.player_button,
            self.piano_button,
            self.bpm_button,
        ).addLine(
            self.extract_audio_button
        )

    def run_player(self):
        fp = get_clipboard_file_paths()
        if fp and fp.endswith(('.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a')):
            return run(self.master, 'pygplayer.py', fp)
        file_dialog = QFileDialog(directory=os.path.join(os.path.expanduser("~"), "Music"))
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Audio Files (*.mp3 *.wav *.flac *.ogg *.aac *.m4a)")
        if file_dialog.exec_():
            audio_path = file_dialog.selectedFiles()[0]
            return run(self.master, 'pygplayer.py', audio_path)
    
    def extract_audio(self):
        from musical_lite.musicallitelib import Converter
        file_dialog = QFileDialog(directory=os.path.join(os.path.expanduser("~"), "Videos"))
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Video Files (*.mp4 *.avi *.mkv *.flv *.mov)")
        if file_dialog.exec_():
            video_path = file_dialog.selectedFiles()[0]
            converter = Converter()
            audio_path = os.path.splitext(video_path)[0] + "_audio.mp3"
            converter.video_to_mp3(video_path, audio_path)
            self.master.messages.put_nowait(f"Audio extracted to: {audio_path}")

        