# Docs2MCP Server 使用指南

Docs2MCP 基于 Model Context Protocol (MCP) 标准，通过 Streamable HTTP 协议向 AI Agent 暴露文档抓取和搜索的核心能力。工具由 Agent 框架在运行时自动发现和调用，开发者只需完成接入配置即可。

## 概览

Docs2MCP 是一个智能文档抓取和检索服务，专为 AI 开发助手设计。它能够自动抓取指定 URL 的网页内容，支持动态页面（JavaScript 渲染）和多层深度抓取，并提供高效的文档搜索能力。

### 能力范围

#### 文档管理服务

| 工具 | 描述 | 版本要求 |
|------|------|----------|
| crawl_document | 添加并抓取新的文档 URL | 基础 |
| get_document | 根据 URL 获取完整文档内容 | 基础 |
| list_documents | 列出当前已抓取的所有文档 | 基础 |
| remove_document | 从监控列表中移除指定文档 | 基础 |
| refresh_document | 刷新指定文档的最新内容 | 基础 |

#### 搜索服务

| 工具 | 描述 | 版本要求 |
|------|------|----------|
| search_documentation | 在已抓取的文档中搜索关键词 | 基础 |
| ide_query | IDE 集成的快速查询接口 | 基础 |

#### 信息服务

| 工具 | 描述 | 版本要求 |
|------|------|----------|
| get_server_status | 获取服务器运行状态 | 基础 |
| get_resources | 获取 MCP 资源列表 | 基础 |

## 环境与端点

| 环境 | 端点 | 说明 |
|------|------|------|
| 本地开发 | `http://localhost:5000` | 开发调试使用 |
| 生产环境 | `http://{MCP_HOST}:{MCP_PORT}` | 根据实际部署配置 |

## 快速开始

### 第一步：启动服务器

```bash
cd mcp-server/src
python3 app.py
```

或使用独立的 MCP 服务器：

```bash
python3 mcp_server.py
```

### 第二步：验证连通性

发送以下请求获取工具列表，收到包含工具定义的 JSON 响应即表示接入成功：

```bash
curl -X GET "http://localhost:5000/mcp/tools" \
  -H "Content-Type: application/json; charset=utf-8"
```

成功响应示例：

```json
{
  "tools": [
    {
      "name": "search_documentation",
      "description": "Search through crawled documentation",
      "inputSchema": { ... }
    }
  ]
}
```

### 第三步：在 Agent 中配置

在你的 Agent 框架中添加以下 MCP Server 配置：

```
URL：http://localhost:5000
Type：streamable_http
```

## 协议规范

- **传输协议**：Streamable HTTP
- **消息格式**：JSON-RPC 2.0
- **Content-Type**：application/json; charset=utf-8

## 响应结构

所有工具响应均返回标准 JSON 结构，字段语义如下：

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| data / results | object/array | 请求返回的数据 |
| error | string | 错误信息（仅失败时返回） |
| message | string | 操作描述信息 |

## 核心约束

Agent 在调用工具前必须遵守以下约束，否则将触发参数校验错误或业务异常。

### 约束 1：URL 参数必须完整

所有文档操作必须提供完整的 URL，包含协议前缀（http:// 或 https://）：

```json
// ✅ 正确
{ "url": "https://docs.example.com/guide" }

// ❌ 错误
{ "url": "docs.example.com/guide" }
```

### 约束 2：动态内容页面需使用 Selenium

对于需要 JavaScript 渲染才能获取完整内容的页面，必须设置 `use_selenium: true`：

```json
// ✅ 使用 Selenium 抓取动态页面
{ "url": "https://reactjs.org/docs/getting-started.html", "use_selenium": true }

// ✅ 普通静态页面
{ "url": "https://httpbin.org/html", "use_selenium": false }
```

### 约束 3：搜索前需确保有已抓取的文档

search_documentation 和 ide_query 工具仅在有已抓取文档时返回有意义结果。建议在首次使用时先调用 crawl_document 添加文档源。

### 约束 4：大规模抓取需设置深度限制

为避免抓取过多页面，建议设置合理的 max_depth 参数：

```json
// ✅ 限制抓取深度为 2 层
{ "url": "https://docs.example.com", "max_depth": 2 }

// ✅ 限制最大文档数为 50
{ "url": "https://docs.example.com", "max_docs": 50 }
```

## 工具参考

### 文档管理服务

#### crawl_document — 添加并抓取文档

将指定的文档 URL 添加到抓取队列并执行抓取操作。支持单页抓取和多层深度抓取。

**参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | ✅ | 要抓取的文档 URL，必须包含协议前缀 |
| use_selenium | boolean | — | 是否使用 Selenium 抓取动态内容，默认 false |
| max_depth | number | — | 抓取深度，从该 URL 开始的链接最多跟随层数，默认 2 |
| max_docs | number | — | 最大抓取文档数量，默认 50 |

**关键返回字段**

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| success | boolean | 抓取是否成功 |
| data.title | string | 文档标题 |
| data.content | string | 文档内容（文本形式） |
| data.url | string | 文档原始 URL |
| data.crawled_at | string | 抓取时间（ISO 8601 格式） |
| data.depth | number | 当前文档所在深度 |

**Agent 建议提示词**

```
帮我抓取 https://docs.example.com/getting-started 这个页面

添加一个新的文档源 https://reactjs.org/docs

抓取这个文档，需要支持 JavaScript 渲染
```

**完整响应示例**

```json
{
  "success": true,
  "data": {
    "url": "https://docs.example.com/guide",
    "title": "快速入门指南",
    "content": "这是文档的完整内容...",
    "crawled_at": "2026-05-07T10:30:00Z",
    "depth": 0,
    "links_found": 15,
    "child_pages": [
      {
        "url": "https://docs.example.com/guide/installation",
        "depth": 1
      }
    ]
  },
  "message": "Document crawled successfully"
}
```

#### get_document — 获取文档内容

根据 URL 获取已抓取文档的完整内容。

**参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | ✅ | 要获取的文档 URL |
| project | string | — | 指定项目名称（可选） |

**关键返回字段**

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| success | boolean | 是否成功 |
| data.url | string | 文档 URL |
| data.title | string | 文档标题 |
| data.content | string | 文档完整内容 |
| data.crawled_at | string | 抓取时间 |

**Agent 建议提示词**

```
获取这个页面的完整内容：https://docs.example.com/api

查看 https://reactjs.org/docs/react-api.html 的详细内容
```

**完整响应示例**

```json
{
  "success": true,
  "data": {
    "url": "https://docs.example.com/guide",
    "title": "快速入门指南",
    "content": "这是文档的完整内容...",
    "crawled_at": "2026-05-07T10:30:00Z",
    "project": "example-docs"
  }
}
```

#### list_documents — 列出所有文档

获取当前已抓取的所有文档列表。

**参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project | string | — | 按项目名称筛选（可选） |

**关键返回字段**

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| success | boolean | 是否成功 |
| projects | array | 项目列表 |
| projects[].name | string | 项目名称 |
| projects[].filename | string | 存储文件名 |
| projects[].document_count | number | 文档数量 |
| projects[].last_updated | string | 最后更新时间 |

**Agent 建议提示词**

```
列出所有已抓取的文档

查看有哪些文档源已经被抓取
```

**完整响应示例**

```json
{
  "success": true,
  "projects": [
    {
      "name": "example-docs",
      "filename": "example-docs.json",
      "document_count": 25,
      "last_updated": "2026-05-07T10:30:00Z",
      "urls": [
        "https://docs.example.com/guide",
        "https://docs.example.com/api"
      ]
    }
  ],
  "total": 1
}
```

#### remove_document — 移除文档

从监控列表中移除指定的文档 URL。

**参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | ✅ | 要移除的文档 URL |

**关键返回字段**

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| success | boolean | true 表示移除成功 |

**Agent 建议提示词**

```
移除这个文档：https://docs.example.com/old-page

删除不再需要的文档源
```

**完整响应示例**

```json
{
  "success": true,
  "message": "Document removed from monitoring"
}
```

#### refresh_document — 刷新文档

重新抓取指定文档，获取最新内容。

**参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | ✅ | 要刷新的文档 URL |

**关键返回字段**

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| success | boolean | 是否成功 |
| data.crawled_at | string | 新的抓取时间 |
| data.content | string | 更新后的内容 |

**Agent 建议提示词**

```
刷新这个页面的内容：https://docs.example.com/guide

更新文档源以获取最新内容
```

**完整响应示例**

```json
{
  "success": true,
  "data": {
    "url": "https://docs.example.com/guide",
    "title": "快速入门指南（已更新）",
    "content": "这是更新后的文档内容...",
    "crawled_at": "2026-05-07T12:00:00Z"
  },
  "message": "Document refreshed successfully"
}
```

### 搜索服务

#### search_documentation — 搜索文档内容

在已抓取的文档中搜索包含指定关键词的内容。

**参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | ✅ | 搜索关键词 |
| limit | number | — | 返回结果数量上限，默认 10 |
| project | string | — | 指定项目名称筛选（可选） |

**关键返回字段**

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| results | array | 搜索结果列表 |
| results[].url | string | 文档 URL |
| results[].title | string | 文档标题 |
| results[].project | string | 所属项目 |
| results[].matches | array | 匹配的片段 |
| results[].matches[].snippet | string | 匹配的内容片段 |
| results[].score | number | 相关性得分 |
| total | number | 结果总数 |

**Agent 建议提示词**

```
搜索"安装"相关的文档

查找关于"配置"的说明
```

**完整响应示例**

```json
{
  "success": true,
  "query": "安装",
  "results": [
    {
      "url": "https://docs.example.com/guide/installation",
      "title": "安装指南",
      "project": "example-docs",
      "matches": [
        {
          "type": "text",
          "snippet": "...首先需要执行 npm install 命令进行安装..."
        }
      ],
      "score": 5
    }
  ],
  "total": 1
}
```

#### ide_query — IDE 快速查询

专为 AI IDE 集成的快速查询接口，返回格式优化便于 LLM 处理。

**参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | ✅ | 查询关键词 |
| q | string | ✅ | 同 query，URL 参数形式 |

**关键返回字段**

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| success | boolean | 是否成功 |
| query | string | 原始查询词 |
| results | array | 查询结果 |
| total | number | 结果数量 |

**Agent 建议提示词**

```
帮我查一下相关的文档说明

搜索这个关键词的文档
```

**完整响应示例**

```json
{
  "success": true,
  "query": "API",
  "results": [
    {
      "url": "https://docs.example.com/api",
      "title": "API 参考文档",
      "matches": [
        {
          "type": "text",
          "snippet": "...以下是 REST API 的详细说明..."
        }
      ]
    }
  ],
  "total": 1
}
```

### 信息服务

#### get_server_status — 获取服务器状态

查询 Docs2MCP 服务器的运行状态。

**参数**

无

**关键返回字段**

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| status | string | 服务器状态（running/offline） |
| version | string | 服务器版本 |
| documents_monitored | number | 当前监控的文档数量 |
| timestamp | string | 查询时间戳 |
| uptime | number | 运行时间（秒） |

**Agent 建议提示词**

```
检查服务器状态

查看服务是否正常运行
```

**完整响应示例**

```json
{
  "status": "running",
  "version": "1.0.0",
  "documents_monitored": 25,
  "uptime": 3600.5,
  "timestamp": "2026-05-07T10:30:00Z"
}
```

#### get_resources — 获取 MCP 资源

列出所有可用的 MCP 资源 URI。

**参数**

无

**关键返回字段**

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| resources | array | 资源列表 |
| resources[].uri | string | 资源 URI |
| resources[].name | string | 资源名称 |
| resources[].description | string | 资源描述 |
| total | number | 资源总数 |

**Agent 建议提示词**

```
列出所有可用的文档资源

查看有哪些文档可以访问
```

**完整响应示例**

```json
{
  "resources": [
    {
      "uri": "docs://https___docs_example_com_guide",
      "name": "快速入门指南",
      "description": "https://docs.example.com/guide",
      "mimeType": "application/json"
    }
  ],
  "total": 1
}
```

## 工作流程

### 完整文档抓取流程

**场景**：用户要求抓取一个完整的文档站点

**步骤 1**：获取起始 URL

```
用户：帮我抓取 https://docs.example.com 的所有文档
```

**步骤 2**：调用 crawl_document 启动抓取

```python
crawl_document(
    url="https://docs.example.com",
    max_depth=2,    # 限制抓取深度
    max_docs=50    # 限制最大文档数
)
```

**步骤 3**：确认抓取完成

返回结果包含抓取到的文档数量和子页面列表。

### 搜索使用流程

**场景**：用户在开发时需要查阅文档

**步骤 1**：发起搜索请求

```
用户：帮我找一下"安装"的说明
```

**步骤 2**：调用 search_documentation

```python
search_documentation(
    query="安装",
    limit=10
)
```

**步骤 3**：展示结果供用户选择

返回匹配度最高的文档列表和内容片段。

### 文档更新流程

**场景**：文档内容可能已更新，需要刷新

**步骤 1**：发起刷新请求

```
用户：刷新一下这个页面的内容
```

**步骤 2**：调用 refresh_document

```python
refresh_document(
    url="https://docs.example.com/guide"
)
```

**步骤 3**：返回最新内容

## 对话参考示例

### 示例 1：抓取新文档

```
用户：帮我抓取 React 官方文档的入门指南

Agent：（调用 crawl_document）
- URL: https://reactjs.org/docs/getting-started.html
- 使用 Selenium: false

抓取成功！
标题：开始使用 React
内容：[文档内容预览]

已添加到监控列表，后续可以随时搜索和查询。
```

### 示例 2：搜索文档内容

```
用户：搜索"组件"相关的文档

Agent：（调用 search_documentation）
- 查询词：组件

找到 3 个相关文档：

1. React 组件指南
   URL: https://reactjs.org/docs/components-and-props.html
   匹配片段："...组件允许你将 UI 拆分成独立可复用的部分..."

2. 函数组件与类组件
   URL: https://reactjs.org/docs/components-props.html
   匹配片段："...了解函数组件和类组件的区别..."

3. 组件状态管理
   URL: https://reactjs.org/docs/state-and-lifecycle.html
   匹配片段："...state 是组件私有的数据..."
```

### 示例 3：获取特定文档

```
用户：查看 React 官方文档中关于 Hook 的说明

Agent：（调用 get_document）
- URL: https://reactjs.org/docs/hooks-intro.html

文档内容：
[React Hook 完整文档内容]

需要我帮你搜索更多相关内容吗？
```

## 错误处理

### 错误码参考

| 错误码 | 含义 | 处理建议 |
|--------|------|----------|
| 400 | 参数错误 | 检查 URL 格式是否正确，是否包含协议前缀 |
| 404 | 文档不存在 | 确认 URL 是否正确，或先调用 crawl_document 抓取 |
| 500 | 服务器内部错误 | 检查服务器日志，稍后重试 |
| 503 | 服务不可用 | 确认服务器是否启动，网络是否正常 |

### 常见错误场景

#### 场景 1：URL 格式错误

```json
// ❌ 错误请求
{ "url": "docs.example.com/guide" }

// ✅ 正确请求
{ "url": "https://docs.example.com/guide" }

// 错误响应
{
  "success": false,
  "error": "URL must include protocol prefix (http:// or https://)"
}
```

#### 场景 2：文档未抓取

```json
// ❌ 尝试获取未抓取的文档
{ "url": "https://docs.example.com/new-page" }

// 错误响应
{
  "success": false,
  "error": "Document not found. Please crawl it first."
}
```

#### 场景 3：服务器未启动

```json
// 请求失败
{
  "success": false,
  "error": "Cannot connect to server. Please check if the server is running."
}
```

## 版本日志

| 版本 | 发布时间 | 更新内容 |
|------|----------|----------|
| v1.1.0 | 2026-05-07 | 完善工具定义，增强错误处理 |
| v1.0.0 | 2026-01-15 | 首次发布，提供基础文档抓取和搜索功能 |

## 附录

### 配置说明

#### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| MCP_HOST | localhost | 服务器主机地址 |
| MCP_PORT | 5000 | 服务器端口 |
| DATA_DIR | ./data | 文档数据存储目录 |
| CHECK_INTERVAL | 3600 | 文档检查更新间隔（秒） |

#### MCP 配置文件示例 (mcp-config.json)

```json
{
  "mcpServers": {
    "docs2mcp": {
      "command": "python3",
      "args": [
        "-m",
        "http.client",
        "--port",
        "5000"
      ],
      "env": {
        "MCP_HOST": "localhost",
        "MCP_PORT": "5000"
      },
      "description": "Docs2MCP - Documentation Crawler for AI Development"
    }
  }
}
```

### 数据存储格式

抓取的文档以 JSON 格式存储在 data 目录下，文件名格式为 `{项目名}.json`：

```json
{
  "project": "example-docs",
  "crawled_at": "2026-05-07T10:30:00Z",
  "documents": [
    {
      "url": "https://docs.example.com/guide",
      "title": "快速入门指南",
      "content": "这是文档的完整内容...",
      "crawled_at": "2026-05-07T10:30:00Z",
      "depth": 0
    }
  ]
}
```
