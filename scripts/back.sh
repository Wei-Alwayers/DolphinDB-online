#!/bin/bash

# 进入项目目录
cd /home/ecology/DolphinDB-ol

# 激活虚拟环境
source myenv/bin/activate

# 进入后端目录
cd src/back

# 启动后端服务
nohup uvicorn server:app --host 0.0.0.0 --port 8000 --reload > /home/ecology/DolphinDB-ol/logs/app.log 2>&1 &

