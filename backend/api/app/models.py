from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

# 用户模型
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # 关系：一个用户可以拥有多个“被监视的应用”
    watched_applications = relationship("ServerWatchedApplication", back_populates="owner", cascade="all, delete-orphan")

# 层级 1: 被监视的应用 (顶层模型)
class ServerWatchedApplication(Base):
    __tablename__ = 'server_watched_applications'
    id = Column(Integer, primary_key=True)
    executable_name = Column(String(255), nullable=False, index=True)

    # 外键：关联到用户
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 关系：指回它的拥有者
    owner = relationship("User", back_populates="watched_applications")
    # 关系：一个“被监视的应用”对应一个“总账”
    summary = relationship("ServerAppUsageSummary", back_populates="application", uselist=False, cascade="all, delete-orphan")

# 层级 2: 应用使用总账
class ServerAppUsageSummary(Base):
    __tablename__ = 'server_app_usage_summary'
    id = Column(Integer, primary_key=True)
    
    # 外键：关联到被监视的应用
    application_id = Column(Integer, ForeignKey('server_watched_applications.id'), nullable=False, unique=True)
    
    first_seen_at = Column(DateTime, nullable=True)
    last_seen_start_at = Column(DateTime, nullable=True)
    last_seen_end_at = Column(DateTime, nullable=True)
    total_lifetime_seconds = Column(Integer, nullable=False, default=0)
    total_focus_time_seconds = Column(Integer, nullable=False, default=0)
    
    # 关系
    application = relationship("ServerWatchedApplication", back_populates="summary")
    sessions = relationship("ServerProcessSession", back_populates="summary", cascade="all, delete-orphan")

# 层级 3: 进程会话
class ServerProcessSession(Base):
    __tablename__ = 'server_process_sessions'
    id = Column(Integer, primary_key=True)
    
    # 外键：关联到总账
    summary_id = Column(Integer, ForeignKey('server_app_usage_summary.id'), nullable=False, index=True)
    
    process_name = Column(String(255), nullable=False)
    session_start_time = Column(DateTime, nullable=False)
    session_end_time = Column(DateTime, nullable=False)
    total_lifetime_seconds = Column(Integer, nullable=False)
    total_focus_seconds = Column(Integer, nullable=False, default=0)
    
    # 关系
    summary = relationship("ServerAppUsageSummary", back_populates="sessions")
    activities = relationship("ServerFocusActivity", back_populates="session", cascade="all, delete-orphan")

# 层级 4: 焦点活动
class ServerFocusActivity(Base):
    __tablename__ = 'server_focus_activities'
    id = Column(Integer, primary_key=True)
    
    # 外键：关联到会话
    session_id = Column(Integer, ForeignKey('server_process_sessions.id'), nullable=False, index=True)
    
    window_title = Column(String(1024))
    focus_duration_seconds = Column(Integer, nullable=False)
    
    # 关系
    session = relationship("ServerProcessSession", back_populates="activities")
