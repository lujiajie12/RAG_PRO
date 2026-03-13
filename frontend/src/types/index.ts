export interface SessionItem {
  id: string;
  userId: string;
  kbId: string;
  title: string;
  summary: string;
  updatedAt: string;
  tags: string[];
  modelName: string;
  retrievalMode: "hybrid" | "vector" | "bm25";
  webSearchEnabled: boolean;
}

export interface CitationItem {
  documentId: string;
  chunkId: string;
  fileName: string;
  page?: number;
  rerankScore?: number;
}

export interface ToolTraceItem {
  name: string;
  status: "planned" | "running" | "completed" | "failed";
  summary: string;
}

export interface MessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  citations: CitationItem[];
  toolTrace: ToolTraceItem[];
  streaming?: boolean;
  failed?: boolean;
}

export interface RetrievalHit {
  id: string;
  fileName: string;
  score: number;
  preview: string;
  tag: string;
}

export interface RetrievalPanelSection {
  key: string;
  title: string;
  hits: RetrievalHit[];
}

export interface PromptBudgetSummary {
  used: number;
  budget: number;
  history: number;
  memory: number;
  userQuery: number;
}

export interface KnowledgeDocument {
  id: string;
  kbId: string;
  name: string;
  type: string;
  chunkCount: number;
  parentCount: number;
  childCount: number;
  status: "indexed" | "processing" | "failed";
  indexedAt: string;
  embeddingStatus: string;
  bm25Status: string;
}

export interface MemoryItem {
  id: string;
  category: "preference" | "long_term_task" | "background_fact" | "manual_note";
  summary: string;
  detail: string;
  score: number;
  sourceSession: string;
  createdAt: string;
  updatedAt: string;
  pinned: boolean;
}
