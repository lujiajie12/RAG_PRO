import { computed, ref } from "vue";
import { defineStore } from "pinia";

import { knowledgeDocuments, memories, messages, retrievalSections, sessions } from "@/mocks/workspace";

export const useWorkspaceStore = defineStore("workspace", () => {
  const selectedSessionId = ref(sessions[0].id);
  const selectedKnowledgeBase = ref("kb-langchain");
  const allowWebSearch = ref(false);
  const debugPanelCollapsed = ref(false);
  const activeRetrievalTab = ref("vector");

  const currentSession = computed(() => sessions.find((item) => item.id === selectedSessionId.value) ?? sessions[0]);

  return {
    sessions,
    messages,
    knowledgeDocuments,
    memories,
    retrievalSections,
    selectedSessionId,
    selectedKnowledgeBase,
    allowWebSearch,
    debugPanelCollapsed,
    activeRetrievalTab,
    currentSession,
  };
});
