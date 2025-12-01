 # app/schemas.py

from pydantic import BaseModel
from datetime import datetime
from typing import List

# --- ActivityLog Schemas ---
class ActivityLogBase(BaseModel):
    process_name: str
    window_title: str | None = None
    start_time: datetime
    end_time: datetime
    duration_seconds: int

class ActivityLogCreate(ActivityLogBase):
    pass

class ActivityLog(ActivityLogBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True # 在Pydantic V2中应为 from_attributes = True

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    logs: List[ActivityLog] = [] # 读取一个用户时，也带上他的日志

    class Config:
        orm_mode = True # 在Pydantic V2中应为 from_attributes = True
