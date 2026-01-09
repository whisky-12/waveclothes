# WaveClothes 图像生成服务 - 分布式架构

基于 RabbitMQ 的分布式图像生成任务队列服务，采用分层架构设计。

## 架构说明

### 工作流程

1. 用户通过浏览器访问 Client 层的 Web 界面
2. Client 层将任务发送到 RabbitMQ 的任务队列 (`image.generate.task`)
3. Server 层监听任务队列，接收到任务后执行图像生成
4. Server 层将处理结果推送到结果队列 (`image.generate.result`)
5. Client 层从结果队列拉取结果并展示给用户

### 队列说明

- **任务队列** (`image.generate.task`): 存储待处理的图像生成任务
- **结果队列** (`image.generate.result`): 存储已完成的任务结果

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户浏览器                                │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTP
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Client 层 (B机器)                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              FastAPI Web 服务                           │   │
│  │  - REST API 接口                                         │   │
│  │  - 前端页面                                              │   │
│  │  - RabbitMQ 生产者 (发送任务)                           │   │
│  │  - RabbitMQ 消费者 (接收结果)                           │   │
│  └──────────────────┬──────────────────────────────────────┘   │
└─────────────────────┼────────────────────────────────────────────┘
                      │ 发送任务
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              RabbitMQ 服务器                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 任务队列: image.generate.task                           │   │
│  │ 结果队列: image.generate.result                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────┬────────────────────────────────────────────┘
                      │ 消费任务
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Server 层 (A机器)                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           Server 服务管理                                │   │
│  │  - RabbitMQ 消费者 (监听任务队列)                        │   │
│  │  - 图像生成器 (构图任务)                                 │   │
│  │  - RabbitMQ 生产者 (推送结果)                           │   │
│  │  - 服务生命周期管理                                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 各层职责

#### Server 层 (A机器)
- **职责**:
  - 运行 RabbitMQ 消费者，监听任务队列 (`image.generate.task`)
  - 执行图像生成任务（模拟构图生成）
  - 将处理结果推送到结果队列 (`image.generate.result`)
  - 服务启动时自动启动消费者
  - 服务停止时自动断开连接

- **核心组件**:
  - `ServerService`: 服务管理类
  - `RabbitMQConsumer`: RabbitMQ 消费者
  - `ImageGenerator`: 图像生成器

- **启动命令**:
  ```bash
  cd server
  python server_service.py
  ```

#### Client 层 (B机器)
- **职责**:
  - 提供 FastAPI Web 服务
  - 接收用户请求（Web界面/API）
  - 通过服务模块发送任务到不同的构图服务队列
  - 从对应的队列接收处理结果
  - 提供前端交互界面

- **核心组件**:
  - FastAPI 应用
  - **服务模块** (services/)
    - `BaseComposeService`: 服务基类
    - `BasicComposeService`: 基础构图服务
    - `AdvancedComposeService`: 高级构图服务
    - `ServiceFactory`: 服务工厂（统一入口）
  - 前端页面（HTML/CSS/JS）

- **启动命令**:
  ```bash
  cd client
  python main.py
  ```
  或
  ```bash
  cd client
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
  ```

## 项目结构

```
waveclothes/
├── server/                    # Server 层 (部署到A机器)
│   ├── __init__.py
│   ├── config.py             # 配置类
│   ├── generators/            # 生成器模块
│   │   ├── __init__.py
│   │   ├── base_generator.py
│   │   ├── basic_compose_generator.py
│   │   └── advanced_compose_generator.py
│   ├── compose_service.py    # 构图服务管理器
│   ├── rabbitmq_service_consumer.py # 多服务消费者
│   ├── server_service.py     # 服务管理（启动入口）
│   ├── .env                  # 环境配置
│   ├── requirements.txt      # Python 依赖
│   └── test_services.py    # 服务测试脚本
│
├── client/                    # Client 层 (部署到B机器)
│   ├── __init__.py
│   ├── config.py             # 配置类
│   ├── services/             # 服务模块
│   │   ├── __init__.py
│   │   ├── base_service.py
│   │   ├── basic_compose_service.py
│   │   ├── advanced_compose_service.py
│   │   └── service_factory.py
│   ├── main.py               # FastAPI 主应用（启动入口）
│   ├── .env                  # 环境配置
│   ├── requirements.txt      # Python 依赖
│   ├── static/               # 静态文件
│   │   ├── style.css         # 样式文件
│   │   └── script.js         # JavaScript 文件
│   ├── templates/            # 模板文件
│   │   └── index.html        # 前端页面
│   └── test_client_services.py # 客户端服务测试脚本
│
└── README.md                 # 本文档
```

## 部署指南

### 前置要求

1. RabbitMQ 服务器已部署并运行
2. Python 3.8+ 环境
3. 两台服务器（A机器部署Server层，B机器部署Client层）

### Server 层部署 (A机器)

#### 1. 上传代码到A机器

```bash
# 将 server 目录上传到A机器
scp -r server/ user@machine-a:/path/to/waveclothes/
```

#### 2. 安装依赖

```bash
cd /path/to/waveclothes/server
pip install -r requirements.txt
```

#### 3. 配置环境变量

编辑 `.env` 文件，配置 RabbitMQ 连接信息：

```env
RABBITMQ_HOST=122.51.1.189
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/
RABBITMQ_TASK_QUEUE=image.generate.task
RABBITMQ_RESULT_QUEUE=image.generate.result
```

#### 4. 启动服务

```bash
python server_service.py
```

服务启动后会：
- 自动连接到 RabbitMQ
- 创建消费者并监听队列
- 等待处理任务

#### 5. 后台运行（推荐）

使用 systemd 或 supervisor 管理服务：

**systemd 示例** (`/etc/systemd/system/waveclothes-server.service`):

```ini
[Unit]
Description=WaveClothes Server Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/waveclothes/server
ExecStart=/usr/bin/python server_service.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl start waveclothes-server
sudo systemctl enable waveclothes-server
sudo systemctl status waveclothes-server
```

### Client 层部署 (B机器)

#### 1. 上传代码到B机器

```bash
# 将 client 目录上传到B机器
scp -r client/ user@machine-b:/path/to/waveclothes/
```

#### 2. 安装依赖

```bash
cd /path/to/waveclothes/client
pip install -r requirements.txt
```

#### 3. 配置环境变量

编辑 `.env` 文件：

```env
RABBITMQ_HOST=122.51.1.189
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/
RABBITMQ_TASK_QUEUE=image.generate.task
RABBITMQ_RESULT_QUEUE=image.generate.result

APP_HOST=0.0.0.0
APP_PORT=8000
```

#### 4. 启动服务

```bash
python main.py
```

或使用 uvicorn：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 5. 访问服务

打开浏览器访问：`http://machine-b:8000`

#### 6. 后台运行（推荐）

**systemd 示例** (`/etc/systemd/system/waveclothes-client.service`):

```ini
[Unit]
Description=WaveClothes Client Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/waveclothes/client
ExecStart=/usr/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl start waveclothes-client
sudo systemctl enable waveclothes-client
sudo systemctl status waveclothes-client
```

## 使用说明

### 通过 Web 界面使用

1. 打开浏览器访问 Client 层服务地址：`http://machine-b:8000`
2. 填写图像生成参数：
   - **提示词**: 必填，描述要生成的图像内容
   - **宽度**: 可选，默认 512
   - **高度**: 可选，默认 512
   - **风格**: 可选，支持默认、写实、艺术、卡通、抽象
   - **用户ID**: 可选
3. 点击"提交任务"
4. 等待任务处理完成（约 1-5 秒）
5. 查看生成的结果（图像URL、耗时、元数据等）

### 通过 API 使用

#### 提交任务

```bash
POST /api/submit_task
Content-Type: application/json

{
  "prompt": "A beautiful sunset over mountains",
  "width": 512,
  "height": 512,
  "style": "photorealistic",
  "user_id": "user_001"
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "success": true,
    "image_url": "http://image.example.com/generated/task_1234567890_1234.png",
    "task_id": "task_1234567890",
    "duration": 3.45,
    "timestamp": "2025-12-31T10:30:00",
    "metadata": {
      "width": 512,
      "height": 512,
      "style": "photorealistic",
      "prompt": "A beautiful sunset over...",
      "file_size": 234567,
      "generator": "ImageGenerator-v1.0"
    }
  }
}
```

#### API 文档

启动服务后访问 `http://machine-b:8000/docs` 查看完整的 API 文档（Swagger UI）。

## 监控与运维

### RabbitMQ 管理界面

访问：`http://122.51.1.189:15672`

查看：
- 队列状态
- 消息数量
- 消费者连接
- 消息吞吐量

### 日志查看

#### Server 层日志

```bash
# systemd 日志
sudo journalctl -u waveclothes-server -f

# 或查看应用日志
tail -f /var/log/waveclothes/server.log
```

#### Client 层日志

```bash
# systemd 日志
sudo journalctl -u waveclothes-client -f

# 或查看应用日志
tail -f /var/log/waveclothes/client.log
```

### 服务管理

#### Server 层

```bash
# 启动
sudo systemctl start waveclothes-server

# 停止
sudo systemctl stop waveclothes-server

# 重启
sudo systemctl restart waveclothes-server

# 状态
sudo systemctl status waveclothes-server
```

#### Client 层

```bash
# 启动
sudo systemctl start waveclothes-client

# 停止
sudo systemctl stop waveclothes-client

# 重启
sudo systemctl restart waveclothes-client

# 状态
sudo systemctl status waveclothes-client
```

## 故障排查

### Server 层

#### 问题1: 无法连接到 RabbitMQ

**症状**: 日志显示 "连接RabbitMQ失败"

**解决方案**:
1. 检查 `.env` 配置是否正确
2. 确认 RabbitMQ 服务正在运行
3. 检查网络连接和防火墙
4. 测试连接：`telnet 122.51.1.189 5672`

#### 问题2: 队列参数不匹配

**症状**: 日志显示 "PRECONDITION_FAILED"

**解决方案**: 使用被动模式检查队列，代码已处理此问题

### Client 层

#### 问题1: Web 服务无法访问

**症状**: 浏览器无法访问

**解决方案**:
1. 检查服务是否启动
2. 检查端口是否被占用
3. 检查防火墙设置
4. 检查 `APP_HOST` 和 `APP_PORT` 配置

#### 问题2: 提交任务超时

**症状**: 显示"任务处理超时"

**解决方案**:
1. 检查 Server 层是否正常运行
2. 检查 RabbitMQ 队列是否有消息积压
3. 增加超时时间（修改 `TASK_TIMEOUT` 配置）
4. 检查网络延迟

## 扩展说明

### 扩展 Server 层（多消费者）

在同一台机器启动多个 Server 实例，提高处理能力：

```bash
python server_service.py &
python server_service.py &
python server_service.py &
```

或使用 systemd 的多实例配置。

### 扩展 Client 层（负载均衡）

在多台机器部署 Client 层，使用 Nginx 进行负载均衡：

```nginx
upstream waveclothes_backend {
    server machine-b1:8000;
    server machine-b2:8000;
    server machine-b3:8000;
}

server {
    listen 80;
    server_name waveclothes.example.com;

    location / {
        proxy_pass http://waveclothes_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 替换为真实图像生成

修改 `server/image_generator.py` 中的 `generate()` 方法，调用真实的图像生成 API：

```python
def generate(self, params):
    import requests
    
    response = requests.post(
        'https://api.example.com/generate',
        json=params,
        timeout=60
    )
    
    return response.json()
```

## 性能优化建议

1. **增加 Server 层实例**: 根据任务量启动多个消费者
2. **调整 prefetch_count**: 根据任务处理时长调整预取数量
3. **使用连接池**: 优化 RabbitMQ 连接管理
4. **异步处理**: 考虑使用异步框架（如 asyncio）
5. **缓存**: 对频繁请求的结果进行缓存
6. **监控**: 添加 Prometheus 监控指标

## 安全建议

1. 修改默认的 RabbitMQ 用户名和密码
2. 使用 TLS 加密 RabbitMQ 连接
3. 添加 API 认证和限流
4. 配置防火墙规则
5. 定期更新依赖包

## 许可证

MIT License
