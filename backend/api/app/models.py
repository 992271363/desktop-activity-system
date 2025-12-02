from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # 关系：一个用户可以有多个“进程会话”
    sessions = relationship("ServerProcessSession", back_populates="owner", cascade="all, delete-orphan")
class ServerProcessSession(Base):
    """
    服务器端的“进程会话”模型，对应客户端的 ProcessSession。
    """
    __tablename__ = "server_process_sessions" # 新表名
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 外键：关联到用户
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 会话的宏观数据
    process_name = Column(String(255), nullable=False, index=True)
    session_start_time = Column(DateTime, nullable=False)
    session_end_time = Column(DateTime, nullable=False)
    total_lifetime_seconds = Column(Integer, nullable=False)
    
    # 关系：一个会话可以有多个“焦点活动”
    owner = relationship("User", back_populates="sessions")
    activities = relationship("ServerFocusActivity", back_populates="session", cascade="all, delete-orphan")
class ServerFocusActivity(Base):
    """
    服务器端的“焦点活动”模型，对应客户端的 FocusActivity。
    """
    __tablename__ = "server_focus_activities" # 新表名
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 外键：关联到某一次“会话”
    session_id = Column(Integer, ForeignKey("server_process_sessions.id"), nullable=False)
    
    # 活动的微观数据
    window_title = Column(Text) # 使用 Text 类型以支持更长的窗口标题
    focus_duration_seconds = Column(Integer, nullable=False)
    
    # 关系：指回它的父会话
    session = relationship("ServerProcessSession", back_populates="activities")