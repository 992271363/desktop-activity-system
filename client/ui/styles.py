from util.path import _program_dir
from ui.theme_light import MODERN_LIGHT_QSS as _LIGHT_RAW
from ui.theme_dark import MODERN_DARK_QSS as _DARK_RAW

_ICONS_DIR = _program_dir().replace("\\", "/") + "/icons"
MODERN_LIGHT_QSS = _LIGHT_RAW.replace("__ICONS_DIR__", _ICONS_DIR)
MODERN_DARK_QSS = _DARK_RAW.replace("__ICONS_DIR__", _ICONS_DIR)
