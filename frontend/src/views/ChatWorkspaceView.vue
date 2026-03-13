<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { NAlert, NButton, NEmpty, NInput, NSelect, NSwitch, NTag } from "naive-ui";

import DebugPanel from "@/components/chat/DebugPanel.vue";
import MessageBubble from "@/components/chat/MessageBubble.vue";
import SessionRail from "@/components/chat/SessionRail.vue";
import { useWorkspaceStore } from "@/stores/workspace";

const store = useWorkspaceStore();
const draft = ref("");
const attachmentFiles = ref<File[]>([]);
const attachmentInput = ref<HTMLInputElement | null>(null);

const modelOptions = [
  { label: "qwen-plus", value: "qwen-plus" },
  { label: "qwen-max", value: "qwen-max" },
  { label: "qwen-turbo", value: "qwen-turbo" },
];

const retrievalOptions = [
  { label: "混合检索", value: "hybrid" },
  { label: "仅向量检索", value: "vector" },
  { label: "仅 BM25", value: "bm25" },
];

const canSend = computed(() => Boolean(store.currentSession) && !store.isSendingMessage);

const retrievalModeLabel = computed(() => {
  const labels: Record<string, string> = {
    hybrid: "混合检索",
    vector: "仅向量检索",
    bm25: "仅 BM25",
  };
  return labels[store.currentRetrievalMode] ?? store.currentRetrievalMode;
});

function openAttachmentPicker() {
  attachmentInput.value?.click();
}

function handleAttachmentSelection(event: Event) {
  const target = event.target as HTMLInputElement;
  const files = Array.from(target.files ?? []);
  target.value = "";
  attachmentFiles.value = [...attachmentFiles.value, ...files];
}

function removeAttachment(fileName: string) {
  attachmentFiles.value = attachmentFiles.value.filter((file) => file.name !== fileName);
}

async function handleSend() {
  const success = await store.sendMessage(draft.value, attachmentFiles.value);
  if (success) {
    draft.value = "";
    attachmentFiles.value = [];
  }
}

onMounted(() => {
  void store.ensureInitialized().catch(() => undefined);
});
</script>

<template>
  <div class="workspace-grid">
    <SessionRail />

    <section class="chat-stage glass-card">
      <header class="chat-toolbar">
        <div>
          <p class="section-title">对话工作台</p>
          <h2>{{ store.currentSession?.title ?? "正在加载会话..." }}</h2>
        </div>
        <div class="toolbar-controls">
          <n-select v-model:value="store.currentModel" :options="modelOptions" class="toolbar-select" />
          <n-select v-model:value="store.currentRetrievalMode" :options="retrievalOptions" class="toolbar-select" />
          <div class="toolbar-switch">
            <span>联网搜索</span>
            <n-switch v-model:value="store.allowWebSearch" />
          </div>
        </div>
      </header>

      <n-alert v-if="store.lastError" type="error" :show-icon="false">
        {{ store.lastError }}
      </n-alert>

      <div class="signal-strip">
        <div class="signal-card">
          <span class="muted">当前知识库</span>
          <strong>{{ store.selectedKnowledgeBase }}</strong>
        </div>
        <div class="signal-card">
          <span class="muted">记忆状态</span>
          <strong>{{ store.memoryStateSummary }}</strong>
        </div>
        <div class="signal-card">
          <span class="muted">上下文预算</span>
          <strong class="mono">{{ store.contextBudgetLabel }}</strong>
        </div>
      </div>

      <div v-if="store.isInitializing" class="message-flow empty-panel">
        正在初始化工作台...
      </div>
      <div v-else-if="!store.messages.length" class="message-flow empty-panel">
        <n-empty description="输入一个问题，开始与知识库进行对话。" />
      </div>
      <div v-else class="message-flow">
        <MessageBubble v-for="message in store.messages" :key="message.id" :message="message" />
      </div>

      <footer class="composer glass-card">
        <div class="composer-hints">
          <n-tag round :bordered="false" type="success">RAG 已就绪</n-tag>
          <n-tag round :bordered="false">{{ retrievalModeLabel }}</n-tag>
          <n-tag round :bordered="false">{{ store.allowWebSearch ? "联网搜索已开启" : "联网搜索已关闭" }}</n-tag>
        </div>

        <div v-if="attachmentFiles.length" class="attachment-row">
          <button
            v-for="file in attachmentFiles"
            :key="file.name"
            class="attachment-chip"
            type="button"
            @click="removeAttachment(file.name)"
          >
            {{ file.name }} ×
          </button>
        </div>

        <n-input
          v-model:value="draft"
          type="textarea"
          round
          placeholder="请输入你的问题。系统会流式返回回答、引用来源和检索调试信息。"
          :autosize="{ minRows: 4, maxRows: 6 }"
          @keydown.enter.exact.prevent="handleSend"
        />
        <div class="composer-actions">
          <div class="muted">
            你可以为当前问题附加文件，查看流式回答，并在右侧调试面板中检查检索到的上下文。
          </div>
          <div class="button-row">
            <n-button tertiary @click="openAttachmentPicker">添加附件</n-button>
            <n-button type="primary" :loading="store.isSendingMessage" :disabled="!canSend" @click="handleSend">
              发送
            </n-button>
          </div>
        </div>
        <input ref="attachmentInput" class="hidden-input" type="file" multiple @change="handleAttachmentSelection" />
      </footer>
    </section>

    <DebugPanel />
  </div>
</template>

<style scoped>
.workspace-grid {
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr) 380px;
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

.empty-panel {
  display: grid;
  place-items: center;
}

.composer {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 18px;
  border-radius: 28px;
}

.composer-hints,
.button-row,
.attachment-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.attachment-chip {
  border: 1px solid rgba(66, 84, 108, 0.12);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  padding: 8px 12px;
  cursor: pointer;
}

.hidden-input {
  display: none;
}

@media (max-width: 1400px) {
  .workspace-grid {
    grid-template-columns: 320px minmax(0, 1fr);
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
