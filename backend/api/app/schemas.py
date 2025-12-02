from pydantic import BaseModel
from datetime import datetime


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
        from_attributes = True


class UserBase(BaseModel):
    username: str

class UserCreate(UserBase): 
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True
