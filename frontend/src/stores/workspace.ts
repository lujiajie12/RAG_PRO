import { computed, ref } from "vue";
import { defineStore } from "pinia";

import { APIClientError } from "@/api/client";
import {
  createSession,
  deleteDocument,
  deleteMemory,
  listDocuments,
  listMemories,
  listSessionMessages,
  listSessions,
  patchSession,
  streamChat,
  uploadChatAttachment,
  uploadDocument,
  type ChatAnswerDTO,
  type CitationDTO,
  type DocumentSummaryDTO,
  type MemoryDTO,
  type MessageDTO,
  type RetrievalDebugDTO,
  type RetrievalHitDTO,
  type SessionDTO,
  type ToolTraceDTO,
} from "@/api/workspace";
import type {
  CitationItem,
  KnowledgeDocument,
  MemoryItem,
  MessageItem,
  PromptBudgetSummary,
  RetrievalHit,
  RetrievalPanelSection,
  SessionItem,
  ToolTraceItem,
} from "@/types";

const DEFAULT_USER_ID = "demo-user";
const DEFAULT_KB_ID = "kb-langchain";
const DEFAULT_MODEL = "qwen-plus";

function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "刚刚";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function normalizeSession(dto: SessionDTO): SessionItem {
  return {
    id: dto.id,
    userId: dto.user_id,
    kbId: dto.kb_id ?? DEFAULT_KB_ID,
    title: dto.title,
    summary: dto.summary ?? "暂无摘要",
    updatedAt: formatDateTime(dto.updated_at),
    tags: dto.tags,
    modelName: dto.model_name,
    retrievalMode: dto.retrieval_mode,
    webSearchEnabled: dto.web_search_enabled,
  };
}

function normalizeCitation(dto: CitationDTO): CitationItem {
  return {
    documentId: dto.document_id,
    chunkId: dto.chunk_id,
    fileName: dto.file_name,
    page: dto.page ?? undefined,
    rerankScore: dto.rerank_score ?? undefined,
  };
}

function summarizeToolTrace(trace: ToolTraceDTO): string {
  const output = trace.output ?? {};

  if (trace.name === "rag_search") {
    const finalContext = Number(output.final_context ?? 0);
    const vectorHits = Number(output.vector_hits ?? 0);
    const bm25Hits = Number(output.bm25_hits ?? 0);
    return `已组装 ${finalContext} 个上下文块（向量 ${vectorHits} / BM25 ${bm25Hits}）。`;
  }

  if (Array.isArray(output.documents)) {
    return `共返回 ${output.documents.length} 份文档。`;
  }

  if (typeof output.answer === "string" && output.answer) {
    return output.answer;
  }

  const compact = JSON.stringify(output);
  if (compact && compact !== "{}") {
    return compact.length > 88 ? `${compact.slice(0, 88)}...` : compact;
  }

  if (trace.status === "completed") {
    return "已完成。";
  }
  const statusLabels: Record<ToolTraceDTO["status"], string> = {
    planned: "待执行",
    running: "执行中",
    completed: "已完成",
    failed: "失败",
  };
  return `${statusLabels[trace.status] ?? trace.status}。`;
}

function normalizeToolTrace(dto: ToolTraceDTO): ToolTraceItem {
  return {
    name: dto.name,
    status: dto.status,
    summary: summarizeToolTrace(dto),
  };
}

function normalizeMessage(dto: MessageDTO): MessageItem {
  return {
    id: dto.id,
    role: dto.role,
    content: dto.content,
    timestamp: formatDateTime(dto.created_at),
    citations: dto.citations.map(normalizeCitation),
    toolTrace: dto.tool_trace.map(normalizeToolTrace),
    streaming: false,
  };
}

function normalizeDocumentStatus(status: string): KnowledgeDocument["status"] {
  if (status === "indexed") {
    return "indexed";
  }
  if (status === "failed") {
    return "failed";
  }
  return "processing";
}

function normalizeDocument(dto: DocumentSummaryDTO): KnowledgeDocument {
  return {
    id: dto.id,
    kbId: dto.kb_id,
    name: dto.file_name,
    type: dto.file_type,
    chunkCount: dto.chunk_count,
    parentCount: dto.parent_count,
    childCount: dto.child_count,
    status: normalizeDocumentStatus(dto.status),
    indexedAt: formatDateTime(dto.indexed_at ?? dto.updated_at),
    embeddingStatus: dto.embedding_status,
    bm25Status: dto.bm25_status,
  };
}

function normalizeMemory(dto: MemoryDTO): MemoryItem {
  return {
    id: dto.id,
    category: dto.category,
    summary: dto.summary,
    detail: dto.content,
    score: dto.score ?? 0,
    sourceSession: dto.source_session_id ?? "手动添加",
    createdAt: formatDateTime(dto.created_at),
    updatedAt: formatDateTime(dto.updated_at),
    pinned: dto.pinned,
  };
}

function describeRetrievalHit(hit: RetrievalHitDTO): RetrievalHit {
  const metadata = hit.metadata ?? {};
  const sectionPath = Array.isArray(metadata.section_path) ? metadata.section_path : [];
  const locators = typeof metadata.source_locators === "object" && metadata.source_locators !== null
    ? (metadata.source_locators as Record<string, unknown>)
    : {};
  const pageNumber = typeof locators.page_number === "number"
    ? locators.page_number
    : Array.isArray(locators.page_number) && typeof locators.page_number[0] === "number"
      ? locators.page_number[0]
      : null;
  const lastSection = sectionPath.length ? sectionPath[sectionPath.length - 1] : null;
  const tag = pageNumber
    ? `第${pageNumber}页`
    : typeof lastSection === "string"
      ? lastSection
      : typeof metadata.chunk_type === "string"
        ? metadata.chunk_type === "child"
          ? "子块"
          : metadata.chunk_type === "parent"
            ? "父块"
            : String(metadata.chunk_type)
        : hit.parent_id
          ? "子块"
          : "文本块";

  return {
    id: hit.chunk_id,
    fileName: hit.file_name,
    score: Number(hit.score.toFixed(3)),
    preview: hit.content_preview,
    tag,
  };
}

function normalizeRetrievalSections(debugPayload: RetrievalDebugDTO): RetrievalPanelSection[] {
  return [
    { key: "final_context", title: "最终上下文", hits: debugPayload.final_context.map(describeRetrievalHit) },
    { key: "rerank_hits", title: "重排结果", hits: debugPayload.rerank_hits.map(describeRetrievalHit) },
    { key: "vector_hits", title: "向量召回", hits: debugPayload.vector_hits.map(describeRetrievalHit) },
    { key: "bm25_hits", title: "BM25", hits: debugPayload.bm25_hits.map(describeRetrievalHit) },
    { key: "rrf_hits", title: "RRF 融合", hits: debugPayload.rrf_hits.map(describeRetrievalHit) },
  ].filter((section) => section.hits.length > 0);
}

function normalizePromptBudget(debugPayload: RetrievalDebugDTO): PromptBudgetSummary {
  return {
    used: debugPayload.prompt_budget.retrieved_context,
    budget: debugPayload.prompt_budget.retrieved_context_budget,
    history: debugPayload.prompt_budget.history,
    memory: debugPayload.prompt_budget.memory,
    userQuery: debugPayload.prompt_budget.user_query,
  };
}

function resolveErrorMessage(error: unknown): string {
  if (error instanceof APIClientError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "请求失败，请稍后重试。";
}

export const useWorkspaceStore = defineStore("workspace", () => {
  const userId = ref(DEFAULT_USER_ID);
  const sessions = ref<SessionItem[]>([]);
  const messages = ref<MessageItem[]>([]);
  const knowledgeDocuments = ref<KnowledgeDocument[]>([]);
  const memories = ref<MemoryItem[]>([]);
  const retrievalSections = ref<RetrievalPanelSection[]>([]);
  const selectedSessionId = ref<string | null>(null);
  const selectedKnowledgeBase = ref(DEFAULT_KB_ID);
  const debugPanelCollapsed = ref(false);
  const activeRetrievalTab = ref("final_context");
  const sessionSearchQuery = ref("");
  const isInitializing = ref(false);
  const isLoadingSessions = ref(false);
  const isLoadingMessages = ref(false);
  const isLoadingDocuments = ref(false);
  const isLoadingMemories = ref(false);
  const isSendingMessage = ref(false);
  const isUploadingDocument = ref(false);
  const lastError = ref<string | null>(null);
  const promptBudget = ref<PromptBudgetSummary | null>(null);

  let initializePromise: Promise<void> | null = null;

  const currentSession = computed(() => sessions.value.find((item) => item.id === selectedSessionId.value) ?? null);

  const currentModel = computed({
    get: () => currentSession.value?.modelName ?? DEFAULT_MODEL,
    set: (value: string) => {
      if (!currentSession.value || currentSession.value.modelName === value) {
        return;
      }
      void updateCurrentSession({ model_name: value });
    },
  });

  const currentRetrievalMode = computed({
    get: () => currentSession.value?.retrievalMode ?? "hybrid",
    set: (value: SessionItem["retrievalMode"]) => {
      if (!currentSession.value || currentSession.value.retrievalMode === value) {
        return;
      }
      void updateCurrentSession({ retrieval_mode: value });
    },
  });

  const allowWebSearch = computed({
    get: () => currentSession.value?.webSearchEnabled ?? false,
    set: (value: boolean) => {
      if (!currentSession.value || currentSession.value.webSearchEnabled === value) {
        return;
      }
      void updateCurrentSession({ web_search_enabled: value });
    },
  });

  const memoryStateSummary = computed(() => {
    if (!memories.value.length) {
      return "当前未加载记忆";
    }

    const labels: Record<MemoryItem["category"], string> = {
      preference: "用户偏好",
      long_term_task: "长期任务",
      background_fact: "背景事实",
      manual_note: "手动备注",
    };
    const counts = memories.value.reduce<Record<string, number>>((acc, item) => {
      acc[item.category] = (acc[item.category] ?? 0) + 1;
      return acc;
    }, {});

    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 2)
      .map(([key, value]) => `${value} ${labels[key as MemoryItem["category"]]}`)
      .join(" + ");
  });

  const contextBudgetLabel = computed(() => {
    if (!promptBudget.value) {
      return "尚未产生检索结果";
    }
    return `${promptBudget.value.used} / ${promptBudget.value.budget} Token`;
  });

  function clearRetrievalDebug() {
    retrievalSections.value = [];
    promptBudget.value = null;
    activeRetrievalTab.value = "final_context";
  }

  function syncKnowledgeBaseFromSelection() {
    selectedKnowledgeBase.value = currentSession.value?.kbId ?? DEFAULT_KB_ID;
  }

  function replaceMessage(messageId: string, updater: (message: MessageItem) => MessageItem) {
    const next = messages.value.map((message) => (message.id === messageId ? updater(message) : message));
    messages.value = next;
  }

  async function refreshMessages(sessionId: string) {
    isLoadingMessages.value = true;
    try {
      const payload = await listSessionMessages(sessionId, userId.value);
      messages.value = payload.map(normalizeMessage);
    } finally {
      isLoadingMessages.value = false;
    }
  }

  async function refreshKnowledgeDocuments(kbId = selectedKnowledgeBase.value) {
    if (!kbId) {
      knowledgeDocuments.value = [];
      return;
    }
    isLoadingDocuments.value = true;
    try {
      const payload = await listDocuments(userId.value, kbId);
      knowledgeDocuments.value = payload.map(normalizeDocument);
    } finally {
      isLoadingDocuments.value = false;
    }
  }

  async function refreshMemories() {
    isLoadingMemories.value = true;
    try {
      const payload = await listMemories(userId.value);
      memories.value = payload.map(normalizeMemory);
    } finally {
      isLoadingMemories.value = false;
    }
  }

  async function hydrateSelectedSession(sessionId: string) {
    selectedSessionId.value = sessionId;
    syncKnowledgeBaseFromSelection();
    clearRetrievalDebug();
    await Promise.all([refreshMessages(sessionId), refreshKnowledgeDocuments(selectedKnowledgeBase.value)]);
  }

  async function refreshSessionList(preferredSessionId?: string | null) {
    isLoadingSessions.value = true;
    try {
      const payload = await listSessions({
        userId: userId.value,
        q: sessionSearchQuery.value || undefined,
      });
      const previousSelectedId = selectedSessionId.value;
      sessions.value = payload.map(normalizeSession);

      if (!sessions.value.length) {
        selectedSessionId.value = null;
        messages.value = [];
        knowledgeDocuments.value = [];
        clearRetrievalDebug();
        return;
      }

      const requestedId = preferredSessionId ?? previousSelectedId;
      const nextSelectedId =
        sessions.value.find((item) => item.id === requestedId)?.id ?? sessions.value[0].id;

      const selectionChanged = nextSelectedId !== previousSelectedId;
      const needsHydration = selectionChanged || !messages.value.length;

      selectedSessionId.value = nextSelectedId;
      syncKnowledgeBaseFromSelection();

      if (needsHydration) {
        await hydrateSelectedSession(nextSelectedId);
      } else {
        await refreshKnowledgeDocuments(selectedKnowledgeBase.value);
      }
    } finally {
      isLoadingSessions.value = false;
    }
  }

  async function ensureInitialized() {
    if (initializePromise) {
      return initializePromise;
    }

    initializePromise = (async () => {
      isInitializing.value = true;
      lastError.value = null;
      try {
        await refreshSessionList();
        if (!sessions.value.length) {
          const created = await createSession({
            user_id: userId.value,
            kb_id: selectedKnowledgeBase.value,
            model_name: DEFAULT_MODEL,
            retrieval_mode: "hybrid",
            web_search_enabled: false,
          });
          sessions.value = [normalizeSession(created)];
          await hydrateSelectedSession(created.id);
        }
        await refreshMemories();
      } catch (error) {
        lastError.value = resolveErrorMessage(error);
        throw error;
      } finally {
        isInitializing.value = false;
        initializePromise = null;
      }
    })();

    return initializePromise;
  }

  async function selectSession(sessionId: string): Promise<boolean> {
    if (selectedSessionId.value === sessionId && messages.value.length) {
      return true;
    }
    try {
      lastError.value = null;
      await hydrateSelectedSession(sessionId);
      return true;
    } catch (error) {
      lastError.value = resolveErrorMessage(error);
      return false;
    }
  }

  async function searchSessions(query: string): Promise<boolean> {
    sessionSearchQuery.value = query.trim();
    try {
      lastError.value = null;
      await refreshSessionList(selectedSessionId.value);
      return true;
    } catch (error) {
      lastError.value = resolveErrorMessage(error);
      return false;
    }
  }

  async function createNewSession(): Promise<boolean> {
    lastError.value = null;
    try {
      const created = await createSession({
        user_id: userId.value,
        kb_id: selectedKnowledgeBase.value,
        model_name: currentModel.value,
        retrieval_mode: currentRetrievalMode.value,
        web_search_enabled: allowWebSearch.value,
      });
      const normalized = normalizeSession(created);
      sessions.value = [normalized, ...sessions.value.filter((item) => item.id !== normalized.id)];
      await hydrateSelectedSession(normalized.id);
      return true;
    } catch (error) {
      lastError.value = resolveErrorMessage(error);
      return false;
    }
  }

  async function updateCurrentSession(payload: {
    model_name?: string;
    retrieval_mode?: SessionItem["retrievalMode"];
    web_search_enabled?: boolean;
  }): Promise<boolean> {
    if (!currentSession.value) {
      return false;
    }
    lastError.value = null;
    try {
      const updated = await patchSession(currentSession.value.id, {
        user_id: userId.value,
        model_name: payload.model_name,
        retrieval_mode: payload.retrieval_mode,
        web_search_enabled: payload.web_search_enabled,
      });
      const normalized = normalizeSession(updated);
      sessions.value = sessions.value.map((item) => (item.id === normalized.id ? normalized : item));
      syncKnowledgeBaseFromSelection();
      return true;
    } catch (error) {
      lastError.value = resolveErrorMessage(error);
      return false;
    }
  }

  async function uploadKnowledgeFiles(files: File[]): Promise<boolean> {
    if (!files.length) {
      return false;
    }
    isUploadingDocument.value = true;
    lastError.value = null;
    try {
      for (const file of files) {
        await uploadDocument(userId.value, selectedKnowledgeBase.value, file);
      }
      await refreshKnowledgeDocuments(selectedKnowledgeBase.value);
      return true;
    } catch (error) {
      lastError.value = resolveErrorMessage(error);
      return false;
    } finally {
      isUploadingDocument.value = false;
    }
  }

  async function removeDocument(documentId: string): Promise<boolean> {
    lastError.value = null;
    try {
      await deleteDocument(documentId);
      knowledgeDocuments.value = knowledgeDocuments.value.filter((item) => item.id !== documentId);
      return true;
    } catch (error) {
      lastError.value = resolveErrorMessage(error);
      return false;
    }
  }

  async function removeMemory(memoryId: string): Promise<boolean> {
    lastError.value = null;
    try {
      await deleteMemory(memoryId);
      memories.value = memories.value.filter((item) => item.id !== memoryId);
      return true;
    } catch (error) {
      lastError.value = resolveErrorMessage(error);
      return false;
    }
  }

  async function sendMessage(content: string, files: File[]): Promise<boolean> {
    const trimmed = content.trim();
    if (!trimmed) {
      return false;
    }

    if (!currentSession.value) {
      await createNewSession();
    }
    const session = currentSession.value;
    if (!session) {
      return false;
    }

    isSendingMessage.value = true;
    lastError.value = null;

    const userMessageId = `user-${Date.now()}`;
    const assistantMessageId = `assistant-${Date.now()}`;

    messages.value = [
      ...messages.value,
      {
        id: userMessageId,
        role: "user",
        content: trimmed,
        timestamp: formatDateTime(new Date().toISOString()),
        citations: [],
        toolTrace: [],
      },
      {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        timestamp: formatDateTime(new Date().toISOString()),
        citations: [],
        toolTrace: [],
        streaming: true,
      },
    ];

    try {
      const attachmentIds: string[] = [];
      for (const file of files) {
        const uploaded = await uploadChatAttachment(userId.value, session.id, file);
        attachmentIds.push(uploaded.attachment_id);
      }

      let streamError: string | null = null;

      await streamChat(
        {
          user_id: userId.value,
          session_id: session.id,
          message: trimmed,
          attachment_ids: attachmentIds,
          debug: true,
        },
        {
          onToolCall(data) {
            const trace = normalizeToolTrace(data as unknown as ToolTraceDTO);
            replaceMessage(assistantMessageId, (message) => ({
              ...message,
              toolTrace: [...message.toolTrace, trace],
            }));
          },
          onToken(data) {
            const text = typeof data.text === "string" ? data.text : "";
            replaceMessage(assistantMessageId, (message) => ({
              ...message,
              content: `${message.content}${text}`,
              streaming: true,
            }));
          },
          onRetrievalDebug(data) {
            const debugPayload = data as unknown as RetrievalDebugDTO;
            retrievalSections.value = normalizeRetrievalSections(debugPayload);
            promptBudget.value = normalizePromptBudget(debugPayload);
            activeRetrievalTab.value = retrievalSections.value[0]?.key ?? "final_context";
          },
          onFinalAnswer(data) {
            const answer = data as unknown as ChatAnswerDTO;
            replaceMessage(assistantMessageId, (message) => ({
              ...message,
              content: answer.answer,
              citations: answer.citations.map(normalizeCitation),
              toolTrace: answer.tool_trace.map(normalizeToolTrace),
              streaming: false,
              failed: false,
            }));
          },
          onError(data) {
            streamError = typeof data.error === "string" ? data.error : "聊天流返回失败。";
          },
        },
      );

      if (streamError) {
        throw new Error(streamError);
      }

      await refreshMessages(session.id);
      await refreshSessionList(session.id);
      return true;
    } catch (error) {
      const message = resolveErrorMessage(error);
      lastError.value = message;
      replaceMessage(assistantMessageId, (item) => ({
        ...item,
        content: message,
        streaming: false,
        failed: true,
      }));
      return false;
    } finally {
      isSendingMessage.value = false;
    }
  }

  return {
    userId,
    sessions,
    messages,
    knowledgeDocuments,
    memories,
    retrievalSections,
    selectedSessionId,
    selectedKnowledgeBase,
    debugPanelCollapsed,
    activeRetrievalTab,
    sessionSearchQuery,
    isInitializing,
    isLoadingSessions,
    isLoadingMessages,
    isLoadingDocuments,
    isLoadingMemories,
    isSendingMessage,
    isUploadingDocument,
    lastError,
    currentSession,
    currentModel,
    currentRetrievalMode,
    allowWebSearch,
    memoryStateSummary,
    contextBudgetLabel,
    promptBudget,
    ensureInitialized,
    refreshSessionList,
    searchSessions,
    selectSession,
    createNewSession,
    updateCurrentSession,
    refreshKnowledgeDocuments,
    refreshMemories,
    uploadKnowledgeFiles,
    removeDocument,
    removeMemory,
    sendMessage,
  };
});
