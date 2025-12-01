from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas
from .database import engine, get_db


#    这行代码是关键：它会找到 models.py 中所有继承了 Base 的类，
#    并根据它们的定义，在数据库中创建相应的表。
#    这只会在表不存在时执行，所以可以安全地在每次启动时调用。
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    读取用户列表。
    """
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    创建一个新用户。
    注意：这里只是一个简单示例，没有处理密码哈希等安全问题。
    """
    # 实际项目中，你需要先哈希密码再存储
    # fake_hashed_password = user.password + "notreallyhashed" 
    db_user = models.User(username=user.username, hashed_password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/logs/", response_model=List[schemas.ActivityLog])
def read_activity_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    读取活动日志列表。
    """
    logs = db.query(models.ActivityLog).offset(skip).limit(limit).all()
    return logs
