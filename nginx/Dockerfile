FROM node:20-alpine AS builder

# 设置工作目录
WORKDIR /app

COPY ../frontend/package*.json ./

# 安装项目依赖
RUN npm install

# 复制前端项目的其余所有源文件
COPY ../frontend/ ./

# 执行构建命令，这会在 /app/dist 目录下生成静态文件
RUN npm run build

FROM nginx:alpine

# 从 "builder" 阶段复制构建好的静态文件到 Nginx 的默认网站根目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 将我们自定义的 nginx.conf 配置文件复制到容器中正确的位置
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露 80 端口
EXPOSE 80

