from pydantic import BaseModel
from datetime import datetime
from typing import List


class ActivityLogBase(BaseModel):
    user_id: int
    process_name: str
    window_title: str | None = None
    start_time: datetime
    end_time: datetime
    duration_seconds: int
class ActivityLogCreate(ActivityLogBase):
    pass
class ActivityLog(ActivityLogBase):
    id: int
    # user_id 字段已经从 ActivityLogBase 继承了
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    logs: List[ActivityLog] = [] # 读取一个用户时，也带上他的日志

    class Config:
        orm_mode = True # 在Pydantic V2中应为 from_attributes = True
