import json
import os

from util.path import _settings_dir, get_data_dir


def update_state(data_dir: str = None):
    """写入 uninstall_state.json，供卸载程序读取实际数据目录。"""
    if data_dir is None:
        data_dir = get_data_dir()
    state_file = os.path.join(_settings_dir(), "uninstall_state.json")
    state = {
        "dataDirectory": os.path.normpath(data_dir),
        "settingsDirectory": os.path.normpath(_settings_dir()),
    }
    os.makedirs(_settings_dir(), exist_ok=True)
    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[State] 写入卸载状态失败: {e}")
