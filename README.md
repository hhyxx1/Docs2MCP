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

### 1. 服务器已部署

MCP服务器已部署在: `http://115.190.247.178:5000`

### 2. API端点

- `GET /api/server/status` - 服务器状态
- `GET /api/docs/list` - 文档列表
- `POST /api/docs/add` - 添加文档
- `POST /api/docs/remove` - 移除文档
- `GET /api/ide/query?q=<search>` - AI查询接口
- `GET /mcp/info` - MCP信息

### 3. 添加华为文档示例

```bash
curl -X POST http://115.190.247.178:5000/api/docs/add \
  -H "Content-Type: application/json" \
  -d '{"url": "https://developer.huawei.com/consumer/cn/doc/"}'
```

### 4. IDE集成

#### Trae AI
在Trae AI设置中添加MCP服务器，指向本项目的MCP端点。

#### VSCode + Cursor
使用MCP扩展配置:

```json
{
  "mcpServers": {
    "docs2mcp": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "http://115.190.247.178:5000/mcp"]
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
├── mcp-config.json       # MCP配置
└── deploy_*.sh/exp       # 部署脚本
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

```bash
cd flutter-app
flutter pub get
flutter run
```

## 功能

- ✅ 自动爬取官方文档
- ✅ 实时更新监控
- ✅ MCP协议支持
- ✅ 多端适配前端
- ✅ 文档搜索
- ✅ IDE AI集成

## License

MIT
