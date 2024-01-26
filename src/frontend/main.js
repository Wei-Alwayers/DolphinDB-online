var isConnected = false;
var currentContainerName = "";

function connect() {
    if (!isConnected) {
        // 发送连接请求
        fetch("http://183.134.101.143:8000/connect", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({}),
        })
            .then(response => response.json())
            .then(data => {
                // 更新右侧显示连接信息的区域
                document.getElementById("containerInfo").innerHTML = `
                        <Container>Status: Connected ${data.container_name}</p>
                    `;

                // 更新按钮状态
                document.getElementById("connectBtn").disabled = true;
                document.getElementById("disconnectBtn").disabled = false;

                isConnected = true;
                currentContainerName = data.container_name;

                // 延时2秒后嵌入连接后的网页
                setTimeout(() => {
                    embedBrowser(`http://183.134.101.143:${data.port}`);
                }, 2000);

                // 弹出欢迎提示
                alert("欢迎连接 DolphinDB 连接将在20分钟后自动断开");
            })
            .catch(error => console.error("连接时发生错误:", error));
    } else {
        alert("已连接到容器，不能创建新的连接。");
    }
}

function disconnect() {
    if (isConnected) {
        // 发送断开连接请求
        fetch("http://183.134.101.143:8000/disconnect", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ container_name: currentContainerName }),
        })
            .then(response => response.json())
            .then(data => {
                // 更新右侧显示连接信息的区域
                document.getElementById("containerInfo").innerHTML = `
                        <Container>Status: Disconnected</p>
                    `;

                // 更新按钮状态
                document.getElementById("connectBtn").disabled = false;
                document.getElementById("disconnectBtn").disabled = true;

                isConnected = false;
                currentContainerName = "";

                // 移除嵌入的网页
                removeEmbeddedBrowser();
            })
            .catch(error => console.error("断开连接时发生错误:", error));
    } else {
        alert("未连接到容器，不能断开连接。");
    }
}

function embedBrowser(url) {
    // 创建 iframe 元素
    var iframe = document.createElement("iframe");
    iframe.src = url;
    iframe.width = "100%";
    iframe.height = "100%";
    iframe.frameBorder = "0";
    // 将 iframe 插入到指定容器中
    document.getElementById("embeddedBrowser").appendChild(iframe);
}

function removeEmbeddedBrowser() {
    // 移除嵌入的网页（清空容器内容）
    document.getElementById("embeddedBrowser").innerHTML = "";
}

// 在用户即将离开页面时触发断开连接
window.addEventListener('beforeunload', function (event) {
    if (isConnected) {
        disconnect();
    }
});