from base_import import *
from main_window import MainWindow, WidgetBox, PlainText
from switch_widgets import PushButton
from drop_runner import DropRunner
from popup_window import FadingPopup

class ClipboardWidget(WidgetBox):
    def __init__(self, parent:MainWindow):
        super().__init__(
            parent=parent,
            title="Clipboard Utilities"
        )
        self.master=parent
        self.clear_format_button = PushButton(
            text="Clipboard Clear Format", 
            width=320, 
            bg_color=QColor(150, 100, 250),
            onclick=self.clear_format_callback
        )
        # self.save_image_button = PushButton(
        #     text="Save Clipboard Image", 
        #     width=320, 
        #     bg_color=QColor(200, 200, 100),
        #     onclick=self.save_image_callback
        # )
        self.clear_content_button = PushButton(
            text="Clipboard Clear Content", 
            width=320, 
            bg_color=QColor(250, 150, 100),
            onclick=self.clear_content_callback
        )
        self.advanced_reader_button = PushButton(
            text = "Advanced ClipboardReader",
            width=360,
            bg_color=QColor(100, 250, 150),
            onclick=self.start_advanced_reader_callback
        )
        self.current_clipboard_state = PlainText(
            text="<Not Initialized>",
        )

        self.addWidget(self.clear_format_button)
        self.addWidget(self.clear_content_button)
        self.addWidget(self.advanced_reader_button)
        self.addWidget(self.current_clipboard_state)
        
        self.addWidget(PlainText(
            text="Win+V : Clipboard History", 
        ))
        self.addWidget(PlainText(
            text="Win+Shift+V : Advanced Paster", 
        ))
        self.addWidget(PlainText(
            text="Win+Ctrl+Alt+V : Paste as Plain Text", 
        ))

        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.refresh_clipboard_state)
        self.timer.start()

    def clear_format_callback(self):
        content = pyperclip.paste()
        if content:
            pyperclip.copy(content)
            FadingPopup("Clipboard format cleared ~").fadeIn()
        else:
            FadingPopup("No text in clipboard ~").fadeIn()

    def clear_content_callback(self):
        pyperclip.copy("")
        FadingPopup("Clipboard cleared!").fadeIn()

    def save_image_callback(self):
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
                import io
                from PIL import Image
                bmpinfo = data[:40]
                width = int.from_bytes(bmpinfo[4:8], 'little')
                height = int.from_bytes(bmpinfo[8:12], 'little')
                bpp = int.from_bytes(bmpinfo[14:16], 'little')
                if bpp != 32:
                    raise RuntimeError("Only 32bpp images are supported.")
                img_data = data[40:]
                img = Image.frombuffer('RGBA', (width, height), img_data, 'raw', 'BGRA', 0, 1)
                save_path, _ = QFileDialog.getSaveFileName(self.parent, "Save Clipboard Image", "", "PNG Files (*.png);;All Files (*)")
                if save_path:
                    img.save(save_path, 'PNG')
                    FadingPopup(f"Image saved to {save_path}").fadeIn()
            else:
                FadingPopup("No image data in clipboard ~").fadeIn()
        except Exception as e:
            FadingPopup(f"Failed to save image: {str(e)}").fadeIn()
        finally:
            win32clipboard.CloseClipboard()

    def start_advanced_reader_callback(self):
        if hasattr(self.master, 'droprunner') and isinstance(self.master.droprunner, DropRunner):
            droprunner=self.master.droprunner
            droprunner.run(os.path.abspath(os.path.join(PROJECT_DIR, 'clipboard_reader.py')), without_console=True)
        else:
            droprunner=DropRunner(self.master)
            droprunner.run(os.path.abspath(os.path.join(PROJECT_DIR, 'clipboard_reader.py')), without_console=True)
            droprunner.close()
            droprunner.deleteLater()

    def refresh_clipboard_state(self):
        try:
            text = f"Current State: {get_clipboard_state()}"
        except Exception as e:
            text = "<error>"
        self.current_clipboard_state.setText(text)

    def closeEvent(self, event):
        self.timer.timeout.disconnect()
        self.timer.stop()
        self.timer.deleteLater()
        super().closeEvent(event)


def get_clipboard_state()->str:
    known_formats = {
        1: "CF_TEXT",
        2: "CF_BITMAP",
        3: "CF_METAFILEPICT",
        4: "CF_SYLK",
        5: "CF_DIF",
        6: "CF_TIFF",
        7: "CF_OEMTEXT",
        8: "CF_DIB",
        9: "CF_PALETTE",
        10: "CF_PENDATA",
        11: "CF_RIFF",
        12: "CF_WAVE",
        13: "CF_UNICODETEXT",
        14: "CF_ENHMETAFILE",
        15: "CF_HDROP",
        16: "CF_LOCALE",
        17: "CF_DIBV5"
    }
    formats = {}
    error = ''
    try:
        win32clipboard.OpenClipboard()
        format_id = win32clipboard.EnumClipboardFormats(0)
        error_capacity=16
        while format_id != 0 and error_capacity>0:
            format_name = None
            try:
                if format_id in known_formats:
                    format_name = known_formats[format_id]
                else:
                    format_name = win32clipboard.GetClipboardFormatName(format_id)
            except Exception as e:
                format_name = '<Unknown>'
            
            formats[format_id] = format_name

            try:
                old_format_id=format_id
                format_id = win32clipboard.EnumClipboardFormats(format_id)
                if format_id==old_format_id:
                    break
            except Exception as e:
                error_capacity-=1
        if error_capacity<=0:
            error = '<Max tries exceeded>'
    except Exception as e:
        error = e.__class__.__name__
    finally:
        win32clipboard.CloseClipboard()

    if len(formats)==0:
        if error:
            result = error
        else:
            result = "<Empty>"
    elif 1 in formats or 7 in formats or 13 in formats:
        # text
        if 49403 in formats or 49282 in formats:
            result = "Rich Text"
        elif set(formats.keys()).difference({1,7,13,16}):
            result = "Suspected Rich Text"
        else:
            result = "Plain Text"
    elif 2 in formats or 3 in formats or 6 in formats or 8 in formats or 14 in formats:
        result = "Image"
        if 49289 in formats:
            result = "PNG Image"
    elif 15 in formats:
        result = "File"
    elif 12 in formats:
        result = "Audio"
    else:
        result = "Other Data"
        
    return result


def get_encoding_name(data):
    encoding_name="Unknown"
    try:
        if isinstance(data, str):
            text_data=data
            encoding_name="String"
        elif isinstance(data, bytes):
            try:
                try:
                    try:
                        text_data=data.decode('ascii')
                        encoding_name="ASCII"
                    except UnicodeDecodeError:
                        text_data=data.decode('utf-8')
                        encoding_name="UTF-8"
                except UnicodeDecodeError:
                    text_data=data.decode('gb18030')
                    encoding_name="GB18030"
                for c in text_data:
                    if ord(c)<32 and c not in '\r\n\t':
                        raise RuntimeError
            except UnicodeDecodeError:
                encoding_name="RAW"
            except RuntimeError:
                encoding_name="RAW"
        else:
            raise RuntimeError
    except RuntimeError:
        encoding_name="Not Text"
    return encoding_name
