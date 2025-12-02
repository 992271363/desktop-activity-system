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
    
@app.post("/sync/sessions/", status_code=status.HTTP_201_CREATED, tags=["Sync"])
def sync_sessions_from_client(
    sessions_data: List[schemas.SyncProcessSession],
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    接收来自客户端的、具有层级结构的会话数据，
    并在服务器端完整地重建这个结构，然后存入数据库。
    """
    total_sessions_created = 0
    total_activities_created = 0
    # 1. 遍历客户端发来的每一个“进程会话”
    for session_dto in sessions_data:
        # 2. 创建一个数据库会话模型 (ServerProcessSession)
        new_db_session = models.ServerProcessSession(
            owner=current_user,  # 直接通过关系关联用户
            process_name=session_dto.process_name,
            session_start_time=session_dto.session_start_time,
            session_end_time=session_dto.session_end_time,
            total_lifetime_seconds=session_dto.total_lifetime_seconds,
        )
        # 3. 遍历该会话下的每一个“焦点活动”
        for activity_dto in session_dto.activities:
            # 4. 创建数据库活动模型 (ServerFocusActivity)
            new_db_activity = models.ServerFocusActivity(
                window_title=activity_dto.window_title,
                focus_duration_seconds=activity_dto.focus_duration_seconds
            )
            # 5. 【核心】将活动添加到会话的 activities 列表中
            # SQLAlchemy 的 ORM 魔术会处理外键关联
            new_db_session.activities.append(new_db_activity)
            total_activities_created += 1
        # 6. 将构建好的、包含所有子活动的完整会话对象添加到数据库会话中
        db.add(new_db_session)
        total_sessions_created += 1
    # 7. 所有数据都处理完毕后，一次性提交事务
    db.commit()
    print(f"用户 '{current_user.username}' (ID: {current_user.id}) 同步完成。")
    print(f"  -> 创建了 {total_sessions_created} 个新会话。")
    print(f"  -> 创建了 {total_activities_created} 个新活动记录。")
    return {
        "message": f"成功接收并存储了 {total_sessions_created} 个会话及其包含的 {total_activities_created} 个活动。"
    }


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
    current_user: Optional[models.User] = Depends(get_current_user_from_cookie)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    # 新的查询：获取当前用户的所有“会话”，并预加载其下的“活动”
    # order_by 对会话的开始时间进行降序排序
    user_sessions = db.query(models.ServerProcessSession)\
                      .filter(models.ServerProcessSession.user_id == current_user.id)\
                      .order_by(models.ServerProcessSession.session_start_time.desc())\
                      .all()
    
    return templates.TemplateResponse(
        "index.html", 
        # 将 user_sessions 传递给模板，而不是旧的 activities
        {"request": request, "sessions": user_sessions, "user": current_user}
    )