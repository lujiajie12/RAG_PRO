<script setup lang="ts">
import { computed } from "vue";
import { NButton, NEmpty, NTabPane, NTabs, NTag } from "naive-ui";

import { useWorkspaceStore } from "@/stores/workspace";

const store = useWorkspaceStore();
const sections = computed(() => store.retrievalSections);
</script>

<template>
  <section class="debug-panel glass-card" :class="{ collapsed: store.debugPanelCollapsed }">
    <div class="debug-head">
      <div>
        <p class="section-title">检索调试</p>
        <h3>检索链路与上下文装配</h3>
      </div>
      <n-button quaternary size="small" @click="store.debugPanelCollapsed = !store.debugPanelCollapsed">
        {{ store.debugPanelCollapsed ? "展开" : "收起" }}
      </n-button>
    </div>

    <div v-if="!store.debugPanelCollapsed" class="debug-body">
      <n-tabs v-if="sections.length" v-model:value="store.activeRetrievalTab" type="segment">
        <n-tab-pane
          v-for="section in sections"
          :key="section.key"
          :tab="section.title"
          :name="section.key"
        >
          <div class="hit-list">
            <article v-for="hit in section.hits" :key="hit.id" class="hit-card">
              <div class="hit-top">
                <div>
                  <strong>{{ hit.fileName }}</strong>
                  <small class="mono">{{ hit.id }}</small>
                </div>
                <n-tag round :bordered="false" size="small">
                  {{ hit.tag }}
                </n-tag>
              </div>
              <p>{{ hit.preview }}</p>
              <div class="hit-score">
                <span>相关分数</span>
                <strong class="mono">{{ hit.score }}</strong>
              </div>
            </article>
          </div>
        </n-tab-pane>
      </n-tabs>

      <n-empty v-else description="发送一条开启调试的消息后，这里会展示完整检索链路。" />
    </div>
  </section>
</template>

<style scoped>
.debug-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  border-radius: 28px;
}

.debug-panel.collapsed {
  min-height: 160px;
}

.debug-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.debug-head h3 {
  margin: 8px 0 0;
  font-size: 20px;
}

.debug-body {
  min-height: 580px;
}

.hit-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hit-card {
  padding: 16px;
  border-radius: 22px;
  border: 1px solid rgba(66, 84, 108, 0.12);
  background: rgba(255, 255, 255, 0.72);
}

.hit-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.hit-top div {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.hit-top small {
  color: var(--cp-text-soft);
}

.hit-card p {
  margin: 12px 0;
  color: var(--cp-text-muted);
  line-height: 1.6;
}

.hit-score {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px dashed rgba(66, 84, 108, 0.14);
}

.hit-score span {
  color: var(--cp-text-soft);
  font-size: 12px;
}
</style>
