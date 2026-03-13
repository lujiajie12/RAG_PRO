import { apiClient, getJSON, postEventStream, sendForm, sendJSON, type SSEHandlers } from "@/api/client";

export interface SessionDTO {
  id: string;
  user_id: string;
  kb_id: string | null;
  title: string;
  summary: string | null;
  thread_id: string;
  tags: string[];
  model_name: "qwen-plus" | "qwen-max" | "qwen-turbo" | string;
  retrieval_mode: "hybrid" | "vector" | "bm25";
  web_search_enabled: boolean;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface MessageDTO {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  citations: CitationDTO[];
  tool_trace: ToolTraceDTO[];
  created_at: string;
  updated_at: string;
}

export interface CitationDTO {
  document_id: string;
  file_name: string;
  page?: number | null;
  chunk_id: string;
  rerank_score?: number | null;
}

export interface ToolTraceDTO {
  name: string;
  status: "planned" | "running" | "completed" | "failed";
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
}

export interface DocumentSummaryDTO {
  id: string;
  user_id: string;
  kb_id: string;
  file_name: string;
  file_type: string;
  status: string;
  parsed_type: string;
  chunk_count: number;
  parent_count: number;
  child_count: number;
  indexed_at: string | null;
  embedding_status: string;
  bm25_status: string;
  created_at: string;
  updated_at: string;
}

export interface MemoryDTO {
  id: string;
  user_id: string;
  category: "preference" | "long_term_task" | "background_fact" | "manual_note";
  summary: string;
  content: string;
  source_session_id: string | null;
  pinned: boolean;
  score: number | null;
  created_at: string;
  updated_at: string;
}

export interface RetrievalHitDTO {
  chunk_id: string;
  file_name: string;
  content_preview: string;
  score: number;
  parent_id?: string | null;
  metadata: Record<string, unknown>;
}

export interface RetrievalDebugDTO {
  query: string;
  vector_hits: RetrievalHitDTO[];
  bm25_hits: RetrievalHitDTO[];
  rrf_hits: RetrievalHitDTO[];
  rerank_hits: RetrievalHitDTO[];
  final_context: RetrievalHitDTO[];
  prompt_budget: {
    system: number;
    history: number;
    memory: number;
    retrieved_context: number;
    user_query: number;
    retrieved_context_budget: number;
  };
}

export interface ChatAnswerDTO {
  session_id: string;
  answer: string;
  citations: CitationDTO[];
  tool_trace: ToolTraceDTO[];
}

export interface CreateSessionPayload {
  user_id: string;
  kb_id?: string | null;
  title?: string | null;
  tags?: string[];
  model_name?: string | null;
  retrieval_mode?: "hybrid" | "vector" | "bm25" | null;
  web_search_enabled?: boolean;
}

export interface UpdateSessionPayload extends CreateSessionPayload {}

export interface ChatStreamPayload {
  user_id: string;
  session_id: string;
  message: string;
  attachment_ids?: string[];
  debug?: boolean;
}

function buildQuery(params: Record<string, string | number | null | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") {
      continue;
    }
    search.set(key, String(value));
  }
  const suffix = search.toString();
  return suffix ? `?${suffix}` : "";
}

export function listSessions(params: {
  userId: string;
  q?: string;
  kbId?: string | null;
  tag?: string | null;
  limit?: number;
  offset?: number;
}) {
  return getJSON<SessionDTO[]>(
    `${apiClient.sessions}${buildQuery({
      user_id: params.userId,
      q: params.q,
      kb_id: params.kbId,
      tag: params.tag,
      limit: params.limit,
      offset: params.offset,
    })}`,
  );
}

export function getSession(sessionId: string, userId: string) {
  return getJSON<SessionDTO>(`${apiClient.sessions}/${sessionId}${buildQuery({ user_id: userId })}`);
}

export function createSession(payload: CreateSessionPayload) {
  return sendJSON<SessionDTO>(apiClient.sessions, "POST", payload);
}

export function patchSession(sessionId: string, payload: UpdateSessionPayload) {
  return sendJSON<SessionDTO>(`${apiClient.sessions}/${sessionId}`, "PATCH", payload);
}

export function listSessionMessages(sessionId: string, userId: string) {
  return getJSON<MessageDTO[]>(`${apiClient.sessions}/${sessionId}/messages${buildQuery({ user_id: userId })}`);
}

export function listDocuments(userId: string, kbId: string) {
  return getJSON<DocumentSummaryDTO[]>(
    `${apiClient.documents}${buildQuery({ user_id: userId, kb_id: kbId })}`,
  );
}

export async function uploadDocument(userId: string, kbId: string, file: File) {
  const form = new FormData();
  form.append("user_id", userId);
  form.append("kb_id", kbId);
  form.append("file", file);
  return sendForm<{ document_id: string; kb_id: string; status: string; parsed_type: string; file_name: string; file_type: string }>(
    apiClient.upload,
    "POST",
    form,
  );
}

export function deleteDocument(documentId: string) {
  return sendJSON<void>(`${apiClient.documents}/${documentId}`, "DELETE");
}

export function listMemories(userId: string) {
  return getJSON<MemoryDTO[]>(`${apiClient.memory}${buildQuery({ user_id: userId })}`);
}

export function deleteMemory(memoryId: string) {
  return sendJSON<void>(`${apiClient.memory}/${memoryId}`, "DELETE");
}

export async function uploadChatAttachment(userId: string, sessionId: string, file: File) {
  const form = new FormData();
  form.append("user_id", userId);
  form.append("session_id", sessionId);
  form.append("file", file);
  return sendForm<{
    attachment_id: string;
    session_id: string;
    file_name: string;
    file_type: string;
    mime_type: string;
    size_bytes: number;
    status: string;
  }>(apiClient.chatAttachments, "POST", form);
}

export function streamChat(payload: ChatStreamPayload, handlers: SSEHandlers) {
  return postEventStream(apiClient.chatStream, payload, handlers);
}
