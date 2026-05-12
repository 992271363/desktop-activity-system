import os


def normalize_exe_path(path: str) -> str:
    if not path:
        return ""
    return os.path.normcase(os.path.normpath(path.strip()))
