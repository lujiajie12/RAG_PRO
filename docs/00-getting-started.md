# 00 快速上手

这份文档只做一件事：让你从 0 开始，把 `RAG_PRO / ContextPilot` 在本地跑起来，并知道当前阶段应该怎么测试。

## 1. 环境准备

建议本地准备：

- `Conda` / `Miniconda`
- `Node.js 20+`
- `npm 10+`
- `Docker Desktop` 或可用的 Docker Engine
- `Git`

可选但推荐：

- `Postman` 或 `Apifox`
- 一个支持 SSE 的 API 调试工具

## 2. 获取代码

如果你已经在本地打开这个仓库，可以跳过。

```powershell
git clone <your-repo-url> RAG_PRO
Set-Location RAG_PRO
```

## 3. 配置环境变量

在仓库根目录执行：

```powershell
Copy-Item .env.example .env
```

然后编辑 `.env`。

当前默认值已经适用于本地开发，重点关注以下字段：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `APP_HOST` | `0.0.0.0` | 后端监听地址 |
| `APP_PORT` | `5001` | 后端端口 |
| `CORS_ORIGINS` | `http://localhost:5173` | 前端开发地址 |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/contextpilot` | 本地数据库 |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO API 地址 |
| `MINIO_BUCKET` | `knowledge-files` | 默认桶名 |
| `OPENAI_API_KEY` | `replace-me` | 当前可先占位，后续接真实模型时再替换 |
| `CHAT_MODEL` | `gpt-4.1-mini` | 预留的聊天模型名 |
| `EMBEDDING_MODEL` | `text-embedding-3-large` | 预留的 embedding 模型名 |

说明：

- 目前仓库仍然是工程骨架阶段，所以 `OPENAI_API_KEY` 不是立即阻塞项
- 但如果你后续要接真实 LLM / embedding，建议现在就填好

## 4. 启动 PostgreSQL 和 MinIO

在仓库根目录执行：

```powershell
docker compose -f infra/docker/docker-compose.yml up -d
```

查看容器状态：

```powershell
docker compose -f infra/docker/docker-compose.yml ps
```

默认暴露端口：

- PostgreSQL: `5432`
- MinIO API: `9000`
- MinIO Console: `9001`

如果你想停掉：

```powershell
docker compose -f infra/docker/docker-compose.yml down
```

如果你想连同数据卷一起清理：

```powershell
docker compose -f infra/docker/docker-compose.yml down -v
```

注意：`down -v` 会删除本地容器卷数据。

## 5. 创建 Conda 环境并安装后端依赖

在仓库根目录执行：

```powershell
conda create -n rag_pro python=3.11 -y
conda activate rag_pro
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

安装完成后，你会拿到这些核心依赖：

- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- psycopg
- pgvector
- minio
- langchain
- langgraph
- pytest
- ruff

补充说明：

- 这里的 `requirements.txt` 位于仓库根目录
- 它和 `backend/pyproject.toml` 保持同一套依赖范围
- 如果你的 PowerShell 里 `conda activate` 不生效，先执行一次 `conda init powershell`，然后重开终端

## 6. 初始化数据库

当前仓库只预留了 `backend/migrations/README.md`，还没有提交 Alembic 迁移环境和版本文件，所以第一次启动前要先做一次初始化。

### 第一次本地初始化

```powershell
Remove-Item backend/migrations/README.md -ErrorAction SilentlyContinue
python -m flask --app backend/run.py db init -d backend/migrations
python -m flask --app backend/run.py db migrate -d backend/migrations -m "init schema"
python -m flask --app backend/run.py db upgrade -d backend/migrations
```

### 后续更新数据库结构

如果以后 ORM 结构改了，可以继续：

```powershell
python -m flask --app backend/run.py db migrate -d backend/migrations -m "describe your change"
python -m flask --app backend/run.py db upgrade -d backend/migrations
```

### 如果你只是重复启动项目

通常只需要：

```powershell
python -m flask --app backend/run.py db upgrade -d backend/migrations
```

## 7. 启动后端

仍然在仓库根目录执行：

```powershell
python backend/run.py
```

默认启动地址：

- 根路径：`http://localhost:5001/`
- 健康检查：`http://localhost:5001/api/health`

你应该能看到类似返回：

```json
{
  "service": "ContextPilot",
  "status": "ok",
  "env": "development"
}
```

## 8. 启动前端

打开第二个终端，进入前端目录：

```powershell
Set-Location frontend
npm install
npm run dev
```

默认前端地址：

- `http://localhost:5173`

说明：

- 当前前端页面主要由 mock 数据驱动
- 所以前端可以先独立跑起来
- 后续接真实 API 时，再把 store 数据源切到后端接口

## 9. 最小验证清单

按下面顺序验证最省时间：

### 9.1 检查后端健康状态

浏览器打开：

- `http://localhost:5001/api/health`

或者命令行执行：

```powershell
curl.exe http://localhost:5001/api/health
```

### 9.2 检查前端页面能否打开

浏览器打开：

- `http://localhost:5173`

确认这三个页面能切换：

- `Chat Workspace`
- `Knowledge Base`
- `Memory Studio`

### 9.3 检查后端会话接口

创建会话：

```powershell
curl.exe -X POST http://localhost:5001/api/sessions -H "Content-Type: application/json" -d '{"user_id":"demo-user","kb_id":"default-kb","title":"First Session"}'
```

查询会话：

```powershell
curl.exe "http://localhost:5001/api/sessions?user_id=demo-user"
```

### 9.4 检查 Memory 接口

新增一条记忆：

```powershell
curl.exe -X POST http://localhost:5001/api/memory -H "Content-Type: application/json" -d '{"user_id":"demo-user","category":"manual_note","summary":"演示时优先展示 debug 面板","content":"用于联调和演示。","pinned":true}'
```

查询记忆：

```powershell
curl.exe "http://localhost:5001/api/memory?user_id=demo-user"
```

### 9.5 检查 Retrieval Debug 接口

```powershell
curl.exe -X POST http://localhost:5001/api/retrieval/debug -H "Content-Type: application/json" -d '{"user_id":"demo-user","kb_id":"default-kb","query":"Parent Document Retrieval 为什么更适合教程型文档？"}'
```

### 9.6 检查聊天 SSE 接口

```powershell
curl.exe -N -X POST http://localhost:5001/api/chat/stream -H "Content-Type: application/json" -d '{"user_id":"demo-user","session_id":"demo-session","kb_id":"default-kb","message":"Parent Document Retrieval 为什么更适合教程型文档？","debug":true}'
```

你会看到连续的 SSE 事件，例如：

- `token`
- `tool_call`
- `retrieval_debug`
- `final_answer`

## 10. 当前阶段应该怎么用这个项目

目前最合理的使用方式不是“直接当成完整产品来用”，而是按下面方式推进：

### 用法一：前端工作台原型

适合：

- 看页面结构
- 调整视觉样式
- 改组件层次
- 规划状态管理

当前特点：

- UI 完整度不错
- 交互骨架比较清晰
- 数据主要来自 mock

### 用法二：后端接口脚手架

适合：

- 对齐 API 契约
- 稳定 DTO
- 先打通数据库增删查
- 后续替换内部 stub 为真实逻辑

当前特点：

- API 边界已经清晰
- 服务层和 repo 层已拆开
- SSE 事件格式已定

### 用法三：RAG / Agent / Memory 工程练手项目

适合：

- 逐步实现文档解析
- 加入 chunk 切分和 embedding
- 实现 vector + BM25 + RRF + rerank
- 接入 LangChain / LangGraph
- 做长时记忆写入与召回

## 11. 当前真实状态说明

为了避免你在联调时产生误判，这里把当前仓库状态说清楚。

### 已经具备的部分

- Flask 应用工厂和蓝图结构
- SQLAlchemy ORM 模型
- 会话、记忆、文档、检索调试、聊天 SSE 的接口
- Vue 前端工作台和三大页面
- PostgreSQL / MinIO 的本地开发编排
- RAG / Agent / Memory 的模块骨架

### 仍是占位实现的部分

- 文档真实落盘到 MinIO
- 文档解析和 chunk 切分
- embedding 写入和 pgvector 检索
- BM25 索引构建
- rerank
- 真实 Agent tool calling
- 自动 memory extraction
- 前端对真实 API 的全量接入

## 12. 常见问题

### 1. 前端打开了，但数据看起来是写死的

这是当前设计的一部分。前端现在优先稳定页面结构和数据字段形状，所以仍然使用 `frontend/src/mocks/workspace.ts`。

### 2. 后端能启动，但不是完整的 AI 问答系统

对。当前后端更接近“接口边界稳定、内部逻辑待补”的阶段，重点是让你可以继续往真实实现演进。

### 3. 一定要装 Docker 吗

不是绝对必须，但最省事。因为当前默认配置已经把 PostgreSQL 和 MinIO 的地址写成了本地 Docker 服务。

### 4. `OPENAI_API_KEY` 现在一定要填真实值吗

不是。当前骨架里大多数能力不会马上用到真实模型，但你后续接入真实 RAG / Agent 时一定会需要它。

## 13. 下一步建议

如果你准备继续开发，我建议按这个顺序推进：

1. 先把 `sessions / documents / memory` 的真实数据库流转彻底打通
2. 再把前端 store 从 mock 切到真实 API
3. 再实现 ingestion pipeline 和 chunk/embedding
4. 再实现 hybrid retrieval、rerank 和 context builder
5. 最后接入 LangGraph persistence 和 long-term memory

## 14. 相关文档

- [文档总索引](./README.md)
- [架构说明](./01-architecture.md)
- [后端 API 文档](./02-backend-api.md)
- [前端规格说明](./03-frontend-spec.md)
- [LLM / RAG / Agent 指南](./04-llm-rag-agent-guide.md)
