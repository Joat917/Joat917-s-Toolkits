from basic_settings import *

class CustomMenu(QMenu):
    "更好看的菜单（默认不内置任何按钮，可自行添加）"
    def __init__(self, parent:QWidget=None):
        super().__init__(parent)

        # 透明背景
        self.setStyleSheet("background-color: transparent;")
        self.setWindowFlags(self.windowFlags()|Qt.FramelessWindowHint|Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # 设置按钮样式
        self.setStyleSheet(f"""
            QMenu {{
                background-color: rgba{SETTINGS.contextmenu_bgcolor_tuple+(SETTINGS.contextmenu_bgalpha,)};
                color: rgba{SETTINGS.contextmenu_fgcolor_tuple+(SETTINGS.contextmenu_fgalpha,)};
                border-radius: {SETTINGS.contextmenu_border_radius}px;
                border: {SETTINGS.contextmenu_border_width}px solid rgba{SETTINGS.contextmenu_fgcolor_tuple+(SETTINGS.contextmenu_fgalpha,)};
            }}
            QMenu::item {{
                padding: 8px 24px;
                background-color: transparent;
                border-radius: {SETTINGS.contextmenu_border_radius}px;
            }}
            QMenu::item:selected {{
                background-color: rgba{SETTINGS.contextmenu_hover_bgcolor_tuple+(SETTINGS.contextmenu_bgalpha,)};
                border-radius: {SETTINGS.contextmenu_border_radius}px;
            }}
        """)

