import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from local_models import Base

basedir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(basedir, "data")
os.makedirs(data_dir, exist_ok=True)
db_path = os.path.join(data_dir, "local_client.db")

# DATABASE_URL 格式 (SQLite)
DATABASE_URL = f"sqlite:///{db_path}"
# 创建数据库引擎
# connect_args 是 SQLite 多线程使用的重要参数
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

#创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#创建数据库表
def create_db_and_tables():
    """
    在应用首次启动时调用，用于创建数据库文件和所有表。
    """
    Base.metadata.create_all(bind=engine)

