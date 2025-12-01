#导入fastapi库
from fastapi import FastAPI

#创建一个FastAPI实例
app = FastAPI()

#定义一个根路由
@app.get("/")
def read_root():
    return {"message": "Hello, World! "}