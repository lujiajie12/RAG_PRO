# 文档索引

这个目录存放 `RAG_PRO / ContextPilot` 的项目文档。建议从上往下读。

## 阅读顺序

1. [00-getting-started.md](./00-getting-started.md)
2. [01-architecture.md](./01-architecture.md)
3. [02-backend-api.md](./02-backend-api.md)
4. [03-frontend-spec.md](./03-frontend-spec.md)
5. [04-llm-rag-agent-guide.md](./04-llm-rag-agent-guide.md)

## 每份文档解决什么问题

### [00-getting-started.md](./00-getting-started.md)

适合第一次接手项目时看，内容包括：

- 需要安装什么
- `.env` 怎么配
- Docker 服务怎么启动
- 后端怎么装依赖和初始化数据库
- 前端怎么安装和启动
- 当前阶段应该如何测试

### [01-architecture.md](./01-architecture.md)

解释项目整体结构和模块职责，包括：

- 前后端分层
- RAG / Agent / Memory / Ingestion 的边界
- 核心数据流
- 存储设计

### [02-backend-api.md](./02-backend-api.md)

描述当前后端 API 契约，包括：

- 路由列表
- 请求参数
- 响应结构
- SSE 事件格式
- 页面与接口的对应关系

### [03-frontend-spec.md](./03-frontend-spec.md)

描述前端工作台的页面结构和交互目标，包括：

- 页面路由
- 工作台布局
- 核心组件
- 响应式规则
- 状态管理建议

### [04-llm-rag-agent-guide.md](./04-llm-rag-agent-guide.md)

描述这个项目后续要落地的 AI 能力设计，包括：

- 文档解析
- parent / child chunking
- vector retrieval
- BM25
- RRF
- rerank
- context engineering
- agent tool calling
- short-term / long-term memory

## 当前维护建议

当你修改下列内容时，建议同步更新对应文档：

- 改接口字段：更新 `02-backend-api.md`
- 改页面结构：更新 `03-frontend-spec.md`
- 改模块边界或数据流：更新 `01-architecture.md`
- 改 RAG / Agent / Memory 方案：更新 `04-llm-rag-agent-guide.md`
- 改启动方式或本地环境准备：更新 `00-getting-started.md`
