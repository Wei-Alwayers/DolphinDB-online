# DolphinDB在线功能体验

## 1 快速开始

网页地址：[DolphinDB在线体验](http://183.134.101.143:11001/)

## 2 项目结构

```
/DolphinDB-ol
├── conf
│   └── config.ini
├── logs
│   └── app.log
├── myenv  
├── scripts
│   └── back.sh
└── src
    ├── back
    │   └── server.py
    └── fronted
        ├── index.html
        ├── styles.css
        └── scripts.js
```

- conf/： 存放配置文件的目录。
- logs/： 存放日志文件的目录。
- myenv/： 存放虚拟环境的目录，用于隔离项目的依赖。
- scripts/： 存放脚本文件的目录。
- src/： 存放源代码的目录。
  - back/： 后端代码目录。
  - fronted/： 前端代码目录。

## 3 配置说明

配置文件位于conf/config.ini

```
[container]
cpu_limit = 0.5
memory_limit = 512m
port_range_start = 10000
port_range_end = 11001
cpuset_cpus = 0,2,4,6,8,10,12,14,16,18
image_tag = v2.00.10
```

- cpu_limit：每个DolphinDB容器限制CPU核数
- memory_limit：每个DolphinDB容器限制
- port_range_start port_range_end：项目使用的端口范围
- cpuset_cpus：限制容器使用的特定 CPU 核心。
- image_tag：DolphinDB使用的镜像版本标签，可参考[Docker 官方镜像仓库](https://hub.docker.com/u/dolphindb)

## 4 设计说明

### 4.1 服务端设计

> 服务端代码位于src/back/server.py

**功能概述：**该项目是一个基于 FastAPI 的 Docker 容器管理服务。它允许用户通过 API 请求创建和断开连接到DolphinDB的Docker 容器，同时实现了自动断开过期容器的功能。容器断开时自动终止并销毁容器。

**依赖组件：**

- FastAPI： 使用 FastAPI 框架构建 Web API。
- Docker： 利用 Docker 容器来提供可隔离的计算环境。
- APScheduler**：** 使用 BackgroundScheduler 实现定时任务，自动断开过期容器。

**API说明：**

- 连接到容器
  - Endpoint： /connect
  - Method： POST
  - 请求体： 无
  - 响应：{ "status": "connected", "container_name": "", "port":  ""}
  - 说明： 用户请求连接到容器，系统返回成功连接的容器信息。
- 断开连接
  - Endpoint： /disconnect
  - Method： POST
  - 请求体：{ "container_name": "dolphindb9001" }
  - 响应：{ "status": "disconnected", "container_name": "" }
  - 说明： 用户请求断开连接，系统根据容器名断开连接并停止删除容器。

**定时任务：**使用 APScheduler 实现了一个定时任务，每分钟检查连接的容器列表，断开并移除过期容器。

**启动和关闭：**项目使用 uvicorn 来运行 FastAPI 应用。在服务器关闭时，注册了一个事件处理程序，会关闭并删除所有连接的容器。

### 4.2 客户端设计

> 客户端代码位于src/back，包括index.html style.css main.js，为简单静态页面

**功能概述：**客户端是一个简单的 Web 页面，允许用户通过按钮点击连接到 Docker 容器并在嵌入的网页中进行 DolphinDB 的在线体验。

**主要功能：**

- 连接到容器
  - 点击 "Connect" 按钮将向服务器发送连接请求。
  - 成功连接后，显示连接信息和嵌入 DolphinDB 在线体验页面。
  - 连接成功后，禁用 "Connect" 按钮并启用 "Disconnect" 按钮。
- 断开连接
  - 点击 "Disconnect" 按钮将向服务器发送断开连接请求。
  - 成功断开连接后，更新连接信息和移除嵌入的 DolphinDB 在线体验页面。
  - 断开连接后，禁用 "Disconnect" 按钮并启用 "Connect" 按钮。
- 自动断开
  - 当用户即将离开页面时，会触发 beforeunload 事件，此时系统会自动调用断开连接函数。

**使用方法：**

1. 打开 index.html 文件。
2. 点击 "Connect" 按钮连接到 Docker 容器。
3. 在连接成功后，嵌入 DolphinDB 在线体验页面。
4. 如果需要断开连接，点击 "Disconnect" 按钮。

## 5 注意事项

1. **服务端启动：**

   ```
   # 进入项目目录
   ./scripts/back.sh
   ```

2. **虚拟的python环境：**项目使用到虚拟的python环境myenv，项目依赖的包安装在该虚拟环境中，启动后端服务需要在该环境下。后端启动脚本**back.sh**会自动激活该虚拟环境。如果需要退出虚拟环境，执行

```
# 退出虚拟环境
$ deactivate
```

3. **服务端静态网页部署：**服务端静态界面部署在nginx服务器11001端口上，相关配置如下：

```
# nginx.conf
server {
        listen       11001;
        server_name  183.134.101.143;

        location / {
            root   /home/ecology/DolphinDB-ol/src/frontend;
            index  index.html;
        }
}
```

## 6 已知问题

1. 在项目最初设计中，用户关闭前端界面，将会给后端发送断开连接请求，停止并删除对应DolphinDB容器。但是由于某些浏览器限制（如chrome），该请求不能正确发送，这将会导致容器在后台一直运行，直到超时（创建20分钟后），服务端将其自动回收。在一些其他浏览器，如edge，则不存在这类问题。