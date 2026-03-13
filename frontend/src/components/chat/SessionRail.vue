<script setup lang="ts">
import { computed, ref } from "vue";
import { NButton, NInput, NTag } from "naive-ui";

import { useWorkspaceStore } from "@/stores/workspace";

const store = useWorkspaceStore();
const searchValue = ref(store.sessionSearchQuery);

const retrievalModeLabel = computed(() => {
  const labels: Record<string, string> = {
    hybrid: "混合检索",
    vector: "仅向量检索",
    bm25: "仅 BM25",
  };
  return labels[store.currentRetrievalMode] ?? store.currentRetrievalMode;
});

let searchTimer: ReturnType<typeof setTimeout> | null = null;

function handleSearchInput(value: string) {
  searchValue.value = value;
  if (searchTimer) {
    clearTimeout(searchTimer);
  }
  searchTimer = setTimeout(() => {
    void store.searchSessions(value);
  }, 250);
}
</script>

<template>
  <section class="rail-panel glass-card">
    <div class="rail-head">
      <div>
        <p class="section-title">会话列表</p>
        <h3>对话与知识库</h3>
      </div>
      <n-button tertiary type="primary" size="small" @click="store.createNewSession">
        新建
      </n-button>
    </div>

    <n-input
      :value="searchValue"
      placeholder="按标题、知识库、摘要或标签搜索"
      round
      clearable
      @update:value="handleSearchInput"
    />

    <div class="kb-chip-row">
      <n-tag round :bordered="false" type="success">{{ store.selectedKnowledgeBase }}</n-tag>
      <n-tag round :bordered="false">{{ retrievalModeLabel }}</n-tag>
      <n-tag round :bordered="false">
        {{ store.allowWebSearch ? "联网搜索已开启" : "联网搜索已关闭" }}
      </n-tag>
    </div>

    <div v-if="store.isLoadingSessions" class="empty-state">正在加载会话...</div>
    <div v-else-if="!store.sessions.length" class="empty-state">当前还没有会话。</div>

    <div v-else class="session-list">
      <button
        v-for="session in store.sessions"
        :key="session.id"
        class="session-card"
        :class="{ active: store.selectedSessionId === session.id }"
        @click="store.selectSession(session.id)"
      >
        <div class="session-row">
          <strong>{{ session.title }}</strong>
          <span>{{ session.updatedAt }}</span>
        </div>
        <p>{{ session.summary }}</p>
        <small class="mono">{{ session.kbId }}</small>
      </button>
    </div>
  </section>
</template>

<style scoped>
.rail-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 20px;
  border-radius: 28px;
}

.rail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.rail-head h3 {
  margin: 8px 0 0;
  font-size: 20px;
}

.kb-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.empty-state {
  padding: 20px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.62);
  color: var(--cp-text-soft);
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.session-card {
  width: 100%;
  text-align: left;
  border: 1px solid rgba(66, 84, 108, 0.12);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.58);
  padding: 16px;
  cursor: pointer;
  transition: 180ms ease;
}

.session-card.active,
.session-card:hover {
  transform: translateY(-1px);
  border-color: rgba(15, 118, 110, 0.28);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(234, 246, 244, 0.9));
}

.session-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.session-card strong {
  font-size: 14px;
}

.session-card span,
.session-card small {
  color: var(--cp-text-soft);
}

.session-card p {
  margin: 10px 0;
  color: var(--cp-text-muted);
  font-size: 13px;
  line-height: 1.5;
}
</style>
