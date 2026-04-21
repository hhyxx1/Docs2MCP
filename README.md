# Docs2MCP - AI开发文档助手

## 项目概述

Docs2MCP 是一个帮助AI开发者的工具，通过爬取官方文档并将其转换为MCP服务器，使AI能够在编写代码时实时查询官方文档，避免使用过时或弃用的API。

## 架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Flutter App   │────▶│   MCP Server    │────▶│   Official Docs  │
│   (管理界面)     │     │   (后端服务)     │     │   (华为/Flutter)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   IDE AI        │
                        │   (Trae/VSCode) │
                        └─────────────────┘
```

## 快速开始

### 1. 服务器配置

默认配置:
- 本地开发: `http://localhost:5000`
- 生产部署: 使用你自己的服务器地址

详细部署步骤请参考 [3. 服务器部署](#3-服务器部署) 部分。

### 2. API端点

- `GET /api/server/status` - 服务器状态
- `GET /api/docs/list` - 文档列表
- `POST /api/docs/add` - 添加文档
- `POST /api/docs/remove` - 移除文档
- `GET /api/ide/query?q=<search>` - AI查询接口
- `GET /mcp/info` - MCP信息

### 3. 服务器部署

#### 环境要求
- Python 3.7+
- pip 3.0+

#### 部署步骤

1. **安装依赖**
   ```bash
   cd mcp-server
   pip install -r requirements.txt
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 根据需要修改 .env 文件中的配置
   ```

3. **启动服务**
   ```bash
   cd src
   python app.py
   ```

4. **后台运行（可选）**
   ```bash
   # 使用 nohup 在后台运行
   nohup python app.py > server.log 2>&1 &
   ```

5. **防火墙配置**
   ```bash
   # 开放 5000 端口
   sudo ufw allow 5000/tcp  # Ubuntu/Debian
   # 或
   sudo firewall-cmd --add-port=5000/tcp --permanent  # CentOS/RHEL
   sudo firewall-cmd --reload
   ```

### 4. 添加华为文档示例

```bash
# 替换为你自己的服务器地址
curl -X POST http://localhost:5000/api/docs/add \
  -H "Content-Type: application/json" \
  -d '{"url": "https://developer.huawei.com/consumer/cn/doc/"}'
```

### 5. IDE集成

#### Trae AI
在Trae AI设置中添加MCP服务器，指向本项目的MCP端点。

#### VSCode + Cursor
使用MCP扩展配置（替换为你的服务器地址）:

```json
{
  "mcpServers": {
    "docs2mcp": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "http://localhost:5000/mcp"]
    }
  }
}
```

## 项目结构

```
Docs2MCP/
├── mcp-server/           # Python后端
│   ├── src/
│   │   ├── app.py       # Flask应用
│   │   ├── mcp_server.py # MCP服务器
│   │   └── utils/
│   │       ├── crawler.py    # 文档爬虫
│   │       └── scheduler.py  # 更新调度器
│   └── requirements.txt
├── flutter-app/          # Flutter前端
│   └── lib/
│       ├── main.dart
│       ├── pages/home_page.dart
│       └── services/
│           ├── mcp_service.dart
│           └── storage_service.dart
└── mcp-config.json       # MCP配置
```

## 开发

### 后端运行

```bash
cd mcp-server/src
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Flutter前端

#### 运行到移动设备
```bash
cd flutter-app
flutter pub get
flutter run
```

#### 运行到Web端
```bash
cd flutter-app
flutter pub get
flutter run -d web
```

#### 构建Web版本
```bash
cd flutter-app
flutter build web
```



## 功能

- ✅ 自动爬取官方文档
- ✅ 实时更新监控
- ✅ MCP协议支持
- ✅ 多端适配前端
- ✅ 文档搜索
- ✅ IDE AI集成
- ✅ Web端控制页面

## License

MIT
