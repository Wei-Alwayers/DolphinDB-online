from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import random
import subprocess
import time
import webbrowser

app = FastAPI()

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源访问，生产环境中建议更加限制
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

# 保存当前连接的容器信息
# TO DO：限制最大连接
connected_containers = []


# 创建新容器请求的数据模型
class ConnectRequest(BaseModel):
    # 可以根据需要添加其他请求参数
    pass


# 断开连接请求的数据模型
class DisconnectRequest(BaseModel):
    container_name: str


# 创建新容器
def create_new_container():
    while True:
        random_port = random.randint(9000, 9999)
        if random_port not in [container["port"] for container in connected_containers]:
            break

    new_container_name = f"dolphindb{random_port}"
    new_host_name = f"host{random_port}"

    # 添加资源限制
    # TO DO:：限制其他资源
    cpu_limit = "0.5"  # 限制使用的 CPU 核心数为 0.5
    memory_limit = "512m"  # 限制使用的内存量为 512MB

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
            cpu_limit,
            "--memory",
            memory_limit,
            "dolphindb/dolphindb:v2.00.10",
            "sh",
        ]
    )
    connected_containers.append({"name": new_container_name, "port": random_port})
    print(f" new_container_name: { new_container_name}")
    print(f"random_port: {random_port}")
    return new_container_name, random_port


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
