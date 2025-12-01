#Python3.11新版基础镜像
FROM python:3.11.14-trixie

#容器内的工作目录
WORKDIR /app

#复制依赖文件
COPY requirements.txt .

#安装项目所需依赖
RUN pip install --no-cache-dir -r requirements.txt

#把./app的东西复制到容器/app
COPY ./app .

#端口声明
EXPOSE 80

#启动
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
