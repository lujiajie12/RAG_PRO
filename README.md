# RAG_PRO / ContextPilot

`RAG_PRO` 是一个面向练手和工程化演示的 AI 应用项目，产品名是 `ContextPilot`。它的目标不是做一个单点 demo，而是把一套完整的大模型应用链路拆成清晰的前后端模块，包括知识库、RAG 检索、Agent 工具调用、会话管理、长时记忆和调试面板。

当前仓库已经具备比较完整的项目骨架：

- 前端有 3 个核心页面：`Chat Workspace`、`Knowledge Base`、`Memory Studio`
- 后端已经搭好 `Flask API + SQLAlchemy + SSE` 的接口边界
- 基础设施已经准备好 `PostgreSQL + pgvector + MinIO` 的本地开发编排
- `RAG / Agent / Memory` 目录结构和技术文档已经就位，适合继续往真实实现推进

需要注意的是，当前阶段仍然是“工程骨架 + 部分 mock/stub 实现”：

- 前端页面目前主要由 mock 数据驱动，视觉和交互已完成，尚未全量接入真实 API
- 后端接口、数据模型和服务层边界已经建立，但部分检索、摄取、记忆写入仍是占位实现
- 文档上传接口当前会写入文档记录，但还没有完全串起真实的 MinIO 落盘和解析索引流程
- 聊天接口已经是 SSE 形态，但返回内容目前是演示用的 stub 数据

## 这个项目要解决什么问题

这个项目想练的是一条完整的现代 AI 应用工程链路，而不是只练一个 prompt：

- 文档上传后构建知识库
- 基于 Hybrid Retrieval 的知识问答
- 基于 Agent 的工具调用与上下文编排
- 长时记忆的查看、写入和召回
- 对检索链路进行可视化调试
- 用一个前端工作台把这些能力串起来

## 核心页面

### 1. Chat Workspace

主工作区，用来承载：

- 会话列表
- 消息流
- 模型和检索模式切换
- Web Search 开关
- Retrieval Debug 面板

### 2. Knowledge Base

知识库页面，目标是承载：

- 文档上传
- 文档列表
- 文档状态查看
- chunk 数量和索引信息查看
- 文档删除和后续重建索引

### 3. Memory Studio

记忆页面，目标是承载：

- 长时记忆列表
- 记忆分类筛选
- 记忆来源会话查看
- pinned memory 管理
- 后续的手动新增、编辑和清理

## 技术栈

### 前端

- `Vue 3`
- `TypeScript`
- `Vite`
- `Vue Router`
- `Pinia`
- `Naive UI`
- `UnoCSS`

### 后端

- `Python 3.11+`
- `Flask`
- `Flask-SQLAlchemy`
- `Flask-Migrate`
- `Pydantic v2`
- `LangChain`
- `LangGraph`

### 基础设施

- `PostgreSQL 17`
- `pgvector`
- `MinIO`
- `Docker Compose`

## 项目结构

```text
RAG_PRO/
├─ backend/                 # Flask 后端、数据库模型、服务层、RAG/Agent/Memory 骨架
├─ frontend/                # Vue 前端工作台
├─ docs/                    # 技术文档
├─ infra/docker/            # 本地开发用基础设施编排
├─ .env.example             # 环境变量模板
└─ README.md
```

更细一点的模块划分：

- `backend/app/api`：HTTP/SSE 接口层
- `backend/app/services`：业务编排层
- `backend/app/repos`：数据库访问层
- `backend/app/models`：ORM 和 DTO
- `backend/app/rag`：检索与上下文构建骨架
- `backend/app/agent`：Agent 与工具层骨架
- `backend/app/memory`：长时记忆层骨架
- `backend/app/ingestion`：文档摄取与解析骨架
- `frontend/src/views`：三个主页面
- `frontend/src/components`：工作台组件
- `frontend/src/mocks`：前端当前使用的 mock 数据

## 快速开始

如果你只想先把项目跑起来，按下面顺序做即可。

### 1. 准备环境

建议本地安装这些工具：

- `Conda` / `Miniconda`
- `Node.js 20` 或更高
- `npm 10` 或更高
- `Docker Desktop` 或可用的 Docker Engine

### 2. 复制环境变量

在项目根目录执行：

```powershell
Copy-Item .env.example .env
```

然后打开 `.env`，至少确认下面这些值：

- `APP_PORT=5001`
- `CORS_ORIGINS=http://localhost:5173`
- `POSTGRES_HOST=localhost`
- `POSTGRES_PORT=5432`
- `POSTGRES_DB=contextpilot`
- `POSTGRES_USER=postgres`
- `POSTGRES_PASSWORD=postgres`
- `MINIO_ENDPOINT=localhost:9000`
- `OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`
- `OPENAI_API_KEY=replace-me`
- `CHAT_MODEL=qwen-plus`
- `EMBEDDING_MODEL=text-embedding-v4`

说明：

- 当前骨架阶段，即使 `OPENAI_API_KEY` 还是占位值，前端页面和多数后端接口也能先跑起来
- 如果你接阿里百炼真实模型，这里填百炼 API Key 即可

### 3. 启动基础设施

在项目根目录执行：

```powershell
docker compose -f infra/docker/docker-compose.yml up -d
```

默认会启动：

- PostgreSQL: `localhost:5432`
- MinIO API: `localhost:9000`
- MinIO Console: `http://localhost:9001`

### 4. 创建 Conda 环境并安装后端依赖

在项目根目录执行：

```powershell
conda create -n rag_pro python=3.11 -y
conda activate rag_pro
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

说明：

- 这会创建一个名为 `rag_pro` 的 Conda 虚拟环境
- `requirements.txt` 已经整理好了当前后端运行和开发需要的 Python 依赖
- 前端依赖仍然单独通过 `npm install` 安装

### 5. 初始化数据库

当前仓库里只预留了 `backend/migrations/README.md`，还没有提交 Alembic 迁移脚本，所以第一次本地运行时要先初始化一次迁移环境。

首次执行：

```powershell
Remove-Item backend/migrations/README.md -ErrorAction SilentlyContinue
python -m flask --app backend/run.py db init -d backend/migrations
python -m flask --app backend/run.py db migrate -d backend/migrations -m "init schema"
python -m flask --app backend/run.py db upgrade -d backend/migrations
```

如果你本地已经初始化过迁移环境，后续通常只需要：

```powershell
python -m flask --app backend/run.py db upgrade -d backend/migrations
```

### 6. 启动后端

仍然在项目根目录执行：

```powershell
python backend/run.py
```

启动后可访问：

- 根路径：`http://localhost:5001/`
- 健康检查：`http://localhost:5001/api/health`

### 7. 安装并启动前端

打开第二个终端，在项目根目录执行：

```powershell
Set-Location frontend
npm install
npm run dev
```

前端默认地址：

- `http://localhost:5173`

### 8. 打开页面验证

建议按下面顺序检查：

1. 打开 `http://localhost:5001/api/health`，确认后端是 `ok`
2. 打开 `http://localhost:5173`，确认前端工作台可以正常显示
3. 进入 `Chat Workspace / Knowledge Base / Memory Studio` 三个页面，确认路由切换正常

## 怎么用

### 前端怎么用

当前前端更偏“工作台原型”和“界面联调”阶段，你可以直接用它来查看：

- 聊天工作区布局
- Knowledge Base 页面结构
- Memory Studio 页面结构
- Retrieval Debug 面板的数据形状

由于当前主要是 mock 数据驱动：

- 前端页面可以独立于后端运行
- 就算后端没接真实数据，前端页面也能先打开
- 真正的 API 联调目前更适合直接调用后端接口测试

### 后端怎么用

后端当前最适合两种用途：

- 验证接口契约、请求字段和响应结构
- 在此基础上逐步替换 stub，实现真实的 RAG / Agent / Memory

你可以先从这些接口开始测：

- `GET /api/health`
- `GET /api/sessions`
- `POST /api/sessions`
- `POST /api/upload`
- `GET /api/documents`
- `GET /api/memory`
- `POST /api/retrieval/debug`
- `POST /api/chat/stream`

更完整的示例命令在 [docs/00-getting-started.md](./docs/00-getting-started.md)。

## 推荐阅读顺序

如果你准备继续开发这个项目，建议按下面顺序读文档：

1. [快速上手](./docs/00-getting-started.md)
2. [架构说明](./docs/01-architecture.md)
3. [后端 API 文档](./docs/02-backend-api.md)
4. [前端规格说明](./docs/03-frontend-spec.md)
5. [LLM / RAG / Agent 指南](./docs/04-llm-rag-agent-guide.md)

你也可以直接看文档总索引：[docs/README.md](./docs/README.md)

## 当前开发建议

如果你接下来准备继续把这个项目做完整，建议推进顺序是：

1. 先把基础 REST 接口和数据库流转打通
2. 再把前端 mock 数据替换为真实 API
3. 再实现真实的文档摄取、切分、embedding 和 hybrid retrieval
4. 最后接入 Agent tool calling、记忆写入和 LangGraph 持久化

## 常见说明

### 为什么前端能跑，但和后端像是没连起来

因为当前前端 store 主要还是读取 `frontend/src/mocks/workspace.ts` 里的数据，视觉和字段形状先行，真实联调还在后续阶段。

### 为什么上传文档后没有真的进入完整索引流程

因为当前 `DocumentService` 和 `IngestionPipeline` 还是骨架实现，文档元数据会入库，但真实的 MinIO 落盘、解析、切分和索引还需要继续补完。

### 为什么聊天接口返回的是演示内容

因为当前 `ChatService` 的 SSE 已经确定了事件格式，但内部答案内容仍是示例数据，便于先把前后端协议定住。

## 文档入口

- [快速上手](./docs/00-getting-started.md)
- [文档索引](./docs/README.md)
- [架构说明](./docs/01-architecture.md)
- [后端 API 文档](./docs/02-backend-api.md)
- [前端规格说明](./docs/03-frontend-spec.md)
- [LLM / RAG / Agent 指南](./docs/04-llm-rag-agent-guide.md)
