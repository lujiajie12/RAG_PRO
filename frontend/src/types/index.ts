export interface SessionItem {
  id: string;
  title: string;
  kbId: string;
  updatedAt: string;
  summary: string;
}

export interface CitationItem {
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
  citations?: CitationItem[];
  toolTrace?: ToolTraceItem[];
  streaming?: boolean;
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

export interface KnowledgeDocument {
  id: string;
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
