from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
Base = declarative_base()
class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, default=0)
    process_name = Column(String, nullable=False)
    window_title = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer, nullable=False)

    synced = Column(Boolean, default=False, nullable=False)
    def __repr__(self):
        return (f"<ActivityLog(id={self.id}, process='{self.process_name}', "
                f"duration={self.duration_seconds}s, synced={self.synced})>") 

# 存储用户选择要自动监视的exe
class WatchedApplication(Base):

    __tablename__ = 'watched_applications'
    id = Column(Integer, primary_key=True)
    executable_name = Column(String, nullable=False, unique=True)
    summary = relationship("AppUsageSummary", back_populates="application", uselist=False, cascade="all, delete-orphan")
    def __repr__(self):
        return f"<WatchedApplication(exe='{self.executable_name}')>"

# 用于存储每个被监视的可执行文件的累计使用情况。
class AppUsageSummary(Base):
    __tablename__ = 'app_usage_summary'
    id = Column(Integer, primary_key=True)
    # 使用外键关联到被监视的程序
    executable_name = Column(String, ForeignKey('watched_applications.executable_name'), nullable=False, unique=True)
    # 第一次启动时间
    first_seen_at = Column(DateTime, nullable=True)
    # 最后一次启动时间
    last_seen_start_at = Column(DateTime, nullable=True)
    # 最后一次停止时间
    last_seen_end_at = Column(DateTime, nullable=True)
    # 累计的总存活时长（秒）
    total_lifetime_seconds = Column(Integer, nullable=False, default=0)
    # 累计的总焦点时长（秒）
    total_focus_time_seconds = Column(Integer, nullable=False, default=0)
    # 建立关系
    application = relationship("WatchedApplication", back_populates="summary")
    def __repr__(self):
        return (f"<AppUsageSummary(exe='{self.executable_name}', "
                f"lifetime={self.total_lifetime_seconds}s, focus={self.total_focus_time_seconds}s)>")