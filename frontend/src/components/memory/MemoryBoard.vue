<script setup lang="ts">
import { computed, ref } from "vue";
import { NButton, NTag } from "naive-ui";

import { useWorkspaceStore } from "@/stores/workspace";

const store = useWorkspaceStore();
const activeCategory = ref("all");

const memoryCategories = [
  { key: "all", label: "全部" },
  { key: "preference", label: "用户偏好" },
  { key: "long_term_task", label: "长期任务" },
  { key: "background_fact", label: "背景事实" },
  { key: "manual_note", label: "手动固定" },
];

const filteredMemories = computed(() =>
  activeCategory.value === "all"
    ? store.memories
    : store.memories.filter((item) => item.category === activeCategory.value),
);
</script>

<template>
  <section class="memory-wrap">
    <div class="memory-header glass-card">
      <div>
        <p class="section-title">Memory Studio</p>
        <h2>长期记忆查看与干预</h2>
        <p class="muted">展示 semantic memory、来源会话、召回分数和 prompt 注入方式，便于调试记忆策略。</p>
      </div>
      <div class="filter-row">
        <button
          v-for="item in memoryCategories"
          :key="item.key"
          class="filter-chip"
          :class="{ active: activeCategory === item.key }"
          @click="activeCategory = item.key"
        >
          {{ item.label }}
        </button>
      </div>
    </div>

    <div class="memory-grid">
      <article v-for="memory in filteredMemories" :key="memory.id" class="memory-card glass-card">
        <div class="memory-top">
          <div>
            <p class="mono">{{ memory.id }}</p>
            <h3>{{ memory.summary }}</h3>
          </div>
          <n-tag round :bordered="false" :type="memory.pinned ? 'success' : 'default'">
            {{ memory.pinned ? "Pinned" : memory.category }}
          </n-tag>
        </div>
        <p class="memory-detail">{{ memory.detail }}</p>
        <div class="memory-meta">
          <div>
            <span class="muted">score</span>
            <strong class="mono">{{ memory.score.toFixed(2) }}</strong>
          </div>
          <div>
            <span class="muted">source</span>
            <strong>{{ memory.sourceSession }}</strong>
          </div>
        </div>
        <div class="memory-footer">
          <small>created {{ memory.createdAt }}</small>
          <small>updated {{ memory.updatedAt }}</small>
        </div>
        <div class="memory-actions">
          <n-button tertiary type="primary" size="small">查看注入详情</n-button>
          <n-button tertiary type="error" size="small">删除</n-button>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.memory-wrap {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.memory-header,
.memory-card {
  border-radius: 30px;
}

.memory-header {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px 26px;
}

.memory-header h2 {
  margin: 8px 0 10px;
  font-size: 28px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-chip {
  padding: 10px 14px;
  border-radius: 999px;
  border: 1px solid rgba(66, 84, 108, 0.14);
  background: rgba(255, 255, 255, 0.7);
  cursor: pointer;
}

.filter-chip.active {
  background: rgba(15, 118, 110, 0.12);
  border-color: rgba(15, 118, 110, 0.24);
  color: var(--cp-accent);
}

.memory-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.memory-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 22px;
}

.memory-top,
.memory-meta,
.memory-footer,
.memory-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.memory-top p {
  margin: 0 0 8px;
  color: var(--cp-text-soft);
}

.memory-top h3 {
  margin: 0;
  font-size: 20px;
}

.memory-detail {
  margin: 0;
  line-height: 1.7;
  color: var(--cp-text-muted);
}

.memory-meta div {
  flex: 1;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(66, 84, 108, 0.12);
}

.memory-meta span,
.memory-footer small {
  color: var(--cp-text-soft);
}

@media (max-width: 1080px) {
  .memory-grid {
    grid-template-columns: 1fr;
  }
}
</style>
