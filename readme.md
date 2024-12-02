# DolphinDB Online Feature Experience

## 1 Quick Start

Website: [DolphinDB Online Experience](http://183.134.101.143:11001/)

## 2 Project Structure

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

- `conf/`: Directory for storing configuration files.
- `logs/`: Directory for storing log files.
- `myenv/`: Directory for the virtual environment, used to isolate project dependencies.
- `scripts/`: Directory for storing script files.
- `src/`: Directory for storing source code.
  - `back/`: Backend code directory.
  - `fronted/`: Frontend code directory.

## 3 Configuration Instructions

The configuration file is located at `conf/config.ini`.

```
[container]
cpu_limit = 0.5
memory_limit = 512m
port_range_start = 10000
port_range_end = 11001
cpuset_cpus = 0,2,4,6,8,10,12,14,16,18
image_tag = v2.00.10
```

- `cpu_limit`: Limits the number of CPU cores for each DolphinDB container.
- `memory_limit`: Limits the memory usage for each DolphinDB container.
- `port_range_start` and `port_range_end`: Define the range of ports used by the project.
- `cpuset_cpus`: Restricts containers to specific CPU cores.
- `image_tag`: Specifies the image version tag for DolphinDB. Refer to the [Docker Official Image Repository](https://hub.docker.com/u/dolphindb) for details.

## 4 Design Overview

### 4.1 Server-Side Design

> The server-side code is located at `src/back/server.py`.

**Functionality Overview:**  
This project is a Docker container management service built with FastAPI. It allows users to create and disconnect from DolphinDB Docker containers via API requests, with an automatic mechanism to disconnect and destroy expired containers upon disconnection.

**Dependencies:**

- **FastAPI:** Used to build the Web API framework.
- **Docker:** Utilized to provide isolated computing environments with Docker containers.
- **APScheduler:** Implements scheduled tasks using `BackgroundScheduler` to automatically disconnect expired containers.

**API Description:**

- **Connect to a container**
  - **Endpoint:** `/connect`
  - **Method:** `POST`
  - **Request Body:** None
  - **Response:** `{ "status": "connected", "container_name": "", "port": "" }`
  - **Description:** Allows users to request a connection to a container. The system returns information about the successfully connected container.

- **Disconnect from a container**
  - **Endpoint:** `/disconnect`
  - **Method:** `POST`
  - **Request Body:** `{ "container_name": "dolphindb9001" }`
  - **Response:** `{ "status": "disconnected", "container_name": "" }`
  - **Description:** Users can request to disconnect. The system stops and removes the specified container by its name.

**Scheduled Tasks:**  
A scheduled task using APScheduler checks the list of connected containers every minute to disconnect and remove expired containers.

**Startup and Shutdown:**  
The project uses `uvicorn` to run the FastAPI application. An event handler is registered to close and delete all connected containers upon server shutdown.

### 4.2 Client-Side Design

> The client-side code is located in `src/back`, including `index.html`, `style.css`, and `main.js`. It is a simple static webpage.

**Functionality Overview:**  
The client is a basic web page that allows users to connect to Docker containers through button clicks and access the DolphinDB online experience via an embedded webpage.

**Main Features:**

- **Connect to a container**
  - Clicking the "Connect" button sends a connection request to the server.
  - Upon successful connection, displays connection information and embeds the DolphinDB online experience page.
  - Disables the "Connect" button and enables the "Disconnect" button after a successful connection.

- **Disconnect from a container**
  - Clicking the "Disconnect" button sends a disconnection request to the server.
  - Updates connection information and removes the embedded DolphinDB online experience page upon disconnection.
  - Disables the "Disconnect" button and enables the "Connect" button after disconnection.

- **Automatic Disconnection**
  - When the user attempts to leave the page, the `beforeunload` event triggers an automatic disconnection function.

**Usage Instructions:**

1. Open the `index.html` file.
2. Click the "Connect" button to connect to a Docker container.
3. Access the DolphinDB online experience page after a successful connection.
4. If needed, click the "Disconnect" button to disconnect.

## 5 Notes

1. **Server Startup:**

   ```
   # Navigate to the project's root directory
   ./scripts/back.sh
   ```

2. **Virtual Python Environment:**  
The project uses a virtual Python environment named `myenv`, where all the project's dependencies are installed. To start the backend service, the virtual environment must be activated. The backend startup script **`back.sh`** will automatically activate this virtual environment.  
If you need to deactivate the virtual environment, execute:

```
# deactivate
$ deactivate
```

3. **Server Static Webpage Deployment:**  
The server's static interface is deployed on an Nginx server at port `11001`. The relevant configuration is as follows:

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

## 6 Known Issues

1. In the initial project design, when the user closes the frontend interface, a disconnect request is sent to the backend to stop and delete the corresponding DolphinDB container. However, due to limitations in some browsers (e.g., Chrome), this request may not be sent correctly, causing the container to continue running in the background until it times out (20 minutes after creation), at which point the server automatically recycles it. This issue does not occur in some other browsers, such as Edge.
