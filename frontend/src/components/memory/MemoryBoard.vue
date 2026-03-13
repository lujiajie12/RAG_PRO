<script setup lang="ts">
import { computed, ref } from "vue";
import { NButton, NDrawer, NDrawerContent, NEmpty, NTag } from "naive-ui";

import { useWorkspaceStore } from "@/stores/workspace";
import type { MemoryItem } from "@/types";

const store = useWorkspaceStore();
const activeCategory = ref("all");
const selected = ref<MemoryItem | null>(null);
const showDetail = ref(false);

const memoryCategories = [
  { key: "all", label: "全部" },
  { key: "preference", label: "用户偏好" },
  { key: "long_term_task", label: "长期任务" },
  { key: "background_fact", label: "背景事实" },
  { key: "manual_note", label: "手动备注" },
];

const filteredMemories = computed(() =>
  activeCategory.value === "all"
    ? store.memories
    : store.memories.filter((item) => item.category === activeCategory.value),
);

function openDetail(memory: MemoryItem) {
  selected.value = memory;
  showDetail.value = true;
}

function formatCategory(memory: MemoryItem): string {
  const labels: Record<MemoryItem["category"], string> = {
    preference: "用户偏好",
    long_term_task: "长期任务",
    background_fact: "背景事实",
    manual_note: "手动备注",
  };
  return memory.pinned ? "已固定" : labels[memory.category] ?? memory.category;
}

async function handleDelete(memory: MemoryItem) {
  await store.removeMemory(memory.id);
  if (selected.value?.id === memory.id) {
    selected.value = null;
    showDetail.value = false;
  }
}
</script>

<template>
  <section class="memory-wrap">
    <div class="memory-header glass-card">
      <div>
        <p class="section-title">记忆中心</p>
        <h2>长期记忆</h2>
        <p class="muted">
          在这里查看会被注入 Prompt 的已召回记忆、来源会话以及手动固定的信息。
        </p>
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

    <n-empty v-if="!store.isLoadingMemories && !filteredMemories.length" description="当前用户还没有存储的长期记忆。" />

    <div v-else class="memory-grid">
      <article v-for="memory in filteredMemories" :key="memory.id" class="memory-card glass-card">
        <div class="memory-top">
          <div>
            <p class="mono">{{ memory.id }}</p>
            <h3>{{ memory.summary }}</h3>
          </div>
          <n-tag round :bordered="false" :type="memory.pinned ? 'success' : 'default'">
            {{ formatCategory(memory) }}
          </n-tag>
        </div>
        <p class="memory-detail">{{ memory.detail }}</p>
        <div class="memory-meta">
          <div>
            <span class="muted">相关分数</span>
            <strong class="mono">{{ memory.score.toFixed(2) }}</strong>
          </div>
          <div>
            <span class="muted">来源会话</span>
            <strong>{{ memory.sourceSession }}</strong>
          </div>
        </div>
        <div class="memory-footer">
          <small>创建于 {{ memory.createdAt }}</small>
          <small>更新于 {{ memory.updatedAt }}</small>
        </div>
        <div class="memory-actions">
          <n-button tertiary type="primary" size="small" @click="openDetail(memory)">查看详情</n-button>
          <n-button tertiary type="error" size="small" @click="handleDelete(memory)">删除</n-button>
        </div>
      </article>
    </div>

    <n-drawer v-model:show="showDetail" width="420">
      <n-drawer-content title="记忆详情" closable>
        <div v-if="selected" class="detail-panel">
          <div class="detail-item">
            <span>摘要</span>
            <strong>{{ selected.summary }}</strong>
          </div>
          <div class="detail-item">
            <span>来源会话</span>
            <strong>{{ selected.sourceSession }}</strong>
          </div>
          <div class="detail-item">
            <span>相关分数</span>
            <strong>{{ selected.score.toFixed(2) }}</strong>
          </div>
          <div class="detail-item">
            <span>详细内容</span>
            <strong>{{ selected.detail }}</strong>
          </div>
        </div>
      </n-drawer-content>
    </n-drawer>
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

.memory-meta div,
.detail-item {
  flex: 1;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(66, 84, 108, 0.12);
}

.detail-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
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
