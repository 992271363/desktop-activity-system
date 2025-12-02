from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
Base = declarative_base()

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
    sessions = relationship("ProcessSession", back_populates="summary", cascade="all, delete-orphan")
    def __repr__(self):
        return (f"<AppUsageSummary(exe='{self.executable_name}', "
                f"lifetime={self.total_lifetime_seconds}s, focus={self.total_focus_time_seconds}s)>")

# 存储每个被监视的可执行文件的每个会话的详细信息。
class ProcessSession(Base):
    __tablename__ = 'process_sessions'
    id = Column(Integer, primary_key=True)
    
    # 外键，关联到总账
    summary_id = Column(Integer, ForeignKey('app_usage_summary.id'), nullable=False)
    
    # 本次会话的宏观数据
    process_name = Column(String, nullable=False)
    session_start_time = Column(DateTime, nullable=False)
    session_end_time = Column(DateTime, nullable=False)
    total_lifetime_seconds = Column(Integer, nullable=False)
    
    # 累计的总焦点时长（秒）
    total_focus_seconds = Column(Integer, nullable=False, default=0)
    # 建立关系
    summary = relationship("AppUsageSummary", back_populates="sessions")
    activities = relationship("FocusActivity", back_populates="session", cascade="all, delete-orphan")

# 存储每个被监视的可执行文件的每个会话的微观数据。
class FocusActivity(Base):
    __tablename__ = 'focus_activities'
    id = Column(Integer, primary_key=True)
    
    # 外键，关联到某一次“会话”
    session_id = Column(Integer, ForeignKey('process_sessions.id'), nullable=False)
    
    # 本次活动的微观数据
    window_title = Column(String, nullable=False)
    focus_duration_seconds = Column(Integer, nullable=False)
    
    synced = Column(Boolean, default=False, nullable=False) # 同步标记仍然需要
    
    # 建立关系
    session = relationship("ProcessSession", back_populates="activities")
