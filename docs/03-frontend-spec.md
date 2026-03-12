# 03 Frontend Spec

## 你开发这一章时要先完成什么
- 先看前端入口 [frontend/src/main.ts](/g:/学习空间夸克/练手项目/RAG_PRO/frontend/src/main.ts)。
- 先看全局布局 [frontend/src/components/layout/AppShell.vue](/g:/学习空间夸克/练手项目/RAG_PRO/frontend/src/components/layout/AppShell.vue)。
- 先看 mock 数据形状 [frontend/src/mocks/workspace.ts](/g:/学习空间夸克/练手项目/RAG_PRO/frontend/src/mocks/workspace.ts) 和类型定义 [frontend/src/types/index.ts](/g:/学习空间夸克/练手项目/RAG_PRO/frontend/src/types/index.ts)。
- 先看页面路由 [frontend/src/router/index.ts](/g:/学习空间夸克/练手项目/RAG_PRO/frontend/src/router/index.ts)。

## 设计目标
- 像一个“知识工作台”，不是普通 CRUD 后台。
- 页面信息密度高，但不压迫。
- 聊天、知识库、Memory、调试面板是同一套视觉语言。
- 保持适合面试演示的观感：专业、清晰、有工程感。

## 技术栈
- `Vue 3`
- `Vite`
- `TypeScript`
- `Vue Router`
- `Pinia`
- `Naive UI`
- `UnoCSS`

## 路由结构

| 路由 | 页面 | 作用 |
| --- | --- | --- |
| `/workspace` | Chat Workspace | 主聊天与调试工作区 |
| `/knowledge` | Knowledge Base | 文档上传、状态、删除、重建索引 |
| `/memory` | Memory Studio | 长期记忆查看、筛选、删除、手动添加 |

## 全局布局
页面采用两层结构：

```text
AppShell
  ├─ Left Rail
  │   ├─ Brand
  │   ├─ Route Nav
  │   └─ Runtime Status
  └─ Main Area
      ├─ Header
      └─ Current Page
```

### Left Rail
- 固定宽度 `92px`。
- 展示品牌、主导航、在线状态。
- 移动端收敛为顶部导航。

### Header
- 展示当前产品标题和技术栈摘要。
- 保持“工作台”感，不使用营销化 banner。

## 视觉 Token

### 字体
- 主字体：`IBM Plex Sans + Noto Sans SC`
- 等宽字体：`JetBrains Mono`

### 颜色

| Token | 值 | 用途 |
| --- | --- | --- |
| `--cp-bg` | `#eef3f4` | 页面底色 |
| `--cp-text` | `#152433` | 主文本 |
| `--cp-text-muted` | `#617487` | 次文本 |
| `--cp-accent` | `#0f766e` | 主强调色 |
| `--cp-secondary` | `#335cff` | 次强调色 |
| `--cp-danger` | `#db4f5f` | 错误或删除操作 |

### 质感
- 背景用浅色渐变 + 细网格纹理。
- 卡片用半透明白底 + 弱模糊，不做重磨砂。
- 圆角统一偏大：`18px ~ 30px`。
- 阴影柔和，避免传统后台大黑影。

## 页面规格

## Chat Workspace

### 页面目标
- 这是主操作台，应该一眼看到：
  - 当前会话
  - 当前知识库
  - 当前模型与检索模式
  - 消息流
  - 调试面板

### 页面布局
```text
Chat Workspace
  ├─ SessionRail (左)
  ├─ ChatStage (中)
  │   ├─ Toolbar
  │   ├─ Signal Strip
  │   ├─ Message Flow
  │   └─ Composer
  └─ DebugPanel (右)
```

### 组件树
```text
ChatWorkspaceView
  ├─ SessionRail
  ├─ MessageBubble[]
  └─ DebugPanel
```

### Toolbar 字段

| 控件 | 作用 |
| --- | --- |
| 模型选择 `NSelect` | 选择 chat model |
| 检索模式 `NSelect` | `Hybrid Retrieval` / `Vector Only` / `BM25 Only` |
| `Web Search` 开关 | 是否允许 Agent 开外部搜索工具 |

### Signal Strip 字段
- `Active KB`
- `Memory State`
- `Context Budget`

### Message Flow
- 用户消息靠右，AI 消息靠左。
- AI 消息支持：
  - citation chips
  - tool trace cards
  - streaming 状态

### Composer
- 多行文本输入。
- 上传附件按钮。
- 发送按钮。
- 标签提示区展示系统能力：`RAG ready`、`Agent tool calling`、`Long-term memory`。

### Debug Panel
- 默认展开。
- 支持收起。
- 使用 `segment tabs` 展示：
  - `Vector Hits`
  - `BM25`
  - `RRF`
  - `Rerank`
  - `Final Context`
  - `Prompt Budget`
  - `Tool Trace`

### Chat 页面状态流
```text
页面加载
  -> 拉取 sessions
  -> 默认选中一个 session
  -> 展示 mock / real messages
  -> 用户发送消息
  -> 调 /api/chat/stream
  -> token 追加到 assistant message
  -> tool_call 更新 trace
  -> retrieval_debug 更新右侧 panel
  -> final_answer 结束 loading
```

### Chat 页面空态
- 没有会话时显示：
  - 一句欢迎语
  - 推荐问题
  - 最近知识库
- 没有关联知识库时，保留聊天，但显式提示“回答可能不含知识库证据”。

## Knowledge Base

### 页面目标
- 上传文档
- 看处理进度
- 看索引状态
- 查父/子块数量
- 删除文档或重建索引

### 页面布局
```text
Knowledge Base
  ├─ Upload Card
  ├─ Document Grid
  └─ Detail Drawer
```

### Upload Card 内容
- 标题、副标题
- 拖拽上传区
- 支持格式说明
- 大小限制
- 上传按钮

### Document Card 字段

| 字段 | 说明 |
| --- | --- |
| `name` | 文档名 |
| `type` | 文件后缀 |
| `status` | `indexed / processing / failed` |
| `chunkCount` | chunk 总数 |
| `parentCount` | 父块数 |
| `childCount` | 子块数 |
| `indexedAt` | 最近索引时间 |

### Detail Drawer 字段
- `Embedding status`
- `BM25 status`
- `Parent / Child`
- `Chunk count`
- 操作按钮：
  - `重建索引`
  - `删除文档`

### 上传交互
1. 用户选择文件。
2. 调 `POST /api/upload`。
3. 卡片立即出现，状态先是 `uploaded` / `processing`。
4. 前端轮询或刷新 `/api/documents` 更新状态。

## Memory Studio

### 页面目标
- 显示系统已经记住了什么
- 让用户知道这些记忆会如何影响 prompt
- 允许人工清理或固定记忆

### 页面布局
```text
Memory Studio
  ├─ Header
  │   ├─ Title
  │   └─ Category Filters
  └─ Memory Grid
```

### Category Filters
- 全部
- 用户偏好
- 长期任务
- 背景事实
- 手动固定

### Memory Card 字段

| 字段 | 说明 |
| --- | --- |
| `summary` | 短摘要 |
| `detail` | 完整内容 |
| `score` | semantic recall score |
| `sourceSession` | 来源会话 |
| `createdAt` | 创建时间 |
| `updatedAt` | 更新时间 |
| `pinned` | 是否固定 |

### 交互动作
- 查看注入详情
- 删除
- 后续可扩展：
  - 编辑
  - 重新 embedding
  - 手动置顶

## 状态管理

### Pinia Store
当前使用 [frontend/src/stores/workspace.ts](/g:/学习空间夸克/练手项目/RAG_PRO/frontend/src/stores/workspace.ts) 管理：

| 状态 | 作用 |
| --- | --- |
| `selectedSessionId` | 当前会话 |
| `selectedKnowledgeBase` | 当前知识库 |
| `allowWebSearch` | 是否允许 Web Search |
| `debugPanelCollapsed` | 调试面板收起状态 |
| `activeRetrievalTab` | 当前调试 tab |

### 后续建议拆分
- `sessionStore`
- `chatStore`
- `knowledgeStore`
- `memoryStore`
- `debugStore`

这样方便真实 API 接入后做独立 loading/error 状态。

## API 对接规则

| 页面区域 | 接口 |
| --- | --- |
| SessionRail | `GET /api/sessions` |
| Chat 发送 | `POST /api/chat/stream` |
| KB 上传 | `POST /api/upload` |
| KB 列表 | `GET /api/documents` |
| KB 删除 | `DELETE /api/documents/{document_id}` |
| Memory 列表 | `GET /api/memory` |
| Memory 删除 | `DELETE /api/memory/{memory_id}` |
| Debug 单独调试 | `POST /api/retrieval/debug` |

## 响应式规则

### 1440px 桌面
- Chat 页保持三栏。
- Knowledge 和 Memory 使用两到三列卡片。

### 1180px 以下
- Chat 页从三栏降为单列。
- 调试面板移到消息区下方。

### 390px 移动端
- Rail 改为顶部导航。
- Header 信息压缩成一列。
- 卡片 padding 收缩。
- Chat toolbar 全部纵向堆叠。

## 交互与动效
- 卡片 hover 仅做轻微抬升和边框高亮。
- 新消息流入时建议做 `fade + translateY(6px)`。
- Debug tab 切换不需要花哨动画，保证内容切换干净。

## 可用性要求
- 消息、citation、tool trace 的层级要一眼可辨。
- 同一信息不要在多个区域重复堆砌。
- 调试面板字段名必须和后端 payload 一致，避免联调时需要映射翻译。

## 当前骨架说明
- 当前前端以 mock 数据驱动，但所有字段形状已经与后端 DTO 对齐。
- 你后续接真实接口时，优先替换数据源，不要先重做组件结构。
- 如果接口字段发生变化，先同步：
  - [frontend/src/types/index.ts](/g:/学习空间夸克/练手项目/RAG_PRO/frontend/src/types/index.ts)
  - [frontend/src/mocks/workspace.ts](/g:/学习空间夸克/练手项目/RAG_PRO/frontend/src/mocks/workspace.ts)
  - 本文档

## 验收清单
- 三个页面能清楚表达产品能力，不像普通管理后台。
- Chat 页面能同时容纳消息流、citation、tool trace、retrieval debug。
- Knowledge Base 页面能让人理解“上传后系统做了什么”。
- Memory 页面能让人理解“记忆为什么被写入、如何被召回”。
- 桌面和移动端都不出现布局崩坏。
