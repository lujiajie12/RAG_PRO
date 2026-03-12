<script setup lang="ts">
import {
  NButton,
  NInput,
  NSelect,
  NSwitch,
  NTag,
} from "naive-ui";

import DebugPanel from "@/components/chat/DebugPanel.vue";
import MessageBubble from "@/components/chat/MessageBubble.vue";
import SessionRail from "@/components/chat/SessionRail.vue";
import { useWorkspaceStore } from "@/stores/workspace";

const store = useWorkspaceStore();

const modelOptions = [
  { label: "qwen-plus", value: "qwen-plus" },
  { label: "qwen-max", value: "qwen-max" },
  { label: "qwen-turbo", value: "qwen-turbo" },
];

const retrievalOptions = [
  { label: "Hybrid Retrieval", value: "hybrid" },
  { label: "Vector Only", value: "vector" },
  { label: "BM25 Only", value: "bm25" },
];
</script>

<template>
  <div class="workspace-grid">
    <SessionRail />

    <section class="chat-stage glass-card">
      <header class="chat-toolbar">
        <div>
          <p class="section-title">Chat Workspace</p>
          <h2>{{ store.currentSession.title }}</h2>
        </div>
        <div class="toolbar-controls">
          <n-select :options="modelOptions" value="qwen-plus" class="toolbar-select" />
          <n-select :options="retrievalOptions" value="hybrid" class="toolbar-select" />
          <div class="toolbar-switch">
            <span>Web Search</span>
            <n-switch v-model:value="store.allowWebSearch" />
          </div>
        </div>
      </header>

      <div class="signal-strip">
        <div class="signal-card">
          <span class="muted">Active KB</span>
          <strong>{{ store.selectedKnowledgeBase }}</strong>
        </div>
        <div class="signal-card">
          <span class="muted">Memory State</span>
          <strong>1 preference + 1 task recalled</strong>
        </div>
        <div class="signal-card">
          <span class="muted">Context Budget</span>
          <strong class="mono">2400 / 6000 tokens</strong>
        </div>
      </div>

      <div class="message-flow">
        <MessageBubble v-for="message in store.messages" :key="message.id" :message="message" />
      </div>

      <footer class="composer glass-card">
        <div class="composer-hints">
          <n-tag round :bordered="false" type="success">RAG ready</n-tag>
          <n-tag round :bordered="false">Agent tool calling</n-tag>
          <n-tag round :bordered="false">Long-term memory</n-tag>
        </div>
        <n-input
          type="textarea"
          round
          placeholder="输入你的问题，或要求记住你的偏好。"
          :autosize="{ minRows: 4, maxRows: 6 }"
        />
        <div class="composer-actions">
          <div class="muted">支持文档问答、偏好记忆、多轮上下文和检索调试联动。</div>
          <div class="button-row">
            <n-button tertiary>上传附件</n-button>
            <n-button type="primary">发送消息</n-button>
          </div>
        </div>
      </footer>
    </section>

    <DebugPanel />
  </div>
</template>

<style scoped>
.workspace-grid {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr) 380px;
  gap: 18px;
}

.chat-stage {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 20px;
  border-radius: 30px;
  min-height: 760px;
}

.chat-toolbar,
.composer-actions,
.signal-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.chat-toolbar h2 {
  margin: 8px 0 0;
  font-size: 24px;
}

.toolbar-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-select {
  width: 170px;
}

.toolbar-switch {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.64);
  border: 1px solid rgba(66, 84, 108, 0.12);
}

.signal-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.signal-card {
  padding: 14px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(66, 84, 108, 0.12);
}

.signal-card span,
.signal-card strong {
  display: block;
}

.signal-card strong {
  margin-top: 6px;
}

.message-flow {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 4px;
}

.composer {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 18px;
  border-radius: 28px;
}

.composer-hints,
.button-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 1400px) {
  .workspace-grid {
    grid-template-columns: 280px minmax(0, 1fr);
  }
}

@media (max-width: 1180px) {
  .workspace-grid {
    grid-template-columns: 1fr;
  }

  .chat-toolbar,
  .composer-actions {
    flex-direction: column;
    align-items: flex-start;
  }

  .toolbar-controls,
  .signal-strip {
    width: 100%;
  }

  .signal-strip {
    grid-template-columns: 1fr;
  }
}
</style>
