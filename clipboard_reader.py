# 转写自已有文件ClipBoardReader.pyw，后者基于tkinter实现

import sys
import os
import json
import threading
import time
import pyperclip
import win32clipboard
import pywintypes
from PIL import Image, ImageDraw, ImageFont
from PyQt5 import QtWidgets, QtGui, QtCore

from base_import import WORKING_DIR, ICON_PATH

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


class Settings:
	def __init__(self, filename="settings.json"):
		self.font_family = "Arial"
		self.font_size = 12
		self.text_color = "#000000"
		self.background_color = "#FFFFFF"
		self.window_geometry = "800x600+200+200"
		self.filename = filename

	def load_from_json(self):
		try:
			with open(self.filename, 'r', encoding='utf-8') as file:
				data = json.load(file)
				self.font_family = data.get("font_family", self.font_family)
				self.font_size = data.get("font_size", self.font_size)
				self.text_color = data.get("text_color", self.text_color)
				self.background_color = data.get("background_color", self.background_color)
				self.window_geometry = data.get("window_geometry", self.window_geometry)
		except FileNotFoundError:
			pass
		except json.decoder.JSONDecodeError as e:
			print(f"Error decoding json: {e}")

	def save_to_json(self):
		settings_data = {
			"font_family": self.font_family,
			"font_size": self.font_size,
			"text_color": self.text_color,
			"background_color": self.background_color,
			"window_geometry": self.window_geometry
		}
		try:
			with open(self.filename, 'w', encoding='utf-8') as file:
				json.dump(settings_data, file, indent=4)
		except Exception as e:
			print(f"Error saving settings: {e}")

	def open_popup_file(self):
		try:
			if os.name == 'nt':
				os.startfile(os.path.abspath(self.filename))
			else:
				os.system(f"xdg-open \"{os.path.abspath(self.filename)}\"")
		except Exception as e:
			print(f"Cannot open settings file: {e}")


class ClipboardMonitorWindow(QtWidgets.QMainWindow):
	def __init__(self, settings: Settings):
		super().__init__()
		self.settings = settings
		self.clipboard_content = ""

		self.init_ui()
		self.apply_settings()

		# Timer to poll clipboard every second
		self.timer = QtCore.QTimer(self)
		self.timer.setInterval(1000)
		self.timer.timeout.connect(self.check_clipboard)
		self.timer.start()

	def init_ui(self):
		self.setWindowTitle('Clipboard Monitor')
		self.setWindowIcon(QtGui.QIcon(ICON_PATH))

		central = QtWidgets.QWidget()
		self.setCentralWidget(central)

		vbox = QtWidgets.QVBoxLayout(central)

		# Button row
		hbox = QtWidgets.QHBoxLayout()
		self.btn_settings = QtWidgets.QPushButton('Settings')
		self.btn_settings.clicked.connect(self.settings.open_popup_file)
		hbox.addWidget(self.btn_settings)

		self.btn_clear_content = QtWidgets.QPushButton('Clear Content')
		self.btn_clear_content.clicked.connect(self.clear_clipboard)
		hbox.addWidget(self.btn_clear_content)

		self.btn_clear_format = QtWidgets.QPushButton('Clear Format')
		self.btn_clear_format.clicked.connect(self.clear_format)
		hbox.addWidget(self.btn_clear_format)

		self.btn_close = QtWidgets.QPushButton('Close')
		self.btn_close.clicked.connect(self.close)
		hbox.addWidget(self.btn_close)

		vbox.addLayout(hbox)

		# Text area
		self.text_widget = QtWidgets.QTextEdit()
		self.text_widget.setReadOnly(True)
		vbox.addWidget(self.text_widget)

	def apply_settings(self):
		# geometry
		try:
			geom = self.settings.window_geometry
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

		font = QtGui.QFont(self.settings.font_family, int(self.settings.font_size))
		self.text_widget.setFont(font)
		# colors
		self.text_widget.setStyleSheet(f"color: {self.settings.text_color}; background-color: {self.settings.background_color};")

	def check_clipboard(self):
		try:
			new_content = get_clipboard_status()
			if new_content != self.clipboard_content:
				self.clipboard_content = new_content
				self.update_text_widget(new_content)
		except Exception as e:
			print(f"Error accessing clipboard: {e}")

	def update_text_widget(self, content):
		self.text_widget.setPlainText(content)

	def clear_clipboard(self):
		try:
			win32clipboard.OpenClipboard()
			win32clipboard.EmptyClipboard()
		except Exception as e:
			print(f"clear_clipboard error: {e}")
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
			print(f"clear_format error: {e}")

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
			self.settings.window_geometry = f"{w}x{h}+{x}+{y}"
			self.settings.save_to_json()
		except Exception:
			pass

	def closeEvent(self, event):
		self.save_geometry()
		self.timer.timeout.disconnect()
		self.timer.stop()
		self.timer.deleteLater()
		super().closeEvent(event)


def main():
	settings = Settings(os.path.join(WORKING_DIR, "clipboard_reader_settings.json"))
	settings.load_from_json()

	app = QtWidgets.QApplication(sys.argv)
	window = ClipboardMonitorWindow(settings)
	window.show()
	sys.exit(app.exec_())


if __name__ == '__main__':
	main()
