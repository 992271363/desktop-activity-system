from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas 
from database import SessionLocal, engine


models.Base.metadata.create_all(bind=engine) 

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/process-data/", response_model=List[schemas.ActivityLog])
def create_activity_log_batch(
    data_batch: List[schemas.ActivityLogCreate],
    db: Session = Depends(get_db)
):
    """
    接收一个包含多条活动日志的列表，并将它们批量存入数据库。
    """
    created_records = []
    for data_item in data_batch:
        # 使用正确的 models.ActivityLog，并从 data_item 解包
        db_item = models.ActivityLog(**data_item.model_dump()) 
        db.add(db_item)
        created_records.append(db_item)
    
    db.commit() # 一次性提交所有数据
    for record in created_records:
        db.refresh(record)
    return created_records