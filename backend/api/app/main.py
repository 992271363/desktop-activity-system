from pathlib import Path
from typing import List, Optional
from fastapi import Request, FastAPI, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from . import models, schemas, auth, database


models.Base.metadata.create_all(bind=database.engine) 


templates_dir = Path(__file__).parent.joinpath("templates")
templates = Jinja2Templates(directory=templates_dir)

app = FastAPI()

async def get_current_user_from_cookie(request: Request, db: Session = Depends(database.get_db)) -> Optional[models.User]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        user = auth.get_current_user(token=token.split(" ")[1], db=db)
        return user
    except HTTPException:
        return None


#浏览器登录页面
@app.get("/login", response_class=HTMLResponse, tags=["UI Authentication"])
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

#处理浏览器登录表单提交
@app.post("/login", tags=["UI Authentication"])
async def handle_login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    # 验证用户名和密码
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # 如果验证失败，可以重定向回登录页并带上错误提示
        return RedirectResponse("/login?error=1", status_code=status.HTTP_302_FOUND)
    
    # 创建令牌
    access_token = auth.create_access_token(data={"sub": user.username})
    
    # 将令牌设置到 Cookie 中，并重定向到仪表盘
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

#登出
@app.get("/logout", tags=["UI Authentication"])
async def logout_and_redirect():
    response = RedirectResponse(url="/login")
    # 删除 cookie
    response.delete_cookie("access_token")
    return response

#为客户端程序提供获取令牌的 API (与之前教程一致)
@app.post("/auth/token", tags=["API Authentication"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

#用户注册API (与之前教程一致)
@app.post("/auth/register", response_model=schemas.User, tags=["API Authentication"])
def register_user(user_create: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user_create.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    new_user = auth.create_user(db=db, user=user_create)
    return new_user



@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard(
    request: Request, 
    db: Session = Depends(database.get_db),
    # 使用新的 cookie 依赖来获取用户
    current_user: Optional[models.User] = Depends(get_current_user_from_cookie)
):
    """
    保护仪表盘，如果用户未登录 (current_user 为 None)，则重定向到登录页面。
    """
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # 如果已登录，查询该用户的数据并展示
    activities = db.query(models.ActivityLog).filter(models.ActivityLog.user_id == current_user.id).order_by(models.ActivityLog.start_time.desc()).all()
    
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "activities": activities, "user": current_user}
    )


@app.post("/process-data/", response_model=List[schemas.ActivityLog])
def create_activity_log_batch(
    data_batch: List[schemas.ActivityLogCreate],
    db: Session = Depends(database.get_db),
    # 使用标准的 Bearer Token 依赖来保护此接口
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    保护数据上传接口，只有携带有效令牌的客户端才能上传数据。
    上传的数据将自动与当前用户关联。
    """
    created_records = []
    for data_item in data_batch:
        # 在创建记录时，关联当前用户的 ID
        db_item = models.ActivityLog(**data_item.model_dump(), user_id=current_user.id)
        db.add(db_item)
        created_records.append(db_item)
    
    db.commit()
    for record in created_records:
        db.refresh(record)
    return created_records
