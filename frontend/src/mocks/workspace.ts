import type {
  KnowledgeDocument,
  MemoryItem,
  MessageItem,
  RetrievalPanelSection,
  SessionItem,
} from "@/types";

export const sessions: SessionItem[] = [
  {
    id: "sess-1",
    userId: "demo-user",
    title: "LangChain 学习笔记",
    kbId: "kb-langchain",
    updatedAt: "03-13 10:42",
    summary: "父子检索与混合召回设计说明。",
    tags: ["教程"],
    modelName: "qwen-plus",
    retrievalMode: "hybrid",
    webSearchEnabled: false,
  },
];

export const messages: MessageItem[] = [
  {
    id: "msg-1",
    role: "user",
    content: "为什么父文档检索更适合教程型内容？",
    timestamp: "03-13 10:42",
    citations: [],
    toolTrace: [],
  },
  {
    id: "msg-2",
    role: "assistant",
    content: "它会先召回命中的子块，再回溯更完整的父块上下文，因此更适合解释型、步骤型内容的回答。",
    timestamp: "03-13 10:42",
    citations: [
      {
        documentId: "doc-1",
        chunkId: "chunk-1",
        fileName: "langchain-notes.md",
        page: 12,
        rerankScore: 0.96,
      },
    ],
    toolTrace: [
      {
        name: "rag_search",
        status: "completed",
        summary: "重排后召回了两个父级上下文块。",
      },
    ],
  },
];

export const retrievalSections: RetrievalPanelSection[] = [
  {
    key: "final_context",
    title: "最终上下文",
    hits: [
      {
        id: "chunk-1",
        fileName: "langchain-notes.md",
        score: 0.96,
        preview: "父文档检索会恢复更大的语义单元，使回答时保留完整解释链路。",
        tag: "第12页",
      },
    ],
  },
];

export const knowledgeDocuments: KnowledgeDocument[] = [
  {
    id: "doc-1",
    kbId: "kb-langchain",
    name: "langchain-notes.md",
    type: "md",
    chunkCount: 112,
    parentCount: 18,
    childCount: 94,
    status: "indexed",
    indexedAt: "03-13 10:11",
    embeddingStatus: "ready",
    bm25Status: "ready",
  },
];

export const memories: MemoryItem[] = [
  {
    id: "mem-1",
    category: "preference",
    summary: "偏好先给结论再解释。",
    detail: "回答时先给出结论，再补充原因和步骤说明。",
    score: 0.97,
    sourceSession: "LangChain 学习笔记",
    createdAt: "03-12 15:30",
    updatedAt: "03-13 09:10",
    pinned: true,
  },
];
