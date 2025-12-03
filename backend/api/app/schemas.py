from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional



# 客户端发来的每个焦点活动的数据
class SyncFocusActivity(BaseModel):
    window_title: str
    focus_duration_seconds: int

# 客户端发来的每个会话的数据包
class SyncProcessSession(BaseModel):
    process_name: str
    session_start_time: datetime
    session_end_time: datetime
    total_lifetime_seconds: int
    activities: List[SyncFocusActivity]

# 用于 API 输出和内部使用的模型

# 用户相关的模型
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase): 
    password: str

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

# 用于未来仪表盘显示的总账数据模型
class AppUsageSummary(BaseModel):
    id: int
    first_seen_at: Optional[datetime]
    last_seen_start_at: Optional[datetime]
    last_seen_end_at: Optional[datetime]
    total_lifetime_seconds: int
    total_focus_time_seconds: int
    
    class Config:
        from_attributes = True
