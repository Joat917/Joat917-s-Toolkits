# 连点器

from basic_settings import *
from main_widgets import MainWindow, WidgetBox, PlainText, SwitchButton


class ClickerWidget(WidgetBox):
    def __init__(self, master:MainWindow):
        super().__init__(parent=master, title="Clicker")
        self.master = master

        self.switch_button = SwitchButton(
            onchange=self.toggle_enabled, 
            parent=self
        )
        self.switch_button_label = PlainText(
            text="Clicker is Disabled", 
            parent=self
        )
        self.addLine(self.switch_button, self.switch_button_label)

        self._mouse_button = pynput.mouse.Button.left
        self.mouse_button_switcher = SwitchButton(
            onchange=self.toggle_mouse_button, 
            parent=self
        )
        self.mouse_button_switcher_label = PlainText(
            text="Mouse Button: Left", 
            parent=self
        )
        self.addLine(self.mouse_button_switcher, self.mouse_button_switcher_label)

        self.interval_label = QLabel("Interval (ms):")
        self.interval_label.setFont(QFont(SETTINGS.font_name))
        self.interval_label.setStyleSheet(f"color:{SETTINGS.text_color}")
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, SETTINGS.clicker_max_interval)
        self.interval_input.setValue(SETTINGS.clicker_default_interval)
        self.interval_input.setFont(QFont(SETTINGS.font_name))
        self.interval_input.setStyleSheet(f"color:{SETTINGS.text_color}")
        self.addLine(self.interval_label, self.interval_input)

        self.hotkey_guideline = PlainText(
            text=f"Hold {SETTINGS.clicker_hotkey} to begin clicking", 
            parent=self
        )
        self.add(self.hotkey_guideline)

        self.enabled = False
        self.clicking = False
        self.click_timer = QTimer()
        self.click_timer.timeout.connect(self.perform_click)

        self.mouseCtrl=pynput.mouse.Controller()
        self._mouse_down = False

        if self.master.globalKeyboardListener is not None:
            self.master.globalKeyboardListener.press_callbacks.append(self.start_clicking_callback)
            self.master.globalKeyboardListener.release_callbacks.append(self.stop_clicking_callback)

        self.toggle_enabled(False)

    def toggle_enabled(self, checked):
        self.enabled = checked
        if self.enabled:
            self.switch_button_label.setText("Clicker is Enabled")
            self.interval_input.show()
            self.interval_label.show()
            self.mouse_button_switcher.show()
            self.mouse_button_switcher_label.show()
            self.hotkey_guideline.show()
        else:
            self.switch_button_label.setText("Clicker is Disabled")
            self.interval_input.hide()
            self.interval_label.hide()
            self.mouse_button_switcher.hide()
            self.mouse_button_switcher_label.hide()
            self.hotkey_guideline.hide()

        if not self.enabled or self.clicking:
            self.stop_clicking()

    def toggle_mouse_button(self, checked):
        if checked:
            self._mouse_button = pynput.mouse.Button.right
            self.mouse_button_switcher_label.setText("Mouse Button: Right")
        else:
            self._mouse_button = pynput.mouse.Button.left
            self.mouse_button_switcher_label.setText("Mouse Button: Left")

    def start_clicking(self):
        if self.enabled and not self.clicking:
            interval = self.interval_input.value()
            self.click_timer.start(interval)
            self.clicking = True

    def stop_clicking(self):
        self.click_timer.stop()
        if self._mouse_down:
            self.mouseCtrl.release(pynput.mouse.Button.left)
            self.mouseCtrl.release(pynput.mouse.Button.right)
            self._mouse_down = False
        self.clicking = False

    def perform_click(self):
        if not self._mouse_down:
            self.mouseCtrl.press(self._mouse_button)
            self._mouse_down = True
        else:
            self.mouseCtrl.release(self._mouse_button)
            self._mouse_down = False

    def start_clicking_callback(self, key):
        if key==SETTINGS.clicker_hotkey:
            self.start_clicking()
    
    def stop_clicking_callback(self, key):
        if key==SETTINGS.clicker_hotkey:
            self.stop_clicking()

    def closeEvent(self, a0):
        self.stop_clicking()
        if self.master.globalKeyboardListener is not None:
            self.master.globalKeyboardListener.press_callbacks.remove(self.start_clicking_callback)
            self.master.globalKeyboardListener.release_callbacks.remove(self.stop_clicking_callback)
        self.click_timer.timeout.disconnect()
        self.click_timer.stop()
        self.click_timer.deleteLater()
        self.deleteLater()
        return super().closeEvent(a0)

