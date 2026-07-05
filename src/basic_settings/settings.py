import os
import subprocess
import json
import warnings
from dataclasses import dataclass, field, fields

os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

WORKING_DIR = os.path.join(os.environ['APPDATA'], 'PyScriptX', 'MyToolkits')
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
os.makedirs(WORKING_DIR, exist_ok=True)
os.chdir(WORKING_DIR)

@dataclass
class ColorSettings:
    fgcolor: str = "#DDDDDD"
    fgcolor2: str = "#88AA88"
    bgcolor: str = "#222222"
    bgcolor2: str = "#344999"
    window_bgcolor_default: str = "#366778"

    contextmenu_bgcolor_overwrite: str = ""
    contextmenu_hover_bgcolor_overwrite: str = ""
    contextmenu_fgcolor_overwrite: str = ""

    popup_fading_bgcolor: str = "#DDDDDD"
    popup_fading_fgcolor: str = "#222222"

    switchbutton_oncolor: str = '#0077cc'
    switchbutton_offcolor: str = '#aaaaaa'
    switchbutton_slidercolor: str = '#dddddd'

    keydisplayer_main_color_overwrite: str = ""
    keydisplayer_sub_color_overwrite: str = ""
    keydisplayer_fgcolor_overwrite: str = ""

    clipboardreader_text_color_overwrite: str = ""
    clipboardreader_background_color_overwrite: str = ""

    stopwatch_tube_color: str = "#FFFFFF"

    @property
    def text_color(self):
        return self.fgcolor
    
    @property
    def contextmenu_bgcolor(self):
        return self.contextmenu_bgcolor_overwrite or self.bgcolor
    
    @property
    def contextmenu_hover_bgcolor(self):
        return self.contextmenu_hover_bgcolor_overwrite or self.bgcolor2
    
    @property
    def contextmenu_fgcolor(self):
        return self.contextmenu_fgcolor_overwrite or self.fgcolor
    
    @property
    def pushbutton_default_bgcolor(self):
        return self.bgcolor2
    
    @property
    def pushbutton_default_fgcolor(self):
        return self.fgcolor
    
    @property
    def c1124_main_color(self):
        return self.keydisplayer_main_color_overwrite or self.bgcolor2
    
    @property
    def c1124_sub_color(self):
        return self.keydisplayer_sub_color_overwrite or self.bgcolor
    
    @property
    def c1124_fgcolor(self):
        return self.keydisplayer_fgcolor_overwrite or self.fgcolor
    
    @property
    def clipboardreader_text_color(self):
        return self.clipboardreader_text_color_overwrite or self.fgcolor
    
    @property
    def clipboardreader_background_color(self):
        return self.clipboardreader_background_color_overwrite or self.bgcolor
    
    # color conversion methods
    @staticmethod
    def color_string_to_tuple(color_string):
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


@dataclass
class GeometrySettings:
    window_width: int = 600
    window_height: int = 1000
    window_padding: int = 16
    window_hidden_exposing_width: int = 10
    shadow_margin: int = 5
    window_scrollbar_width: int = 12
    window_scrollbar_min_height: int = 20

    popup_window_width: int = 300
    popup_window_height: int = 100
    popup_fading_padding: int = 10
    popup_fading_yratio: float = 0.8
    
    switchbutton_size : int = 60
    switchbutton_padding : int = 5
    pushbutton_height : int = 60

    c1124_X_L : float = 0.6
    c1124_Y_R : float = 0.9
    c1124_margin : int = 10
    c1124_padding : int = 10
    c1124_borderRadius : int = 16

    window_border_radius: int = 50
    popup_fading_border_radius: int = 20
    contextmenu_border_radius: int = 20
    contextmenu_border_width: int = 2
    widgetbox_border_radius: int = 20

    stopwatch_tube_length : int = 128
    stopwatch_tube_width : int = 20
    stopwatch_size : int = 100 # px, height
    stopwatch_xpos : int = 50
    stopwatch_ypos : int = -200

    clipboardreader_geometry : str = "800x600+200+200"


@dataclass
class TimeSettings:
    "All settings, unless specified otherwise, are in milliseconds."
    window_animation_frames: int = 60
    window_animation_time_ms: int = 300
    window_checkmessage_interval: int = 1000 # ms
    window_checkapp_interval: int = 1000 # ms

    popup_fading_delay: int = 3000 # ms
    popup_fading_animation_duration: int = 500 # ms
    switchbutton_animation_interval: int = 10 # ms

    pushbutton_colordecay_mouseenter: int = 5
    pushbutton_colordecay_mouseleave: int = 10
    pushbutton_colordecay_mousepress: int = 2
    pushbutton_colordecay_mouserelease: int = 10
    pushbutton_colordecay_interval: int = 30 # ms

    c1124_release_event_delay: float = 1 # ms
    c1124_check_existence_interval: int = 200 #ms
    c1124_fadeout_delay: int = 3000 #ms
    c1124_fadeout_animation_duration: int = 2000 #ms
    c1124_move_duration: int = 300 #ms

    clipboard_refresh_interval: int = 500 # ms

    clicker_max_interval: int = 1000 # ms
    clicker_default_interval: int = 10 # ms


@dataclass
class OpacitySettings:
    reset_background_image_opacity: int = 100 # 0-255
    contextmenu_bgalpha: int = 200 # 0-255
    contextmenu_fgalpha: int = 200 # 0-255
    popup_fading_final_opacity: float = 0.7

    switchbutton_alpha: int = 200
    pushbutton_alpha: int = 150
    c1124_opacity: float = 0.8
    stopwatch_opacity: float = 0.8 # 0-1


@dataclass
class PathSettings:
    custom_icon_path: str = ""
    custom_config_path: str = ""
    custom_bgimage_path: str = ""
    custom_image_save_dir: str = ""

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


@dataclass
class Settings:
    font_name : str = "STXINWEI"
    font_size : int = 10
    font_size_large : int = 12

    window_title : str = "Joat917's Toolkit"
    window_welcome : str = "Hello there!"
    window_animation_K : float = 0.01 # 回弹系数
    window_animation_R : int = 100 # 回弹半径
    
    window_exitkey : str = 'F18'
    window_exitkey_code : int = 16777281 # F18
    window_toggleshowkey : str = 'F24'
    clicker_hotkey : str = 'F16'
    stopwatch_hotkey : str = 'F13'

    switchbutton_animation_K : float = 0.1
    switchbutton_animation_max_steps : int = 100

    pushbutton_hoverlighter : int = 110 # %
    pushbutton_presseddarker : int = 110 # %
    
    c1124_font_size_overwrite : int | None = None
    c1124_font_horizontal_scale : float = 2.0
    c1124_font_vertical_scale : float = 1.2

    droprunner_history_max : int = 5

    colors: ColorSettings = field(default_factory=ColorSettings)
    geometry: GeometrySettings = field(default_factory=GeometrySettings)
    times: TimeSettings = field(default_factory=TimeSettings)
    opacity: OpacitySettings = field(default_factory=OpacitySettings)
    paths: PathSettings = field(default_factory=PathSettings)

    def load(self):
        try:
            with open(self.paths.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, dict):
                warnings.warn(f"Settings file {self.paths.config_path} is not a valid JSON object. Using default settings.")
                return
            for key, value in data.items():
                if key in ['colors', 'geometry', 'times', 'opacity', 'paths']:
                    sub_settings = getattr(self, key)
                    if not isinstance(value, dict):
                        warnings.warn(f"Expected a dictionary for setting '{key}', but got {type(value)}. Ignoring.")
                        continue
                    for sub_key, sub_value in value.items():
                        if sub_key in sub_settings.__dict__:
                            setattr(sub_settings, sub_key, sub_value)
                        else:
                            warnings.warn(f"Unknown setting '{sub_key}' in '{key}'. Ignoring.")
                    continue
                if key in self.__dict__:
                    setattr(self, key, value)
                    continue
                for sub_settings in [self.colors, self.geometry, self.times, self.opacity, self.paths]:
                    if key in sub_settings.__dict__:
                        setattr(sub_settings, key, value)
                        break
                else:
                    warnings.warn(f"Expected type {type(getattr(self, key))} for setting '{key}', but got {type(value)}. Using default value.")
        except FileNotFoundError:
            self.save()
        except Exception as e:
            warnings.warn(f"Error loading settings: {e}")
        

    def save(self, diff_only=False):
        os.makedirs(os.path.dirname(self.paths.config_path), exist_ok=True)
        data = {}
        for field in fields(self):
            key = field.name
            value = getattr(self, key)
            if key in ['colors', 'geometry', 'times', 'opacity', 'paths']:
                sub_data = {}
                for sub_field in fields(value):
                    sub_key = sub_field.name
                    sub_value = getattr(value, sub_key)
                    if not diff_only or sub_value != sub_field.default:
                        sub_data[sub_key] = sub_value
                if sub_data:
                    data[key] = sub_data
            else:
                if not diff_only or value != field.default:
                    data[key] = value
        try:
            with open(self.paths.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            warnings.warn(f"Error saving settings: {e}")
    
    @property
    def c1124_font_size(self):
        return self.c1124_font_size_overwrite or self.font_size
    
    def open_popup_file(self):
        subprocess.Popen("explorer /select,\"{}\"".format(self.paths.config_path))

    def __getattr__(self, name):
        # 擦屁股
        if name in self.paths.__dict__:
            warnings.warn(
                f"Accessing path setting '{name}' directly is deprecated. Use SETTINGS.paths.{name} instead.", 
                DeprecationWarning, stacklevel=2
            )
            return getattr(self.paths, name)
        elif name in self.colors.__dict__:
            warnings.warn(
                f"Accessing color setting '{name}' directly is deprecated. Use SETTINGS.colors.{name} instead.", 
                DeprecationWarning, stacklevel=2
            )
            return getattr(self.colors, name)
        elif name in self.geometry.__dict__:
            warnings.warn(
                f"Accessing geometry setting '{name}' directly is deprecated. Use SETTINGS.geometry.{name} instead.", 
                DeprecationWarning, stacklevel=2
            )
            return getattr(self.geometry, name)
        elif name in self.times.__dict__:
            warnings.warn(
                f"Accessing time setting '{name}' directly is deprecated. Use SETTINGS.times.{name} instead.", 
                DeprecationWarning, stacklevel=2
            )
            return getattr(self.times, name)
        elif name in self.opacity.__dict__:
            warnings.warn(
                f"Accessing opacity setting '{name}' directly is deprecated. Use SETTINGS.opacity.{name} instead.", 
                DeprecationWarning, stacklevel=2
            )
            return getattr(self.opacity, name)

SETTINGS = Settings()
SETTINGS.load()
