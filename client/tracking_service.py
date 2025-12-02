import datetime
from sqlalchemy.orm import Session
from local_models import WatchedApplication, AppUsageSummary, ActivityLog

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
    focus_seconds: int
):
    """
    当一个被监视的进程结束时，调用此函数来记录一切。它会同时更新流水账和总账。
    """
    print(f"[Tracking Service] 正在为 '{executable_name}' 记录一个会话...")
    
    # 1. 查找对应的 AppUsageSummary
    summary = db.query(AppUsageSummary).filter(AppUsageSummary.executable_name == executable_name).first()
    if not summary:
        print(f"[Tracking Service] 错误：找不到 '{executable_name}' 的汇总记录，无法更新！")
        return

    # 2. 计算本次会话的时长
    duration_seconds = int((end_time - start_time).total_seconds())
    if duration_seconds <= 1:
        print(f"[Tracking Service] 会话时长过短 ({duration_seconds}s)，已忽略。")
        return

    # 3. 写入流水 (ActivityLog)
    activity = ActivityLog(
        process_name=executable_name,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=duration_seconds,
        user_id=1 # 默认用户ID
    )
    db.add(activity)
    print(f"[Tracking Service] -> 已创建流水账: {activity}")

    # 4. 更新总账 (AppUsageSummary)
    #   更新累计时长
    summary.total_lifetime_seconds += duration_seconds
    summary.total_focus_time_seconds += focus_seconds
    #   更新首次和最后时间戳
    if not summary.first_seen_at:
        summary.first_seen_at = start_time
    summary.last_seen_start_at = start_time
    summary.last_seen_end_at = end_time
    
    print(f"[Tracking Service] -> 正在更新总账: lifetime +{duration_seconds}s, focus +{focus_seconds}s")
    
    # 5. 提交所有更改
    try:
        db.commit()
        print(f"[Tracking Service] 数据库更新成功！")
    except Exception as e:
        print(f"[Tracking Service] 数据库提交失败: {e}")
        db.rollback()
