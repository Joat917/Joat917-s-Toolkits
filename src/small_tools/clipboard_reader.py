# 转写自已有文件ClipBoardReader.pyw，后者基于tkinter实现

# import patch
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from basic_settings import *

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


def _byte_to_lines(data: bytes):
	out = ""
	while data:
		current = data[:16]
		data = data[16:]
		line = ' '.join('%02X' % i for i in current)
		out += line + '\n'
	return out[:-1]


def _data_to_text_data(data, text_length_limit=2048, byte_length_limit=1024, max_output_limit=32768):
	encoding_name = "Unknown"
	try:
		if isinstance(data, str):
			text_data = data
			encoding_name = "String"
		elif isinstance(data, bytes):
			try:
				try:
					text_data = data.decode('ascii')
					if text_data and text_data[-1] == '\x00':
						text_data = text_data[:-1]
					if len(text_data) > text_length_limit:
						text_data = text_data[:text_length_limit] + '\n' + f"(...,total {len(text_data)} chars)"
					encoding_name = "ASCII"
				except UnicodeDecodeError:
					text_data = data.decode('utf-8')
					if text_data and text_data[-1] == '\x00':
						text_data = text_data[:-1]
					if len(text_data) > text_length_limit:
						text_data = text_data[:text_length_limit] + '\n' + f"(...,total {len(text_data)} chars)"
					encoding_name = "UTF-8"
			except UnicodeDecodeError:
				text_data = data.decode('gb18030')
				if text_data and text_data[-1] == '\x00':
					text_data = text_data[:-1]
				if len(text_data) > text_length_limit:
					text_data = text_data[:text_length_limit] + '\n' + f"(...,total {len(text_data)} chars)"
				encoding_name = "GB18030"
			for c in text_data:
				if ord(c) < 32 and c not in '\r\n\t':
					raise RuntimeError
		else:
			raise RuntimeError
	except UnicodeDecodeError:
		if len(data) > byte_length_limit:
			text_data = _byte_to_lines(data[:byte_length_limit]) + '\n' + f"(...,total {len(data)} bytes)"
		else:
			text_data = _byte_to_lines(data)
		encoding_name = "RAW"
	except RuntimeError:
		if isinstance(data, (bytes, bytearray)):
			if len(data) > byte_length_limit:
				text_data = _byte_to_lines(data[:byte_length_limit]) + '\n' + f"(...,total {len(data)} bytes)"
			else:
				text_data = _byte_to_lines(data)
			encoding_name = "RAW"
		else:
			text_data = repr(data)
	if len(text_data) > max_output_limit:
		text_data = text_data[:max_output_limit] + f"(...,total {len(text_data)} chars)"
	return text_data, encoding_name


def get_clipboard_detail(max_error_time=16) -> str:
	result = ""
	try:
		win32clipboard.OpenClipboard()
		format_id = win32clipboard.EnumClipboardFormats(0)
		error_capacity = max_error_time
		while format_id != 0 and error_capacity > 0:
			format_name = None
			try:
				if format_id in known_formats:
					format_name = known_formats[format_id]
				else:
					format_name = win32clipboard.GetClipboardFormatName(format_id)
			except Exception as e:
				format_name = str(e)

			try:
				data = win32clipboard.GetClipboardData(format_id)
				text_data, encoding_name = _data_to_text_data(data)
				result += f"ID={format_id} \nName={format_name} \nEncoding={encoding_name}\n===CONTENT START===\n"
				result += text_data
				result += "\n===CONTENT END===\n\n"
				old_format_id = format_id
				format_id = win32clipboard.EnumClipboardFormats(format_id)
				if format_id == old_format_id:
					break
				if len(result) > 131072:
					raise RuntimeError("Output length overflow")
			except pywintypes.error as e:
				result += f"ID={format_id} \nName={format_name} \nError accessing clipboard with format_id: {e}\n\n"
				error_capacity -= 1
		if error_capacity <= 0:
			result += "Error handling capacity exceed."
	except Exception as e:
		import traceback
		result += f"Error accessing clipboard: {traceback.format_exc()}\n\n"
	finally:
		try:
			win32clipboard.CloseClipboard()
		except Exception:
			pass
	return result


def get_clipboard_status() -> str:
	try:
		output = pyperclip.paste()
	except Exception:
		output = ""
	if output:
		return output + "\n\n( Below is detail info of your clipboard: )\n\n" + get_clipboard_detail()
	else:
		return "( Cannot get text from clipboard. Below is the detail info of your clipboard: )\n\n" + get_clipboard_detail()

class ClipboardMonitorWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.clipboard_content = ""

		self.init_ui()
		self.apply_settings()

		self.timer = QTimer(self)
		self.timer.setInterval(SETTINGS.clipboard_refresh_interval)
		self.timer.timeout.connect(self.check_clipboard)
		self.timer.start()

	def init_ui(self):
		self.setWindowTitle('Clipboard Monitor')
		self.setWindowIcon(QIcon(SETTINGS.icon_path))

		central = QWidget()
		self.setCentralWidget(central)

		vbox = QVBoxLayout(central)

		# Button row
		hbox = QHBoxLayout()
		self.btn_settings = QPushButton('Settings')
		self.btn_settings.clicked.connect(SETTINGS.open_popup_file)
		hbox.addWidget(self.btn_settings)

		self.btn_clear_content = QPushButton('Clear Content')
		self.btn_clear_content.clicked.connect(self.clear_clipboard)
		hbox.addWidget(self.btn_clear_content)

		self.btn_clear_format = QPushButton('Clear Format')
		self.btn_clear_format.clicked.connect(self.clear_format)
		hbox.addWidget(self.btn_clear_format)

		self.btn_close = QPushButton('Close')
		self.btn_close.clicked.connect(self.close)
		hbox.addWidget(self.btn_close)

		vbox.addLayout(hbox)

		# Text area
		self.text_widget = QTextEdit()
		self.text_widget.setReadOnly(True)
		vbox.addWidget(self.text_widget)

	def apply_settings(self):
		# geometry
		try:
			geom = SETTINGS.clipboardreader_geometry
			# expected format wxh+x+y
			if '+' in geom and 'x' in geom:
				parts = geom.split('+')
				size = parts[0]
				x = int(parts[1]) if len(parts) > 1 else 200
				y = int(parts[2]) if len(parts) > 2 else 200
				w, h = size.split('x')
				self.setGeometry(int(x), int(y), int(w), int(h))
		except Exception:
			pass

		font = QFont(SETTINGS.font_name, SETTINGS.font_size)
		self.text_widget.setFont(font)
		# colors
		self.text_widget.setStyleSheet(f"color: {SETTINGS.clipboardreader_text_color}; background-color: {SETTINGS.clipboardreader_background_color};")

	def check_clipboard(self):
		try:
			new_content = get_clipboard_status()
			if new_content != self.clipboard_content:
				self.clipboard_content = new_content
				self.update_text_widget(new_content)
		except Exception as e:
			warnings.warn(f"Error accessing clipboard: {e}")

	def update_text_widget(self, content):
		self.text_widget.setPlainText(content)

	def clear_clipboard(self):
		try:
			win32clipboard.OpenClipboard()
			win32clipboard.EmptyClipboard()
		except Exception as e:
			warnings.warn(f"clear_clipboard error: {e}")
		finally:
			try:
				win32clipboard.CloseClipboard()
			except Exception:
				pass

	def clear_format(self):
		try:
			content = pyperclip.paste()
			if content:
				self.clear_clipboard()
				pyperclip.copy(content)
		except Exception as e:
			warnings.warn(f"clear_format error: {e}")

	def moveEvent(self, event):
		self.save_geometry()
		super().moveEvent(event)

	def resizeEvent(self, event):
		self.save_geometry()
		super().resizeEvent(event)

	def save_geometry(self):
		try:
			geom = self.geometry()
			x = geom.x()
			y = geom.y()
			w = geom.width()
			h = geom.height()
			SETTINGS.clipboardreader_geometry = f"{w}x{h}+{x}+{y}"
			# SETTINGS.save()
		except Exception:
			pass

	def closeEvent(self, event):
		self.save_geometry()
		SETTINGS.save()
		self.timer.timeout.disconnect()
		self.timer.stop()
		self.timer.deleteLater()
		super().closeEvent(event)


def main():
	app = QApplication(sys.argv)
	window = ClipboardMonitorWindow()
	window.show()
	sys.exit(app.exec_())


if __name__ == '__main__':
	main()
