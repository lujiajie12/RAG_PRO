# 04 LLM RAG Agent Guide

## 你开发这一章时要先完成什么
- 先读 RAG 模块骨架 [backend/app/rag](/g:/学习空间夸克/练手项目/RAG_PRO/backend/app/rag)。
- 先读 Agent 模块骨架 [backend/app/agent](/g:/学习空间夸克/练手项目/RAG_PRO/backend/app/agent)。
- 先读 Memory 模块骨架 [backend/app/memory](/g:/学习空间夸克/练手项目/RAG_PRO/backend/app/memory)。
- 明确本项目的目标不是“极致性能”，而是“能完整展示现代 AI 应用工程思路”。

## 一句话设计目标
让系统同时具备：

- 检索型问答能力
- 工具调用能力
- 用户长期偏好记忆
- 可解释的上下文拼装
- 可视化调试能力

## RAG 设计

## 1. 文档加载与解析

### 支持格式
- `pdf`
- `docx`
- `md`
- `txt`
- `html`

### 解析输出要求
每个文档都要尽量保留：
- `file_name`
- `page`
- `heading_path`
- `section_title`
- `position`
- `raw_text`

原因：
- 后续 citation 需要来源。
- Parent Document Retrieval 需要知道子块来自哪个父语义单元。
- rerank 和 debug 面板需要保留可解释元数据。

## 2. 父子切分设计

### 推荐参数
- Parent chunk：`800 ~ 1200 tokens`
- Parent overlap：`100 ~ 160 tokens`
- Child chunk：`180 ~ 250 tokens`
- Child overlap：`30 ~ 50 tokens`

### 为什么这么切
- 父块负责“回答时读得懂”。
- 子块负责“召回时打得准”。
- 如果直接用大块做检索，召回分辨率不够。
- 如果直接用小块做上下文，回答容易碎片化。

### 回溯规则
1. 先检索 child chunks。
2. child 命中后，根据 `parent_id` 找回 parent chunk。
3. 最终 context 以 parent chunk 为主。

### 表结构要求
`document_chunks` 至少包含：
- `id`
- `document_id`
- `user_id`
- `kb_id`
- `parent_id`
- `chunk_type`
- `content`
- `token_count`
- `metadata_json`
- `embedding`

## 3. 向量检索

### 实现建议
- 向量库：`pgvector`
- embedding：OpenAI-compatible 多语言模型
- 检索对象：`child chunks`
- 默认 topK：`30`

### 为什么子块做向量检索
- 子块更容易命中细粒度问题。
- 用户问题通常只命中一小段语义，不需要整章一起参与相似度计算。

## 4. BM25 检索

### 作用
补足纯向量检索对下面几类 query 的弱项：
- 专有名词
- 函数名 / 类名
- 文件编号
- 中英混合缩写
- 关键词非常短的搜索

### 实现建议
- 每个 `kb_id` 建一个 BM25 索引。
- 检索对象同样是 `child chunks`。
- 默认 topK：`30`

## 5. Hybrid Retrieval

### 推荐策略
- 两路召回：
  - vector top30
  - BM25 top30
- 融合算法：
  - `RRF (Reciprocal Rank Fusion)`
- 融合后保留：
  - top20

### 为什么不用简单分数加权
- 向量分数和 BM25 分数尺度天然不同。
- 简单加权要额外做归一化，易受数据分布影响。
- RRF 更稳，更适合练手项目和多源召回融合。

## 6. Rerank

### 推荐模型
- `BAAI/bge-reranker-v2-m3`

### 流程
1. 对 fused top20 做交叉编码重排。
2. 保留 rerank top8 子块。

### 为什么需要 rerank
- vector / BM25 是召回层。
- reranker 是精排层。
- 它更擅长判断“这段文本是否真的在回答当前问题”。

## 7. Rerank 后上下文截断

### 三段式策略
1. `TopK`
   - rerank 后保留 top8 child chunks
2. `MMR`
   - 按 `parent_id` 聚合后，用 `MMR(lambda=0.65)` 选 `4 ~ 6` 个 parent chunks
3. `Token Budget`
   - 检索上下文预算硬上限 `2400 tokens`

### 为什么不能只做 TopK
- TopK 容易全部来自同一文档或同一章节。
- MMR 可以降低重复内容，提高信息覆盖面。
- Token Budget 是真实工程必须有的边界，避免 prompt 无限膨胀。

## Context Engineering 设计

## Prompt 组成
最终 prompt 按下面顺序拼装：

1. `System Prompt`
2. `Chat History Summary + recent turns`
3. `Long-term Memory Summary`
4. `Retrieved Context`
5. `User Query`
6. `Output Contract`

## 建议预算

| 部分 | 预算 |
| --- | --- |
| System Prompt | 600 |
| History | 1200 |
| Memory | 800 |
| Retrieved Context | 2400 |
| User Query + Tool Observation | 1000 |

## System Prompt 设计要求
- 角色：知识库助手
- 原则：优先使用证据
- 证据不足：必须承认不足
- 输出要求：尽量结构化
- 引用规则：给出文件名和页码
- Tool 使用：必要时才能调用

## Prompt 示例
```text
You are ContextPilot, a knowledge workspace assistant.

Rules:
1. Prefer retrieved evidence over guesswork.
2. If the knowledge base is insufficient, say so explicitly.
3. When using sources, cite filename and page if available.
4. Keep the answer concise first, then explain.

[Long-term Memory]
- The user prefers conclusion-first answers.
- The user is building a study project for LangChain, RAG, Agent, and Memory.

[Recent Conversation]
- User asked about Parent Document Retrieval and tutorial-style documents.

[Retrieved Context]
[langchain-notes.md | page 12 | rerank=0.96]
Parent Document Retrieval uses small child chunks for recall and larger parent chunks for final context.

[tutorial-guide.pdf | page 21 | rerank=0.92]
Tutorial content often requires surrounding section order to preserve explanations and steps.

[User Query]
Parent Document Retrieval 为什么更适合教程型文档？

[Output Contract]
- First give a short conclusion.
- Then explain the reason in 2 to 4 bullet points.
- Add a final line listing citations.
```

## Agent 设计

## 1. Agent 形态
- 使用 `create_agent`
- 单 Agent，多工具
- 不做多 Agent 协作

原因：
- 对练手项目来说，单 Agent 足够展示工具调用、context injection、memory recall。
- 多 Agent 会引入额外编排复杂度，但收益不明显。

## 2. Tool 列表

| Tool | 用途 | 何时调用 |
| --- | --- | --- |
| `rag_search` | 知识库检索 | 用户问题依赖文档证据 |
| `memory_recall` | 召回长期记忆 | 需要用户偏好、长期目标、背景事实 |
| `save_memory` | 写入长期记忆 | 用户显式表达偏好或稳定事实 |
| `web_search` | 外部搜索 | 知识库不足且 `allow_web=true` |
| `list_documents` | 查询文档元数据 | 用户问“库里有哪些文档” |

## 3. Agent 推理流程
```text
User Query
  -> 判断是否需要 knowledge evidence
  -> 判断是否需要 recall memory
  -> 决定是否调用 tool
  -> 获取 tool observation
  -> 汇总 context
  -> 输出 final answer
  -> 触发 memory extraction
```

## 4. Tool 调用策略
- 默认总是允许 `rag_search` 和 `memory_recall`。
- `web_search` 只有 `allow_web=true` 时才开放。
- 单轮最多允许 `3` 次 tool calls，避免循环调用。

## Memory 设计

## 1. Short-term Memory
- 保存在会话消息历史中。
- 建议使用 LangGraph state + messages。
- 历史过长时用 `SummarizationMiddleware` 压缩。

### 历史压缩规则
- 保留最近 `12` 条消息原文。
- 更早历史压缩成 summary block。

## 2. Checkpoint
- 一个 `session_id` 对应一个 `thread_id`。
- 用 Postgres 持久化 checkpoint。
- 作用：
  - 页面刷新后恢复会话
  - 工具调用后可回放执行状态
  - Debug 时可复盘一轮完整推理

## 3. Long-term Store
- 存在 `memories` 表，或 LangGraph `PostgresStore`。
- 每条 memory 建议带：
  - `category`
  - `summary`
  - `content`
  - `source_session_id`
  - `pinned`
  - `embedding`

## 4. 记忆写入规则
只有下面四类内容允许写入：
- 用户偏好
- 长期任务
- 稳定背景事实
- 用户显式要求“记住”

不要写入：
- 一次性问题
- 临时调试状态
- 可以从当前消息直接看出的重复信息

## 5. 记忆召回规则
1. 根据当前 query 做 semantic search。
2. top5 memories 参与召回。
3. 压缩为最多 `800 tokens` 的 memory block。
4. 注入到最终 prompt。

## 6. 去重与冲突
- 相似内容不要盲目追加，优先 upsert。
- 如果新偏好与旧偏好冲突：
  - 新偏好覆盖旧偏好
  - 保留 `updated_at`
- pinned memory 优先级最高。

## 三条完整功能示例

## 示例 1：知识库问答

### 输入
```json
{
  "user_id": "demo-user",
  "session_id": "sess-1",
  "kb_id": "kb-langchain",
  "message": "Parent Document Retrieval 为什么更适合教程型文档？",
  "allow_web": false,
  "debug": true
}
```

### Tool 行为
```text
memory_recall -> 命中“回答尽量先给结论再解释”
rag_search -> vector top30 + bm25 top30 + RRF top20 + rerank top8
```

### 期望回答形态
```text
结论：它更适合教程型文档，因为它既保留局部命中精度，又保留章节级上下文。

解释：
1. 教程类文本依赖步骤顺序和上下文衔接。
2. 子块召回能命中问题相关的局部内容。
3. 父块回溯能把解释、前提和例子一起带回 prompt。
4. 这样回答不容易变成脱离上下文的碎片。

引用：langchain-notes.md p12；tutorial-guide.pdf p21
```

## 示例 2：记住我的偏好

### 用户输入
```text
以后回答尽量先给结论再解释。
```

### 处理流程
```text
LLM / extractor 判断为 preference
  -> save_memory
  -> memories upsert
  -> 下一轮对话 recall 生效
```

### 建议存储内容
```json
{
  "category": "preference",
  "summary": "回答尽量先给结论再解释",
  "content": "用户偏好结构化输出，先给结论，再展开解释。",
  "pinned": false
}
```

## 示例 3：证据不足时的保守回答

### 用户输入
```text
这个知识库里有没有提到 LangGraph 的 distributed scheduler？
```

### 检索结果
- vector 命中弱
- BM25 无明确命中
- rerank 后最高分仍低于阈值

### 输出策略
```text
当前知识库里没有足够证据支持这个结论。
如果你愿意，我可以：
1. 先列出知识库中与 LangGraph 相关的文档；
2. 或在允许外部搜索后再补充结果。
```

原因：
- 这是工程上比“猜一个答案”更可信的行为。
- 也更符合面试中对 RAG 系统“保守性”的预期。

## 调试面板与后端返回字段映射

| 前端面板 | 后端字段 |
| --- | --- |
| Vector Hits | `vector_hits` |
| BM25 | `bm25_hits` |
| RRF | `rrf_hits` |
| Rerank | `rerank_hits` |
| Final Context | `final_context` |
| Prompt Budget | `prompt_budget` |
| Tool Trace | `tool_trace` 或 `tool_call` 事件 |

## 实施优先级
1. 先实现 `rag_search` 的 mock 版本，打通接口与 UI。
2. 再实现真实的 Parent/Child chunking。
3. 再实现 vector + BM25 + RRF。
4. 再接 reranker。
5. 最后接 LangGraph persistence 和 long-term memory。

## 当前骨架说明
- 当前仓库里，Agent、RAG、Memory 模块是“类和边界已建好”的状态。
- 真实开发时，优先替换内部逻辑，不要改动模块名字和职责。
- 如果你要引入新的中间件或额外 tool，先同步：
  - [backend/app/agent](/g:/学习空间夸克/练手项目/RAG_PRO/backend/app/agent)
  - [backend/app/rag](/g:/学习空间夸克/练手项目/RAG_PRO/backend/app/rag)
  - [docs/02-backend-api.md](/g:/学习空间夸克/练手项目/RAG_PRO/docs/02-backend-api.md)

## 参考资料
- LangChain Agents: https://docs.langchain.com/oss/python/langchain/agents
- LangChain Context Engineering: https://docs.langchain.com/oss/python/langchain/context-engineering
- LangGraph Memory: https://docs.langchain.com/oss/python/langgraph/add-memory
- LangGraph Persistence: https://docs.langchain.com/oss/python/langgraph/persistence
- BM25 Retriever: https://docs.langchain.com/oss/python/integrations/retrievers/bm25
- ParentDocumentRetriever API: https://api.python.langchain.com/en/latest/langchain/retrievers/langchain.retrievers.parent_document_retriever.ParentDocumentRetriever.html
