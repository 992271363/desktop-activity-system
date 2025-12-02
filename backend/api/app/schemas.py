from pydantic import BaseModel
from datetime import datetime
from typing import List


class SyncFocusActivity(BaseModel):
    window_title: str
    focus_duration_seconds: int
class SyncProcessSession(BaseModel):
    process_name: str
    session_start_time: datetime
    session_end_time: datetime
    total_lifetime_seconds: int
    activities: List[SyncFocusActivity]

class ServerFocusActivity(BaseModel):
    id: int
    window_title: str
    focus_duration_seconds: int
    class Config:
        from_attributes = True
class ServerProcessSession(BaseModel):
    id: int
    process_name: str
    session_start_time: datetime
    session_end_time: datetime
    total_lifetime_seconds: int
    activities: List[ServerFocusActivity] = [] # 包含其下的所有活动
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    username: str

class UserCreate(UserBase): 
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True
