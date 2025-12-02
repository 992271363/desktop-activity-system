import datetime
from sqlalchemy.orm import Session
from local_models import (WatchedApplication, AppUsageSummary,
                            ProcessSession, FocusActivity)
def add_or_get_watched_app(db: Session, executable_name: str):
    """
    核心交互逻辑：检查一个应用是否已被监视。
    如果没被监视，则创建新记录；如果已被监视，则直接返回现有记录。
    """
    # 尝试查找已存在的 WatchedApplication
    watched_app = db.query(WatchedApplication).filter(WatchedApplication.executable_name == executable_name).first()

    if not watched_app:
        print(f"[Tracking Service] 新程序: '{executable_name}'，正在添加到监视列表...")
        # 创建新的 WatchedApplication
        new_watched_app = WatchedApplication(executable_name=executable_name)
        # 同时为它创建一个空的 AppUsageSummary
        new_summary = AppUsageSummary(
            executable_name=executable_name,
            total_lifetime_seconds=0,
            total_focus_time_seconds=0,
        )

        new_watched_app.summary = new_summary
        
        db.add(new_watched_app)
        db.commit()
        db.refresh(new_watched_app)
        print(f"[Tracking Service] '{executable_name}' 添加成功。")
        return new_watched_app.summary
    else:
        print(f"[Tracking Service] 已识别程序: '{executable_name}'。")
        # 如果已存在，直接返回其关联的 summary
        return watched_app.summary

def record_process_session(
    db: Session, 
    executable_name: str, 
    start_time: datetime.datetime, 
    end_time: datetime.datetime,
    focus_details: dict  # <-- 参数从 focus_seconds: int 变更为 focus_details: dict
):
    """
    当一个被监视的进程结束时，调用此函数。
    它会创建一条 ProcessSession 记录，并在其下创建多条 FocusActivity 记录，
    最后更新总账 AppUsageSummary。
    """
    print(f"[Tracking Service] 正在为 '{executable_name}' 记录一个新会话...")
    
    # 1. 查找对应的总账 (AppUsageSummary)
    summary = db.query(AppUsageSummary).filter(AppUsageSummary.executable_name == executable_name).first()
    if not summary:
        print(f"[Tracking Service] 错误：找不到 '{executable_name}' 的汇总记录，无法更新！")
        return
    # 2. 计算本次会话的总时长和总焦点时长
    total_lifetime = int((end_time - start_time).total_seconds())
    total_focus_time = sum(focus_details.values()) # 从字典的值中计算总和
    if total_lifetime <= 1:
        print(f"[Tracking Service] 会话时长过短 ({total_lifetime}s)，已忽略。")
        return
    # 3. 创建一条新的“会话”记录 (ProcessSession)
    new_session = ProcessSession(
        summary=summary,  # 通过关系直接关联到总账
        process_name=executable_name,
        session_start_time=start_time,
        session_end_time=end_time,
        total_lifetime_seconds=total_lifetime,
        total_focus_seconds=total_focus_time
    )
    db.add(new_session)
    print(f"[Tracking Service] -> 已创建会话记录: {start_time.strftime('%H:%M:%S')} - {end_time.strftime('%H:%M:%S')}")
    # 4. 在“会话”下为每个窗口标题创建“焦点活动”记录 (FocusActivity)
    if not focus_details:
        print("[Tracking Service] -> 该会话没有检测到焦点活动。")
    else:
        print(f"[Tracking Service] -> 该会话检测到 {len(focus_details)} 个窗口标题活动...")
        for title, focus_seconds in focus_details.items():
            if focus_seconds > 0:
                activity = FocusActivity(
                    session=new_session,  # 通过关系关联到刚刚创建的会话
                    window_title=title,
                    focus_duration_seconds=focus_seconds
                )
                db.add(activity)
                print(f"[Tracking Service]     - 焦点活动: '{title}' ({focus_seconds}s)")
    # 5. 更新总账 (AppUsageSummary)
    summary.total_lifetime_seconds += total_lifetime
    summary.total_focus_time_seconds += total_focus_time
    if not summary.first_seen_at:
        summary.first_seen_at = start_time
    summary.last_seen_start_at = start_time
    summary.last_seen_end_at = end_time
    
    print(f"[Tracking Service] -> 正在更新总账: lifetime +{total_lifetime}s, focus +{total_focus_time}s")
    
    # 6. 提交所有更改
    try:
        db.commit()
        print(f"[Tracking Service] 数据库更新成功！")
    except Exception as e:
        print(f"[Tracking Service] 数据库提交失败: {e}")
        db.rollback()