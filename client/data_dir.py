import os
import sys
import json


_basedir = os.path.dirname(os.path.abspath(__file__))


def _from_cmdline() -> str | None:
    for arg in sys.argv[1:]:
        if arg.startswith("--data-dir="):
            return arg.split("=", 1)[1].strip().strip('"')
    return None


def _from_portable() -> str | None:
    if os.path.exists(os.path.join(_basedir, "portable.txt")):
        return os.path.join(_basedir, "data")
    return None


def _from_data_directory_json() -> str | None:
    path = os.path.join(_basedir, "data_directory.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            d = data.get("dataDirectory")
            if d and os.path.isdir(d):
                return d
        except Exception:
            pass
    return None


def _from_legacy_settings() -> str | None:
    """兼容旧版本：settings.json 在程序目录且里面有 dataDirectory"""
    path = os.path.join(_basedir, "settings.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            d = data.get("dataDirectory")
            if d and os.path.isdir(d):
                return d
        except Exception:
            pass
    return None


def _default_appdata() -> str:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        local_appdata = os.path.expanduser("~\\AppData\\Local")
    return os.path.join(local_appdata, "desktopActivitySystem", "data")


def get_data_dir() -> str:
    for fn in (_from_cmdline, _from_portable, _from_data_directory_json, _from_legacy_settings, _default_appdata):
        d = fn()
        if d:
            return d
    return _default_appdata()


def set_data_dir(path: str) -> None:
    path = os.path.normpath(os.path.abspath(path))
    os.makedirs(path, exist_ok=True)
    config_path = os.path.join(_basedir, "data_directory.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump({"dataDirectory": path}, f, ensure_ascii=False, indent=2)


def is_data_dir_configured() -> bool:
    return _from_data_directory_json() is not None or _from_portable() is not None or _from_legacy_settings() is not None
