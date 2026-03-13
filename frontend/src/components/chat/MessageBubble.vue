<script setup lang="ts">
import { NTag } from "naive-ui";

import type { MessageItem, ToolTraceItem } from "@/types";

defineProps<{
  message: MessageItem;
}>();

function formatTraceStatus(status: ToolTraceItem["status"]): string {
  const labels = {
    planned: "待执行",
    running: "执行中",
    completed: "已完成",
    failed: "失败",
  };
  return labels[status];
}
</script>

<template>
  <article class="message-row" :class="message.role">
    <div class="avatar">{{ message.role === "assistant" ? "AI" : "我" }}</div>
    <div class="bubble glass-card" :class="[message.role, { failed: message.failed }]">
      <div class="bubble-meta">
        <strong>{{ message.role === "assistant" ? "ContextPilot" : "你" }}</strong>
        <span>{{ message.streaming ? "正在生成..." : message.timestamp }}</span>
      </div>
      <p>{{ message.content }}</p>

      <div v-if="message.citations.length" class="citation-list">
        <n-tag
          v-for="citation in message.citations"
          :key="`${citation.fileName}-${citation.page ?? 'na'}-${citation.chunkId}`"
          round
          size="small"
          :bordered="false"
        >
          {{ citation.fileName }} · 第{{ citation.page ?? "-" }}页 · {{ citation.rerankScore?.toFixed(3) ?? "-" }}
        </n-tag>
      </div>

      <div v-if="message.toolTrace.length" class="tool-list">
        <div v-for="tool in message.toolTrace" :key="`${tool.name}-${tool.summary}`" class="tool-card">
          <div>
            <strong>{{ tool.name }}</strong>
            <small>{{ formatTraceStatus(tool.status) }}</small>
          </div>
          <p>{{ tool.summary }}</p>
        </div>
      </div>
    </div>
  </article>
</template>

<style scoped>
.message-row {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.message-row.user {
  flex-direction: row-reverse;
}

.avatar {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(51, 92, 255, 0.14), rgba(15, 118, 110, 0.18));
  font-size: 12px;
  font-weight: 700;
  color: var(--cp-text);
}

.bubble {
  max-width: min(760px, 100%);
  border-radius: 28px;
  padding: 18px 20px;
}

.bubble.user {
  background: linear-gradient(180deg, rgba(228, 237, 255, 0.82), rgba(255, 255, 255, 0.88));
}

.bubble.assistant {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(237, 247, 246, 0.82));
}

.bubble.failed {
  border: 1px solid rgba(220, 38, 38, 0.24);
  background: linear-gradient(180deg, rgba(255, 245, 245, 0.92), rgba(255, 255, 255, 0.88));
}

.bubble-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 10px;
}

.bubble-meta span {
  color: var(--cp-text-soft);
  font-size: 13px;
}

.bubble p {
  margin: 0;
  line-height: 1.7;
  color: var(--cp-text);
}

.citation-list,
.tool-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.tool-card {
  min-width: 220px;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(66, 84, 108, 0.12);
}

.tool-card div {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tool-card small {
  color: var(--cp-accent);
  letter-spacing: 0.06em;
}

.tool-card p {
  margin-top: 8px;
  font-size: 13px;
  color: var(--cp-text-muted);
}
</style>
