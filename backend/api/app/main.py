from fastapi import Request
from fastapi import FastAPI, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas 
from .database import SessionLocal, engine


models.Base.metadata.create_all(bind=engine) 

templates = Jinja2Templates(directory="templates")

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard(request: Request, db: Session = Depends(get_db)):
    """
    这个函数将作为仪表盘的主页。
    它会从数据库查询数据，然后渲染一个HTML页面来展示它们。
    """

    activities = db.query(models.ActivityLog).order_by(models.ActivityLog.start_time.desc()).all()
    
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "activities": activities}
    )


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