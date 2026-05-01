def format_seconds_to_text(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} 秒"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    text = ""
    if d > 0:
        text += f"{int(d)}天 "
    if h > 0:
        text += f"{int(h)}小时 "
    if m > 0:
        text += f"{int(m)}分钟 "
    if d == 0 and h == 0:
        text += f"{int(s)}秒"
    return text.strip()
