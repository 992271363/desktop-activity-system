# main.py (完整替换版)

from pathlib import Path
from typing import List, Optional
from fastapi import Request, FastAPI, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from . import models, schemas, auth, database

# 初始化数据库表 (SQLAlchemy 会创建所有新模型对应的表)
models.Base.metadata.create_all(bind=database.engine) 

# FastAPI 实例和模板配置
templates_dir = Path(__file__).parent.joinpath("templates")
templates = Jinja2Templates(directory=templates_dir)
app = FastAPI()

# 核心 API: 智能同步接口
@app.post("/sync/sessions/", status_code=status.HTTP_201_CREATED, tags=["Sync"])
def sync_sessions_from_client(
    sessions_data: List[schemas.SyncProcessSession],
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    接收来自客户端的会话数据，并智能地更新服务端的四层模型结构。
    这是一个事务性操作。
    """
    if not sessions_data:
        return {"message": "无新数据需要同步。"}
        
    try:
        # 开始一个数据库事务，确保所有操作要么全部成功，要么全部失败
        with db.begin():
            for session_dto in sessions_data:
                # 1. 查找或创建 WatchedApplication
                watched_app = db.query(models.ServerWatchedApplication).filter_by(
                    user_id=current_user.id, 
                    executable_name=session_dto.process_name
                ).first()

                if not watched_app:
                    watched_app = models.ServerWatchedApplication(
                        owner=current_user,
                        executable_name=session_dto.process_name
                    )
                    db.add(watched_app)
                    db.flush()

                # 2. 锁定并更新或创建 AppUsageSummary
                summary = db.query(models.ServerAppUsageSummary).filter_by(
                    application_id=watched_app.id
                ).with_for_update().first()

                current_session_focus_seconds = sum(act.focus_duration_seconds for act in session_dto.activities)

                if not summary:
                    summary = models.ServerAppUsageSummary(
                        application=watched_app,
                        first_seen_at=session_dto.session_start_time,
                        last_seen_start_at=session_dto.session_start_time,
                        last_seen_end_at=session_dto.session_end_time,
                        total_lifetime_seconds=session_dto.total_lifetime_seconds,
                        total_focus_time_seconds=current_session_focus_seconds
                    )
                    db.add(summary)
                else:
                    summary.total_lifetime_seconds += session_dto.total_lifetime_seconds
                    summary.total_focus_time_seconds += current_session_focus_seconds
                    summary.last_seen_start_at = session_dto.session_start_time
                    summary.last_seen_end_at = session_dto.session_end_time
                    if not summary.first_seen_at or summary.first_seen_at > session_dto.session_start_time:
                        summary.first_seen_at = session_dto.session_start_time
                
                db.flush()

                # 3. 创建 ProcessSession
                new_session = models.ServerProcessSession(
                    summary_id=summary.id,
                    process_name=session_dto.process_name,
                    session_start_time=session_dto.session_start_time,
                    session_end_time=session_dto.session_end_time,
                    total_lifetime_seconds=session_dto.total_lifetime_seconds,
                    total_focus_seconds=current_session_focus_seconds
                )
                db.add(new_session)
                db.flush()

                # 4. 批量创建 FocusActivities
                activities_to_add = []
                for activity_data in session_dto.activities:
                    activities_to_add.append(
                        models.ServerFocusActivity(
                            session_id=new_session.id,
                            window_title=activity_data.window_title,
                            focus_duration_seconds=activity_data.focus_duration_seconds
                        )
                    )
                if activities_to_add:
                    db.add_all(activities_to_add)

        return {"message": f"成功同步了 {len(sessions_data)} 个会话。"}

    except Exception as e:
        db.rollback()
        print(f"同步过程中发生严重错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"同步失败: {str(e)}"
        )

# 从 Cookie 中获取用户
async def get_current_user_from_cookie(request: Request, db: Session = Depends(database.get_db)) -> Optional[models.User]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        user = auth.get_current_user(token=token.split(" ")[1], db=db)
        return user
    except HTTPException:
        return None

# 浏览器登录页面
@app.get("/login", response_class=HTMLResponse, tags=["UI Authentication"])
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 处理浏览器登录表单提交
@app.post("/login", tags=["UI Authentication"])
async def handle_login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        return RedirectResponse("/login?error=1", status_code=status.HTTP_302_FOUND)
    
    access_token = auth.create_access_token(data={"sub": user.username})
    
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

# 登出
@app.get("/logout", tags=["UI Authentication"])
async def logout_and_redirect():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response

# 为客户端程序提供获取令牌的 API
@app.post("/auth/token", response_model=dict, tags=["API Authentication"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# 用户注册API
@app.post("/auth/register", response_model=schemas.User, tags=["API Authentication"])
def register_user(user_create: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user_create.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    new_user = auth.create_user(db=db, user=user_create)
    return new_user

# 仪表盘页面
@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def get_dashboard(
    request: Request,
    db: Session = Depends(database.get_db),
    current_user: Optional[models.User] = Depends(get_current_user_from_cookie)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # 新的查询逻辑：获取当前用户的“总账”记录
    summaries = db.query(models.ServerAppUsageSummary)\
                  .join(models.ServerWatchedApplication)\
                  .filter(models.ServerWatchedApplication.user_id == current_user.id)\
                  .order_by(models.ServerAppUsageSummary.total_focus_time_seconds.desc())\
                  .all()
    
    # 顺便获取最近的会话记录
    recent_sessions = db.query(models.ServerProcessSession)\
                       .join(models.ServerAppUsageSummary)\
                       .join(models.ServerWatchedApplication)\
                       .filter(models.ServerWatchedApplication.user_id == current_user.id)\
                       .order_by(models.ServerProcessSession.session_start_time.desc())\
                       .limit(20).all()

    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "user": current_user,
            "summaries": summaries,
            "recent_sessions": recent_sessions
        }
    )
