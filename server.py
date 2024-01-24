import datetime
import time
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import random
import subprocess
import webbrowser
import configparser
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()

# 读取配置文件
config = configparser.ConfigParser()
config.read("config.ini")

# 从配置文件中获取值
cpu_limit = config.getfloat("container", "cpu_limit")
memory_limit = config.get("container", "memory_limit")
port_range_start = config.getint("container", "port_range_start")
port_range_end = config.getint("container", "port_range_end")
cpuset_cpus = config.get("container", "cpuset_cpus")

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源访问，生产环境中建议更加限制
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

# 保存当前连接的容器信息
connected_containers = []


# 创建新容器请求的数据模型
class ConnectRequest(BaseModel):
    pass


# 断开连接请求的数据模型
class DisconnectRequest(BaseModel):
    container_name: str


# 创建新容器
def create_new_container():
    while True:
        random_port = random.randint(port_range_start, port_range_end)
        if random_port not in [container["port"] for container in connected_containers]:
            break

    new_container_name = f"dolphindb{random_port}"
    new_host_name = f"host{random_port}"

    # 添加资源限制
    subprocess.run(
        [
            "docker",
            "run",
            "-itd",
            "--name",
            new_container_name,
            "--hostname",
            new_host_name,
            "-p",
            f"{random_port}:8848",
            "-v",
            "/etc:/dolphindb/etc",
            "--cpus",
            str(cpu_limit),  # 使用配置中的cpu_limit值
            "--memory",
            memory_limit,  # 使用配置中的memory_limit值
            "--cpuset-cpus",
            str(cpuset_cpus),  # 使用配置中的cpuset_cpus值
            "dolphindb/dolphindb:v2.00.10",
            "sh",
        ]
    )
    start_time = time.time()
    connected_containers.append(
        {
            "name": new_container_name,
            "port": random_port,
            "start_time": start_time,
        }
    )
    print(f"new_container_name: {new_container_name}")
    print(f"random_port: {random_port}")
    print(f"Current Time: {start_time}")
    return new_container_name, random_port


# 断开过期容器
def disconnect_expired_containers():
    expiration_time = 20 * 60  # 20 minute in seconds
    # print("Checking for expired containers")

    current_time = time.time()

    for container in connected_containers[:]:
        start_time = container.get("start_time", current_time)

        if current_time - start_time > expiration_time:
            container_name = container["name"]
            print(f"自动断开连接容器 {container_name}")
            print(f"Current Time: {current_time}")
            connected_containers.remove(container)
            subprocess.run(["docker", "stop", container_name])
            subprocess.run(["docker", "rm", container_name])


# 定时任务调度器
scheduler = BackgroundScheduler()
scheduler.add_job(disconnect_expired_containers, "interval", minutes=1)
scheduler.start()


# 用户连接
@app.post("/connect")
def connect_to_container(request: ConnectRequest):
    new_container_name, random_port = create_new_container()
    print(f"Connected to new container {new_container_name} on port {random_port}")

    # 返回连接信息
    return {
        "status": "connected",
        "container_name": new_container_name,
        "port": random_port,
    }


# 用户断开连接
@app.post("/disconnect")
def disconnect_from_container(request: DisconnectRequest):
    container_name = request.container_name
    print(f"Trying to disconnect from container {container_name}")
    print(f"Connected containers: {connected_containers}")

    container_index = None
    for i, container in enumerate(connected_containers):
        if container["name"] == container_name:
            container_index = i
            break

    if container_index is not None:
        container = connected_containers.pop(container_index)
        subprocess.run(["docker", "stop", container["name"]])
        subprocess.run(["docker", "rm", container["name"]])
        print(f"Disconnected from container {container['name']}")
        return {"status": "disconnected", "container_name": container_name}
    else:
        print(f"Container {container_name} not found in connected containers.")
        # 返回错误信息
        raise HTTPException(
            status_code=404, detail=f"Container {container_name} not found"
        )


# 在服务器关闭时关闭和删除所有容器
def shutdown_event():
    for container in connected_containers:
        subprocess.run(["docker", "stop", container["name"]])
        subprocess.run(["docker", "rm", container["name"]])
    print("All containers stopped and removed")


app.add_event_handler("shutdown", shutdown_event)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
