<script setup lang="ts">
import { NButton, NInput, NTag } from "naive-ui";

import { useWorkspaceStore } from "@/stores/workspace";

const store = useWorkspaceStore();
</script>

<template>
  <section class="rail-panel glass-card">
    <div class="rail-head">
      <div>
        <p class="section-title">Sessions</p>
        <h3>会话与知识库</h3>
      </div>
      <n-button tertiary type="primary" size="small">新建</n-button>
    </div>

    <n-input placeholder="搜索会话、知识库或标签" round clearable />

    <div class="kb-chip-row">
      <n-tag round :bordered="false" type="success">kb-langchain</n-tag>
      <n-tag round :bordered="false">Hybrid Retrieval</n-tag>
      <n-tag round :bordered="false">Parent Docs</n-tag>
    </div>

    <div class="session-list">
      <button
        v-for="session in store.sessions"
        :key="session.id"
        class="session-card"
        :class="{ active: store.selectedSessionId === session.id }"
        @click="store.selectedSessionId = session.id"
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
