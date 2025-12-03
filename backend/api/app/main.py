from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import models, schemas, auth, database

# 初始化数据库表
models.Base.metadata.create_all(bind=database.engine) 

app = FastAPI()

# 核心 API: 智能同步接口 (采用手动事务控制)
@app.post("/sync/sessions/", status_code=status.HTTP_201_CREATED, tags=["Sync"])
def sync_sessions_from_client(
    sessions_data: List[schemas.SyncProcessSession],
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not sessions_data:
        return {"message": "无新数据需要同步。"}
        
    try:
        # --- 不再使用 with db.begin() ---
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
        
        # 5. 所有循环成功结束后，在 try 块的最后，手动提交整个事务
        db.commit()

        return {"message": f"成功同步了 {len(sessions_data)} 个会话。"}

    except Exception as e:
        # 6. 如果 try 块中的任何地方（包括 flush）发生异常，手动回滚所有更改
        db.rollback()
        print(f"同步过程中发生严重错误，事务已回滚: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"同步失败，服务器内部错误: {str(e)}"
        )



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
