import os
import subprocess
import json
import warnings

os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

WORKING_DIR = os.path.join(os.environ['APPDATA'], 'PyScriptX', 'MyToolkits')
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
os.makedirs(WORKING_DIR, exist_ok=True)
os.chdir(WORKING_DIR)

class Settings:
    def __init__(self):
        self.initialize()
        self.load()

    def load(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for key, value in data.items():
                if not (hasattr(self, key) and key in self.editable_keys()):
                    continue
                if type(getattr(self, key)) == type(value):
                    setattr(self, key, value)
                elif isinstance(getattr(self, key), tuple) and isinstance(value, list):
                    setattr(self, key, tuple(value))
                else:
                    warnings.warn(f"Expected type {type(getattr(self, key))} for setting '{key}', but got {type(value)}. Using default value.")
        except FileNotFoundError:
            self.save()
        except Exception as e:
            warnings.warn(f"Error loading settings: {e}")
        

    def save(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        data = {}
        for key in self.editable_keys():
            data[key] = getattr(self, key)
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            warnings.warn(f"Error saving settings: {e}")


    def initialize(self):
        self.font_name = "STXINWEI"
        self.text_color = "#FFFFFF"
        self.font_size = 10
        self.font_size_large = 12

        self.window_width = 600
        self.window_height = 1000
        self.window_padding = 16
        self.shadow_margin = 16
        self.window_title = "Joat917's Toolkit"
        self.window_welcome = "Hello there!"
        self.window_border_radius = 50
        self.window_animation_K = 0.01 # 回弹系数
        self.window_animation_R = 100 # 回弹半径
        self.window_animation_frames = 60
        self.window_animation_time_ms = 300
        self.window_scrollbar_width = 12
        self.window_scrollbar_min_height = 20
        self.window_checkmessage_interval = 1000 # ms
        self.window_checkapp_interval = 1000 # ms
        self.window_exitkey = 'F18'
        self.window_exitkey_code = 16777281 # F18
        self.window_toggleshowkey = 'F24'
        self.window_default_bgcolor = "#366778"

        self.reset_background_image_opacity = 100 # 0-255

        self.contextmenu_bgcolor = "#333333"
        self.contextmenu_hover_bgcolor = "#415B91"
        self.contextmenu_fgcolor = "#FFFFFF"
        self.contextmenu_bgalpha = 200 # 0-255
        self.contextmenu_fgalpha = 200 # 0-255
        self.contextmenu_border_radius = 20
        self.contextmenu_border_width = 2 # px

        self.widgetbox_border_radius = 20

        self.popup_window_width = 300
        self.popup_window_height = 100
        self.popup_fading_bgcolor = "#DDDDDD"
        self.popup_fading_fgcolor = "#222222"
        self.popup_fading_border_radius = 20
        self.popup_fading_padding = 10
        self.popup_fading_final_opacity = 0.7
        self.popup_fading_delay = 3000 # ms
        self.popup_fading_animation_duration = 500 # ms
        self.popup_fading_yratio = 0.8

        self.switchbutton_size = 60
        self.switchbutton_padding = 5
        self.switchbutton_alpha = 200
        self.switchbutton_oncolor = '#0077cc'
        self.switchbutton_offcolor = '#aaaaaa'
        self.switchbutton_slidercolor = '#dddddd'
        self.switchbutton_animation_interval = 10 # ms
        self.switchbutton_animation_K = 0.1
        self.switchbutton_animation_max_steps = 100

        self.pushbutton_height = 60
        self.pushbutton_hoverlighter = 110 # %
        self.pushbutton_presseddarker = 110 # %
        self.pushbutton_default_bgcolor = '#6464fa'
        self.pushbutton_default_fgcolor = '#ffffff'
        self.pushbutton_alpha = 150
        self.pushbutton_colordecay_mouseenter = 5
        self.pushbutton_colordecay_mouseleave = 10
        self.pushbutton_colordecay_mousepress = 2
        self.pushbutton_colordecay_mouserelease = 10
        self.pushbutton_colordecay_interval = 30 # ms

        self.c1124_X_L = 0.6
        self.c1124_Y_R = 0.9
        self.c1124_margin = 10
        self.c1124_padding = 10
        self.c1124_borderRadius = 16
        self.c1124_opacity = 0.8
        self.c1124_main_color = '#FFA500'
        self.c1124_sub_color = '#DDDDDD'
        self.c1124_font_size = 10
        self.c1124_font_horizontal_scale = 2.0
        self.c1124_font_vertical_scale = 1.2
        self.c1124_release_event_delay = 0.001 #s
        self.c1124_check_existence_interval = 200 #ms
        self.c1124_fadeout_delay = 3000 #ms
        self.c1124_fadeout_animation_duration = 2000 #ms
        self.c1124_move_duration = 300 #ms

        self.droprunner_history_max = 3

        self.clipboard_refresh_interval = 500 # ms
        self.clipboardreader_text_color = "#000000"
        self.clipboardreader_background_color = "#FFFFFF"
        self.clipboardreader_geometry = "800x600+200+200"

        self.clicker_max_interval = 1000 # ms
        self.clicker_default_interval = 10 # ms
        self.clicker_hotkey = 'F16'

        self.stopwatch_tube_length = 128
        self.stopwatch_tube_width = 20
        self.stopwatch_tube_color = "#FFFFFF"
        self.stopwatch_size = 100 # px, height
        self.stopwatch_xpos = 50
        self.stopwatch_ypos = -200
        self.stopwatch_opacity = 0.8 # 0-1
        self.stopwatch_hotkey = 'F13'

        self.custom_icon_path = None
        self.custom_config_path = None
        self.custom_bgimage_path = None
        self.custom_image_save_dir = None

    def keys(self):
        for key in dir(self):
            if not key.startswith("_") and not callable(getattr(self, key)):
                yield key

    def editable_keys(self):
        for key in self.keys():
            if hasattr(Settings, key) and isinstance(getattr(Settings, key), property):
                continue
            yield key

    @property
    def working_dir(self):
        return WORKING_DIR
    
    @property
    def project_dir(self):
        return PROJECT_DIR
    
    @property
    def src_dir(self):
        return os.path.join(PROJECT_DIR, 'src')
    
    @property
    def config_path(self):
        if self.custom_config_path and os.path.isfile(self.custom_config_path):
            return self.custom_config_path
        return os.path.join(WORKING_DIR, 'settings.json')
    
    @property
    def img_dir(self):
        pth = os.path.join(WORKING_DIR, 'img')
        os.makedirs(pth, exist_ok=True)
        return pth

    @property
    def icon_path(self):
        if self.custom_icon_path and os.path.isfile(self.custom_icon_path):
            return self.custom_icon_path
        return os.path.join(PROJECT_DIR, 'assets', 'icon.png')
    
    @property
    def namexfilepath(self):
        return os.path.join(PROJECT_DIR, 'assets', 'namex_data.a85.txt')
    
    @property
    def error_log_file(self):
        return os.path.join(self.working_dir, 'error_log.txt')
    
    @property
    def window_bgimage_path(self):
        if self.custom_bgimage_path and os.path.isfile(self.custom_bgimage_path):
            return self.custom_bgimage_path
        return os.path.join(self.img_dir, "bg_image.png")
    
    @property
    def clipboard_image_save_dir(self):
        if self.custom_image_save_dir and os.path.isdir(self.custom_image_save_dir):
            return self.custom_image_save_dir
        return os.path.expanduser('~/Pictures')
    
    def color_string_to_tuple(self, color_string):
        from PIL import ImageColor
        try:
            rgb = ImageColor.getrgb(color_string)
            return rgb
        except Exception as e:
            warnings.warn(f"Error converting color string '{color_string}' to tuple: {e}")
            return (0, 0, 0)
    
    @property
    def switchbutton_oncolor_tuple(self):
        return self.color_string_to_tuple(self.switchbutton_oncolor)
    
    @property
    def switchbutton_offcolor_tuple(self):
        return self.color_string_to_tuple(self.switchbutton_offcolor)
    
    @property
    def switchbutton_slidercolor_tuple(self):
        return self.color_string_to_tuple(self.switchbutton_slidercolor)
    
    @property
    def contextmenu_bgcolor_tuple(self):
        return self.color_string_to_tuple(self.contextmenu_bgcolor)
    
    @property
    def contextmenu_hover_bgcolor_tuple(self):
        return self.color_string_to_tuple(self.contextmenu_hover_bgcolor)
    
    @property
    def contextmenu_fgcolor_tuple(self):
        return self.color_string_to_tuple(self.contextmenu_fgcolor)
    
    def open_popup_file(self):
        subprocess.Popen("explorer /select,\"{}\"".format(self.config_path))


SETTINGS = Settings()
