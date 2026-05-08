def format_seconds_to_text(seconds: int) -> str:  # 秒数转为可读时长文本
    if seconds < 60:  # 不足一分钟直接返回秒
        return f"{seconds} 秒"
    m, s = divmod(seconds, 60)  # 分出分钟和剩余秒
    h, m = divmod(m, 60)  # 分出小时和剩余分钟
    d, h = divmod(h, 24)  # 分出天和剩余小时
    text = ""  # 累积结果文本
    if d > 0:
        text += f"{int(d)}天 "
    if h > 0:
        text += f"{int(h)}小时 "
    if m > 0:
        text += f"{int(m)}分钟 "
    if d == 0 and h == 0:  # 不到天且不到小时才显示秒
        text += f"{int(s)}秒"
    return text.strip()  # 去除末尾空格