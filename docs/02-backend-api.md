# 02 Backend API

## 你开发这一章时要先完成什么
- 先看应用入口 [backend/app/__init__.py](/g:/学习空间夸克/练手项目/RAG_PRO/backend/app/__init__.py)。
- 先确认 DTO 定义 [backend/app/models/schemas.py](/g:/学习空间夸克/练手项目/RAG_PRO/backend/app/models/schemas.py)。
- 先确认 API blueprint 边界 [backend/app/api](/g:/学习空间夸克/练手项目/RAG_PRO/backend/app/api)。
- 聊天接口默认采用 `SSE`，不要先用普通 JSON 替代。

## 基础约定

### Base URL
- 本地开发：`http://localhost:5001`
- API 前缀：`/api`

### 鉴权与用户标识
- 当前版本不做登录。
- 所有接口都要求显式传 `user_id`，来源可为：
  - query
  - JSON body
  - form-data
- 后续上线版可替换成 `X-User-Id` 或 JWT claims。

### 响应约定
- 成功：返回业务 JSON，或返回 SSE 事件流。
- 校验失败：`400`
- 资源不存在：`404`
- 模型/下游错误：`502`
- 未知错误：`500`

### 错误响应统一格式
```json
{
  "error": "memory not found",
  "code": "resource_not_found",
  "details": {}
}
```

## API 总览

| Method | Path | 用途 | 前端页面 |
| --- | --- | --- | --- |
| GET | `/api/health` | 健康检查 | 无 |
| GET | `/api/sessions` | 会话列表 | Chat Workspace 左侧 |
| POST | `/api/sessions` | 新建会话 | Chat Workspace 左侧 |
| POST | `/api/upload` | 上传文档 | Knowledge Base |
| GET | `/api/documents` | 查询文档 | Knowledge Base |
| DELETE | `/api/documents/{document_id}` | 删除文档 | Knowledge Base |
| GET | `/api/memory` | 查询记忆 | Memory Studio |
| POST | `/api/memory` | 手动新增记忆 | Memory Studio |
| DELETE | `/api/memory/{memory_id}` | 删除记忆 | Memory Studio |
| POST | `/api/retrieval/debug` | 单独调试检索链路 | Chat Debug Panel |
| POST | `/api/chat/stream` | 流式对话 | Chat Workspace |

## GET /api/health

### 作用
用于开发期探活、前后端联调和容器编排健康检查。

### 请求参数
无。

### JSON Schema
```json
{
  "type": "object",
  "required": ["service", "status", "env"],
  "properties": {
    "service": { "type": "string" },
    "status": { "type": "string", "enum": ["ok"] },
    "env": { "type": "string" }
  }
}
```

### 成功响应
```json
{
  "service": "ContextPilot",
  "status": "ok",
  "env": "development"
}
```

### 前端调用关系
- 一般不在主页面展示。
- 可用于启动页或开发模式下的“环境连接正常”提示。

## GET /api/sessions

### 作用
返回指定用户的会话列表，供 Chat 页面左侧 Session Rail 展示。

### 请求参数

| 参数 | 位置 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- | --- |
| `user_id` | query | string | 是 | 用户标识 |

### JSON Schema
```json
{
  "type": "array",
  "items": {
    "type": "object",
    "required": ["id", "user_id", "title", "thread_id", "created_at"],
    "properties": {
      "id": { "type": "string" },
      "user_id": { "type": "string" },
      "kb_id": { "type": ["string", "null"] },
      "title": { "type": "string" },
      "thread_id": { "type": "string" },
      "last_message_at": { "type": ["string", "null"], "format": "date-time" },
      "created_at": { "type": "string", "format": "date-time" }
    }
  }
}
```

### 成功响应示例
```json
[
  {
    "id": "sess-1",
    "user_id": "demo-user",
    "kb_id": "kb-langchain",
    "title": "LangChain 学习笔记整理",
    "thread_id": "demo-user:kb-langchain",
    "last_message_at": "2026-03-12T10:42:00Z",
    "created_at": "2026-03-12T10:10:00Z"
  }
]
```

### 错误示例
```json
{
  "error": "user_id is required",
  "code": "validation_error",
  "details": {}
}
```

### 前端调用关系
- Chat 页面初始化时调用。
- 新建会话成功后应重新刷新此接口。

## POST /api/sessions

### 作用
创建一个新的对话会话。

### 请求参数

| 参数 | 位置 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- | --- |
| `user_id` | body | string | 是 | 用户标识 |
| `kb_id` | body | string | 否 | 当前会话关联知识库 |
| `title` | body | string | 否 | 会话标题，默认 `New conversation` |

### JSON Schema
```json
{
  "type": "object",
  "required": ["user_id"],
  "properties": {
    "user_id": { "type": "string" },
    "kb_id": { "type": ["string", "null"] },
    "title": { "type": ["string", "null"] }
  }
}
```

### 成功响应示例
```json
{
  "id": "sess-9",
  "user_id": "demo-user",
  "kb_id": "kb-langchain",
  "title": "New conversation",
  "thread_id": "demo-user:kb-langchain",
  "last_message_at": null,
  "created_at": "2026-03-12T11:00:00Z"
}
```

### 前端调用关系
- Chat 页面“新建”按钮。
- 成功后切换当前会话，并清空消息区到新状态。

## POST /api/upload

### 作用
上传原始文件并创建文档记录；真实实现中会异步触发解析、切分、embedding 和 BM25 建索引。

### 请求参数

| 参数 | 位置 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- | --- |
| `file` | form-data | binary | 是 | 原始文件 |
| `user_id` | form-data | string | 是 | 用户标识 |
| `kb_id` | form-data | string | 是 | 目标知识库 |

### JSON Schema
```json
{
  "type": "object",
  "required": ["document_id", "kb_id", "status", "parsed_type"],
  "properties": {
    "document_id": { "type": "string" },
    "kb_id": { "type": "string" },
    "status": { "type": "string" },
    "parsed_type": { "type": "string" }
  }
}
```

### 成功响应示例
```json
{
  "document_id": "doc-1",
  "kb_id": "kb-langchain",
  "status": "uploaded",
  "parsed_type": "pdf"
}
```

### 错误响应示例
```json
{
  "error": "file is required",
  "code": "validation_error",
  "details": {}
}
```

### 前端调用关系
- Knowledge Base 上传面板。
- 上传成功后立即刷新 `/api/documents`。

## GET /api/documents

### 作用
按知识库查询文档列表及索引状态。

### 请求参数

| 参数 | 位置 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- | --- |
| `user_id` | query | string | 是 | 用户标识 |
| `kb_id` | query | string | 是 | 目标知识库 |

### JSON Schema
```json
{
  "type": "array",
  "items": {
    "type": "object",
    "required": ["id", "user_id", "kb_id", "file_name", "file_type", "status", "parsed_type", "chunk_count", "created_at", "updated_at"],
    "properties": {
      "id": { "type": "string" },
      "user_id": { "type": "string" },
      "kb_id": { "type": "string" },
      "file_name": { "type": "string" },
      "file_type": { "type": "string" },
      "status": { "type": "string" },
      "parsed_type": { "type": "string" },
      "chunk_count": { "type": "integer" },
      "created_at": { "type": "string", "format": "date-time" },
      "updated_at": { "type": "string", "format": "date-time" }
    }
  }
}
```

### 成功响应示例
```json
[
  {
    "id": "doc-1",
    "user_id": "demo-user",
    "kb_id": "kb-langchain",
    "file_name": "langchain-notes.md",
    "file_type": "md",
    "status": "indexed",
    "parsed_type": "markdown",
    "chunk_count": 112,
    "created_at": "2026-03-12T10:11:00Z",
    "updated_at": "2026-03-12T10:14:00Z"
  }
]
```

### 前端调用关系
- Knowledge Base 文档列表。
- 删除或上传后重新请求。

## DELETE /api/documents/{document_id}

### 作用
删除文档及其关联 chunk、embedding、BM25 索引快照。

### Path 参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `document_id` | string | 是 | 文档 ID |

### 成功响应
- `204 No Content`

### 错误响应示例
```json
{
  "error": "document not found",
  "code": "resource_not_found",
  "details": {}
}
```

### 前端调用关系
- Knowledge Base 文档详情抽屉和文档卡片的删除动作。

## GET /api/memory

### 作用
获取指定用户的长期记忆列表。

### 请求参数

| 参数 | 位置 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- | --- |
| `user_id` | query | string | 是 | 用户标识 |

### JSON Schema
```json
{
  "type": "array",
  "items": {
    "type": "object",
    "required": ["id", "user_id", "category", "summary", "content", "pinned", "created_at", "updated_at"],
    "properties": {
      "id": { "type": "string" },
      "user_id": { "type": "string" },
      "category": { "type": "string" },
      "summary": { "type": "string" },
      "content": { "type": "string" },
      "source_session_id": { "type": ["string", "null"] },
      "pinned": { "type": "boolean" },
      "score": { "type": ["number", "null"] },
      "created_at": { "type": "string", "format": "date-time" },
      "updated_at": { "type": "string", "format": "date-time" }
    }
  }
}
```

### 成功响应示例
```json
[
  {
    "id": "mem-1",
    "user_id": "demo-user",
    "category": "preference",
    "summary": "回答尽量先给结论再解释",
    "content": "用户偏好结构化输出，先总结核心结论，再展开原理与步骤。",
    "source_session_id": "sess-1",
    "pinned": true,
    "score": 0.97,
    "created_at": "2026-03-11T15:30:00Z",
    "updated_at": "2026-03-12T09:10:00Z"
  }
]
```

### 前端调用关系
- Memory Studio 主列表。
- Chat 页面也可以用它做“召回预览”。

## POST /api/memory

### 作用
手动新增一条固定记忆，适用于手工注入偏好、演示脚本或业务背景。

### 请求参数

| 参数 | 位置 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- | --- |
| `user_id` | body | string | 是 | 用户标识 |
| `category` | body | enum | 是 | `preference` / `long_term_task` / `background_fact` / `manual_note` |
| `summary` | body | string | 是 | 短摘要 |
| `content` | body | string | 是 | 完整内容 |
| `pinned` | body | boolean | 否 | 是否置顶 |
| `source_session_id` | body | string | 否 | 来源会话 |

### JSON Schema
```json
{
  "type": "object",
  "required": ["user_id", "category", "summary", "content"],
  "properties": {
    "user_id": { "type": "string" },
    "category": {
      "type": "string",
      "enum": ["preference", "long_term_task", "background_fact", "manual_note"]
    },
    "summary": { "type": "string" },
    "content": { "type": "string" },
    "pinned": { "type": "boolean" },
    "source_session_id": { "type": ["string", "null"] }
  }
}
```

### 成功响应示例
```json
{
  "id": "mem-9",
  "user_id": "demo-user",
  "category": "manual_note",
  "summary": "演示时优先展示 retrieval debug 面板",
  "content": "用于面试演示，突出 Hybrid Retrieval、RRF、rerank 分数和 final context。",
  "source_session_id": null,
  "pinned": true,
  "score": null,
  "created_at": "2026-03-12T11:20:00Z",
  "updated_at": "2026-03-12T11:20:00Z"
}
```

### 前端调用关系
- Memory Studio “手动添加”。

## DELETE /api/memory/{memory_id}

### 作用
删除一条长期记忆。

### 成功响应
- `204 No Content`

### 错误响应示例
```json
{
  "error": "memory not found",
  "code": "resource_not_found",
  "details": {}
}
```

### 前端调用关系
- Memory 卡片右下角删除按钮。

## POST /api/retrieval/debug

### 作用
在不发起完整聊天的情况下，直接查看一条 query 的检索全链路。

### 请求参数

| 参数 | 位置 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- | --- |
| `user_id` | body | string | 是 | 用户标识 |
| `kb_id` | body | string | 是 | 知识库 ID |
| `query` | body | string | 是 | 查询文本 |

### JSON Schema
```json
{
  "type": "object",
  "required": ["query", "vector_hits", "bm25_hits", "rrf_hits", "rerank_hits", "final_context", "prompt_budget"],
  "properties": {
    "query": { "type": "string" },
    "vector_hits": { "$ref": "#/$defs/hitArray" },
    "bm25_hits": { "$ref": "#/$defs/hitArray" },
    "rrf_hits": { "$ref": "#/$defs/hitArray" },
    "rerank_hits": { "$ref": "#/$defs/hitArray" },
    "final_context": { "$ref": "#/$defs/hitArray" },
    "prompt_budget": {
      "type": "object",
      "additionalProperties": { "type": "integer" }
    }
  },
  "$defs": {
    "hitArray": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["chunk_id", "file_name", "content_preview", "score", "metadata"],
        "properties": {
          "chunk_id": { "type": "string" },
          "file_name": { "type": "string" },
          "content_preview": { "type": "string" },
          "score": { "type": "number" },
          "parent_id": { "type": ["string", "null"] },
          "metadata": { "type": "object" }
        }
      }
    }
  }
}
```

### 成功响应示例
```json
{
  "query": "Parent Document Retrieval 为什么更适合教程型文档？",
  "vector_hits": [
    {
      "chunk_id": "c-101",
      "file_name": "langchain-notes.md",
      "content_preview": "Parent Document Retrieval improves answer quality by returning a larger parent block.",
      "score": 0.88,
      "parent_id": "p-11",
      "metadata": { "page": 12 }
    }
  ],
  "bm25_hits": [],
  "rrf_hits": [],
  "rerank_hits": [],
  "final_context": [],
  "prompt_budget": {
    "system": 600,
    "history": 1200,
    "memory": 800,
    "retrieved_context": 2400,
    "user_query": 1000
  }
}
```

### 前端调用关系
- Chat Debug Panel 单独调试。
- 聊天时也可复用相同结构塞入 SSE 的 `retrieval_debug` 事件。

## POST /api/chat/stream

### 作用
主聊天接口。使用 `SSE` 逐步返回 token、tool call、retrieval debug 和最终答案。

### 请求参数

| 参数 | 位置 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- | --- |
| `user_id` | body | string | 是 | 用户标识 |
| `session_id` | body | string | 否 | 已有会话 ID，首次为空 |
| `kb_id` | body | string | 否 | 当前知识库 ID |
| `message` | body | string | 是 | 用户输入 |
| `allow_web` | body | boolean | 否 | 是否允许外网搜索 |
| `debug` | body | boolean | 否 | 是否返回 `retrieval_debug` 事件 |

### 请求 JSON Schema
```json
{
  "type": "object",
  "required": ["user_id", "message"],
  "properties": {
    "user_id": { "type": "string" },
    "session_id": { "type": ["string", "null"] },
    "kb_id": { "type": ["string", "null"] },
    "message": { "type": "string", "minLength": 1 },
    "allow_web": { "type": "boolean", "default": false },
    "debug": { "type": "boolean", "default": false }
  }
}
```

### SSE 事件格式
```text
event: token
data: {"text":"..."}

event: tool_call
data: {"name":"rag_search","status":"completed","input":{},"output":{}}

event: retrieval_debug
data: {...}

event: final_answer
data: {"session_id":"sess-1","answer":"...","citations":[],"tool_trace":[]}

event: error
data: {"message":"..."}
```

### `token` 事件 Schema
```json
{
  "type": "object",
  "required": ["text"],
  "properties": {
    "text": { "type": "string" }
  }
}
```

### `tool_call` 事件 Schema
```json
{
  "type": "object",
  "required": ["name", "status", "input", "output"],
  "properties": {
    "name": { "type": "string" },
    "status": {
      "type": "string",
      "enum": ["planned", "running", "completed", "failed"]
    },
    "input": { "type": "object" },
    "output": { "type": "object" }
  }
}
```

### `final_answer` 事件 Schema
```json
{
  "type": "object",
  "required": ["session_id", "answer", "citations", "tool_trace"],
  "properties": {
    "session_id": { "type": "string" },
    "answer": { "type": "string" },
    "citations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["document_id", "file_name", "chunk_id"],
        "properties": {
          "document_id": { "type": "string" },
          "file_name": { "type": "string" },
          "page": { "type": ["integer", "null"] },
          "chunk_id": { "type": "string" },
          "rerank_score": { "type": ["number", "null"] }
        }
      }
    },
    "tool_trace": {
      "type": "array",
      "items": { "$ref": "#/$defs/toolTrace" }
    }
  },
  "$defs": {
    "toolTrace": {
      "type": "object",
      "required": ["name", "status", "input", "output"],
      "properties": {
        "name": { "type": "string" },
        "status": { "type": "string" },
        "input": { "type": "object" },
        "output": { "type": "object" }
      }
    }
  }
}
```

### 成功事件示例
```text
event: token
data: {"text":"Parent Document Retrieval 更适合教程型文档，"}

event: tool_call
data: {"name":"rag_search","status":"completed","input":{"query":"Parent Document Retrieval 为什么更适合教程型文档？","kb_id":"kb-langchain"},"output":{"top_k":8,"strategy":"hybrid+rerank"}}

event: final_answer
data: {"session_id":"sess-1","answer":"Parent Document Retrieval 更适合教程型文档，因为它用子块做命中、用父块还原上下文，能同时保留章节逻辑与答案局部相关性。","citations":[{"document_id":"doc-langchain-notes","file_name":"langchain-notes.md","page":12,"chunk_id":"p-11","rerank_score":0.96}],"tool_trace":[{"name":"rag_search","status":"completed","input":{"query":"Parent Document Retrieval 为什么更适合教程型文档？","kb_id":"kb-langchain"},"output":{"top_k":8,"strategy":"hybrid+rerank"}}]}
```

### 错误事件示例
```text
event: error
data: {"message":"knowledge base is unavailable"}
```

### 前端调用关系
- Chat Workspace 消息发送按钮。
- token 流用于实时打字机效果。
- `tool_call` 用于消息卡下方的 tool trace。
- `retrieval_debug` 用于右侧调试面板。
- `final_answer` 用于落库、显示 citation、结束 loading 状态。

## 接口实现顺序建议
1. `GET /api/health`
2. `GET/POST /api/sessions`
3. `POST /api/upload` + `GET /api/documents`
4. `GET/POST/DELETE /api/memory`
5. `POST /api/retrieval/debug`
6. `POST /api/chat/stream`

## 当前骨架说明
- 当前仓库里的 API 路由和 DTO 已经建好，但业务实现仍是 mock/stub。
- 你开发真实功能时，优先保持返回字段和事件名不变。
- 如果必须新增字段，先同步修改：
  - [backend/app/models/schemas.py](/g:/学习空间夸克/练手项目/RAG_PRO/backend/app/models/schemas.py)
  - [frontend/src/types/index.ts](/g:/学习空间夸克/练手项目/RAG_PRO/frontend/src/types/index.ts)
  - 本文档对应章节
