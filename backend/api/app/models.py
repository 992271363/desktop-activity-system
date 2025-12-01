# models.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    # 可以在这里添加 email, created_at 等字段

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    process_name = Column(String(255), nullable=False, index=True)
    window_title = Column(Text)
    
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    
    # 建立与 User 的关系
    user = relationship("User", back_populates="logs")

User.logs = relationship("ActivityLog", order_by=ActivityLog.id, back_populates="user")
