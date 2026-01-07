# 连点器

from base_import import *
from main_window import MainWindow, WidgetBox, PlainText
from switch_widgets import SwitchButton

class ClickerWidget(WidgetBox):
    def __init__(self, master:MainWindow):
        super().__init__(parent=master, title="Clicker Settings")
        self.master = master

        self.switch_button = SwitchButton(
            onchange=self.toggle_enabled
        )
        self.switch_button_label = PlainText(
            text="Clicker is Disabled",
        )
        self.enabling_sublayout = QHBoxLayout()
        self.enabling_sublayout.addWidget(self.switch_button)
        self.enabling_sublayout.addWidget(self.switch_button_label)
        self.layout.addLayout(self.enabling_sublayout)

        self._mouse_button = pynput.mouse.Button.left
        self.mouse_button_switcher = SwitchButton(
            onchange=self.toggle_mouse_button
        )
        self.mouse_button_switcher_label = PlainText(
            text="Mouse Button: Left",
        )
        self.mouse_button_sublayout = QHBoxLayout()
        self.mouse_button_sublayout.addWidget(self.mouse_button_switcher)
        self.mouse_button_sublayout.addWidget(self.mouse_button_switcher_label)
        self.layout.addLayout(self.mouse_button_sublayout)

        self.interval_label = QLabel("Interval (ms):")
        self.interval_label.setFont(QFont(FONT_NAME))
        self.interval_label.setStyleSheet(f"color:{PlainText.TEXT_COLOR}")
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 1000)
        self.interval_input.setValue(10)
        self.interval_input.setFont(QFont(FONT_NAME))
        self.interval_input.setStyleSheet(f"color:{PlainText.TEXT_COLOR}")

        self.interval_setting_sublayout = QHBoxLayout()
        self.interval_setting_sublayout.addWidget(self.interval_label)
        self.interval_setting_sublayout.addWidget(self.interval_input)
        self.layout.addLayout(self.interval_setting_sublayout)

        self.hotkey_guideline = PlainText(
            text="Hold F16 to begin clicking",
        )
        self.layout.addWidget(self.hotkey_guideline)

        self.enabled = False
        self.clicking = False
        self.click_timer = QTimer()
        self.click_timer.timeout.connect(self.perform_click)

        self.mouseCtrl=pynput.mouse.Controller()
        self._mouse_down = False

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
        if key=='F16':
            self.start_clicking()
    
    def stop_clicking_callback(self, key):
        if key=='F16':
            self.stop_clicking()

    def closeEvent(self, a0):
        self.stop_clicking()
        self.master.globalKeyboardListener.press_callbacks.remove(self.start_clicking_callback)
        self.master.globalKeyboardListener.release_callbacks.remove(self.stop_clicking_callback)
        self.click_timer.timeout.disconnect()
        return super().closeEvent(a0)

