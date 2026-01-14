from base_import import *
from main_window import MainWindow, WidgetBox, PlainText
from switch_widgets import PushButton
from drop_runner import DropRunner

class ClipboardContext:
    def __init__(self, error_callback=lambda e: None):
        self.error_callback = error_callback
    
    def __enter__(self):
        win32clipboard.OpenClipboard()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            win32clipboard.CloseClipboard()
        except pywintypes.error:
            pass
        if exc_type is not None:
            self.error_callback(exc_value)
            return True

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
        self.save_image_button = PushButton(
            text="Save Clipboard Image", 
            width=320, 
            bg_color=QColor(200, 200, 100),
            onclick=self.save_image_callback
        )
        self.reveal_in_explorer_button = PushButton(
            text="Reveal File in Explorer", 
            width=300, 
            bg_color=QColor(150, 250, 100),
            onclick=self.reveal_in_explorer_callback
        )
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

        self.addWidget(self.advanced_reader_button)
        self.addWidget(self.clear_content_button)
        self.addWidget(self.clear_format_button)
        self.addWidget(self.save_image_button)
        self.addWidget(self.reveal_in_explorer_button)
        self.addWidget(self.current_clipboard_state)

        self.save_image_button.hide()
        self.reveal_in_explorer_button.hide()
        
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
            self.master.messages.put_nowait("Clipboard format cleared ~")
        else:
            self.master.messages.put_nowait("No text in clipboard ~")

    def clear_content_callback(self):
        pyperclip.copy("")
        self.master.messages.put_nowait("Clipboard cleared!")

    def save_image_callback(self):
        def get_image_path():
            save_path, _ = QFileDialog.getSaveFileName(
                parent=self.master,
                caption="Save Clipboard Image As",
                filter="PNG Image (*.png);;All Files (*)",
                directory=os.path.join(os.path.expanduser('~/Pictures'), 'clipboard_image.png')
            )
            return save_path

        with ClipboardContext(error_callback=lambda e: self.master.messages.put_nowait(f"Failed to save image: {str(e)}")):
            if not win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                self.master.messages.put_nowait("No image data in clipboard ~")
                return
            
            # from PNG data
            format_png_id = win32clipboard.RegisterClipboardFormat('PNG')
            if win32clipboard.IsClipboardFormatAvailable(format_png_id):
                data = win32clipboard.GetClipboardData(format_png_id)
                save_path = get_image_path()
                if not save_path:
                    return
                
                with open(save_path, 'wb') as f:
                    f.write(data)
                self.master.messages.put_nowait(f"Image saved to {save_path}")
                return

            # from DIB data
            data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
            bmpinfo = data[:40]
            width = int.from_bytes(bmpinfo[4:8], 'little')
            height = int.from_bytes(bmpinfo[8:12], 'little')
            bpp = int.from_bytes(bmpinfo[14:16], 'little')
            if bpp != 32:
                self.master.messages.put_nowait("Only 32bpp images are supported.")
                return
            img_data = data[40:]
            img = Image.frombuffer('RGBA', (width, height), img_data, 'raw', 'BGRA', 0, 1)
            save_path = get_image_path()
            if not save_path:
                return
            img.save(save_path, 'PNG')
            self.master.messages.put_nowait(f"Image saved to {save_path}")

    def reveal_in_explorer_callback(self):
        with ClipboardContext(error_callback=lambda e: self.master.messages.put_nowait(f"Failed to reveal file: {str(e)}")):
            if not win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
                self.master.messages.put_nowait("No file data in clipboard ~")
                return
            
            file_paths = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
            if not file_paths:
                self.master.messages.put_nowait("No file data in clipboard ~")
                return
            
            file_path = file_paths[0]
            if not os.path.exists(file_path):
                self.master.messages.put_nowait(f"File does not exist: {file_path}")

            subprocess.Popen(f'explorer /select,"{file_path}"')

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
            state = get_clipboard_state()
            text = f"Current State: {state}"
            if state in ["Image", "PNG Image"]:
                # self.clear_content_button.show()
                self.clear_format_button.hide()
                self.save_image_button.show()
                self.reveal_in_explorer_button.hide()
            elif state == "File":
                # self.clear_content_button.show()
                self.clear_format_button.hide()
                self.save_image_button.hide()
                self.reveal_in_explorer_button.show()
            else:
                self.clear_format_button.show()
                self.save_image_button.hide()
                self.reveal_in_explorer_button.hide()
            # elif state == '<Empty>':
            #     # self.clear_content_button.hide()
            #     self.clear_format_button.hide()
            #     self.save_image_button.hide()
            #     self.reveal_in_explorer_button.hide()
            # elif state in ["Rich Text", "Suspected Rich Text"]:
            #     # self.clear_content_button.show()
            #     self.clear_format_button.show()
            #     self.save_image_button.hide()
            #     self.reveal_in_explorer_button.hide()
            # elif state == "Plain Text":
            #     # self.clear_content_button.show()
            #     self.clear_format_button.hide()
            #     self.save_image_button.hide()
            #     self.reveal_in_explorer_button.hide()
            # else:
            #     # self.clear_content_button.show()
            #     self.clear_format_button.hide()
            #     self.save_image_button.hide()
            #     self.reveal_in_explorer_button.hide()
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
    def _error_callback(e):
        nonlocal error
        error = e.__class__.__name__
    with ClipboardContext(error_callback=_error_callback):
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

    if len(formats)==0:
        if error:
            result = error
        else:
            result = "<Empty>"
    elif 1 in formats or 7 in formats or 13 in formats:
        # text
        if 'HTML Format' in formats.values() or 'Rich Text Format' in formats.values():
            result = "Rich Text"
        elif set(formats.keys()).difference({1,7,13,16}):
            result = "Suspected Rich Text"
        else:
            result = "Plain Text"
    elif 2 in formats or 3 in formats or 6 in formats or 8 in formats or 14 in formats:
        result = "Image"
        if 'PNG' in formats.values():
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
