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
    title: "LangChain 学习笔记整理",
    kbId: "kb-langchain",
    updatedAt: "2 分钟前",
    summary: "Parent Document Retrieval 与 Hybrid Retrieval 设计",
  },
  {
    id: "sess-2",
    title: "Prompt 工程实验",
    kbId: "kb-prompts",
    updatedAt: "今天 09:14",
    summary: "总结式历史压缩与 Token Budget",
  },
  {
    id: "sess-3",
    title: "RAG 调优记录",
    kbId: "kb-rag",
    updatedAt: "昨天",
    summary: "BM25、RRF、rerank 对比",
  },
];

export const messages: MessageItem[] = [
  {
    id: "msg-1",
    role: "user",
    content: "Parent Document Retrieval 为什么更适合教程型文档？",
    timestamp: "10:42",
  },
  {
    id: "msg-2",
    role: "assistant",
    content:
      "它用子块做精确召回，用父块恢复章节语义，所以既能命中局部关键词，也不会把教程拆成失去上下文的碎片。对于步骤型、解释型内容，这种回溯比纯 chunk 拼接更稳定。",
    timestamp: "10:42",
    citations: [
      { fileName: "langchain-notes.md", page: 12, rerankScore: 0.96 },
      { fileName: "tutorial-guide.pdf", page: 21, rerankScore: 0.92 },
    ],
    toolTrace: [{ name: "rag_search", status: "completed", summary: "Hybrid Retrieval + rerank 命中 2 个父块" }],
  },
];

export const retrievalSections: RetrievalPanelSection[] = [
  {
    key: "vector",
    title: "Vector Hits",
    hits: [
      { id: "c-101", fileName: "langchain-notes.md", score: 0.88, preview: "Parent/child retrieval returns the larger semantic unit.", tag: "p-11" },
      { id: "c-109", fileName: "rag-handbook.pdf", score: 0.84, preview: "Children are used for recall while parents are used for context.", tag: "p-22" },
    ],
  },
  {
    key: "bm25",
    title: "BM25",
    hits: [
      { id: "c-203", fileName: "tutorial-guide.pdf", score: 15.2, preview: "教程型文档 often requires keeping headings and sequence.", tag: "p-31" },
      { id: "c-101", fileName: "langchain-notes.md", score: 13.8, preview: "Parent Document Retrieval is strong for notebooks and manuals.", tag: "p-11" },
    ],
  },
  {
    key: "rrf",
    title: "RRF",
    hits: [
      { id: "c-101", fileName: "langchain-notes.md", score: 0.93, preview: "RRF balances lexical and semantic recall.", tag: "rank-1" },
      { id: "c-203", fileName: "tutorial-guide.pdf", score: 0.91, preview: "The fused ranking keeps exact terms from BM25.", tag: "rank-2" },
    ],
  },
  {
    key: "rerank",
    title: "Rerank",
    hits: [
      { id: "c-101", fileName: "langchain-notes.md", score: 0.96, preview: "The reranker prioritizes explanatory chunks answering the user directly.", tag: "top-1" },
      { id: "c-203", fileName: "tutorial-guide.pdf", score: 0.92, preview: "The reranker keeps supporting tutorial context for the answer.", tag: "top-2" },
    ],
  },
  {
    key: "context",
    title: "Final Context",
    hits: [
      { id: "p-11", fileName: "langchain-notes.md", score: 920, preview: "Context window retains section title, explanation, and example usage.", tag: "730 tokens" },
      { id: "p-31", fileName: "tutorial-guide.pdf", score: 810, preview: "MMR keeps a different source to avoid repeated phrasing.", tag: "650 tokens" },
    ],
  },
  {
    key: "budget",
    title: "Prompt Budget",
    hits: [
      { id: "budget-1", fileName: "System Prompt", score: 600, preview: "Role, policy, citation rules, fallback behavior.", tag: "reserved" },
      { id: "budget-2", fileName: "Memory", score: 800, preview: "Conclusion-first response preference recalled from long-term memory.", tag: "reserved" },
    ],
  },
  {
    key: "tools",
    title: "Tool Trace",
    hits: [
      { id: "tool-1", fileName: "rag_search", score: 1, preview: "Executed hybrid retrieval and rerank with debug enabled.", tag: "completed" },
      { id: "tool-2", fileName: "memory_recall", score: 1, preview: "Recalled one response-style preference for this user.", tag: "completed" },
    ],
  },
];

export const knowledgeDocuments: KnowledgeDocument[] = [
  {
    id: "doc-1",
    name: "langchain-notes.md",
    type: "md",
    chunkCount: 112,
    parentCount: 18,
    childCount: 94,
    status: "indexed",
    indexedAt: "2026-03-12 10:11",
    embeddingStatus: "ready",
    bm25Status: "ready",
  },
  {
    id: "doc-2",
    name: "rag-handbook.pdf",
    type: "pdf",
    chunkCount: 186,
    parentCount: 28,
    childCount: 158,
    status: "processing",
    indexedAt: "2026-03-12 09:48",
    embeddingStatus: "running",
    bm25Status: "queued",
  },
  {
    id: "doc-3",
    name: "agent-memory-design.docx",
    type: "docx",
    chunkCount: 87,
    parentCount: 14,
    childCount: 73,
    status: "indexed",
    indexedAt: "2026-03-11 18:22",
    embeddingStatus: "ready",
    bm25Status: "ready",
  },
];

export const memories: MemoryItem[] = [
  {
    id: "mem-1",
    category: "preference",
    summary: "回答尽量先给结论再解释",
    detail: "用户偏好结构化输出，先总结核心结论，再展开原理与步骤。",
    score: 0.97,
    sourceSession: "LangChain 学习笔记整理",
    createdAt: "2026-03-11 15:30",
    updatedAt: "2026-03-12 09:10",
    pinned: true,
  },
  {
    id: "mem-2",
    category: "long_term_task",
    summary: "正在整理 RAG / Agent 工程化学习路线",
    detail: "后续问题可以偏向工程实现、模块边界与调试思路。",
    score: 0.84,
    sourceSession: "RAG 调优记录",
    createdAt: "2026-03-10 20:10",
    updatedAt: "2026-03-12 08:50",
    pinned: false,
  },
  {
    id: "mem-3",
    category: "manual_note",
    summary: "演示时优先展示 retrieval debug 面板",
    detail: "用于面试演示，突出 Hybrid Retrieval、RRF、rerank 分数和 final context。",
    score: 0.76,
    sourceSession: "手动添加",
    createdAt: "2026-03-12 08:00",
    updatedAt: "2026-03-12 08:00",
    pinned: true,
  },
];
