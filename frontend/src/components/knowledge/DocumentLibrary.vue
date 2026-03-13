<script setup lang="ts">
import { ref } from "vue";
import { NButton, NDrawer, NDrawerContent, NEmpty, NProgress, NTag } from "naive-ui";

import { useWorkspaceStore } from "@/stores/workspace";
import type { KnowledgeDocument } from "@/types";

const store = useWorkspaceStore();
const selected = ref<KnowledgeDocument | null>(null);
const showDetail = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);

function openDetail(doc: KnowledgeDocument) {
  selected.value = doc;
  showDetail.value = true;
}

function openUploadPicker() {
  fileInput.value?.click();
}

function formatStatus(status: KnowledgeDocument["status"]): string {
  const labels: Record<KnowledgeDocument["status"], string> = {
    indexed: "已完成",
    processing: "处理中",
    failed: "失败",
  };
  return labels[status] ?? status;
}

function formatPipelineStatus(status: string): string {
  const labels: Record<string, string> = {
    ready: "已就绪",
    indexed: "已完成",
    processing: "处理中",
    failed: "失败",
    pending: "待处理",
  };
  return labels[status] ?? status;
}

async function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const files = Array.from(target.files ?? []);
  target.value = "";
  if (!files.length) {
    return;
  }
  await store.uploadKnowledgeFiles(files);
}

async function handleDelete(doc: KnowledgeDocument) {
  await store.removeDocument(doc.id);
  if (selected.value?.id === doc.id) {
    showDetail.value = false;
    selected.value = null;
  }
}
</script>

<template>
  <section class="kb-wrap">
    <div class="upload-card glass-card">
      <div>
        <p class="section-title">知识库</p>
        <h2>{{ store.selectedKnowledgeBase }} 的文档列表</h2>
        <p class="muted">
          支持 PDF、DOCX、MD、TXT、HTML、CSV 和 PPTX。上传后会自动完成解析、清洗、切分与索引构建。
        </p>
      </div>
      <div class="upload-actions">
        <button class="dropzone" type="button" @click="openUploadPicker">
          <strong>选择要上传的文件</strong>
          <span>上传后的文件会进入当前选中的知识库。</span>
        </button>
        <div class="upload-meta">
          <div>
            <span class="muted">支持格式</span>
            <strong>pdf / docx / md / txt / html / csv / pptx</strong>
          </div>
          <div>
            <span class="muted">当前状态</span>
            <strong>{{ store.isUploadingDocument ? "上传中..." : "可上传" }}</strong>
          </div>
          <n-button type="primary" :loading="store.isUploadingDocument" @click="openUploadPicker">
            上传文档
          </n-button>
        </div>
      </div>
      <input ref="fileInput" class="hidden-input" type="file" multiple @change="handleFileChange" />
    </div>

    <n-empty
      v-if="!store.isLoadingDocuments && !store.knowledgeDocuments.length"
      description="当前知识库还没有已索引文档。"
    />

    <div v-else class="doc-grid">
      <article v-for="doc in store.knowledgeDocuments" :key="doc.id" class="doc-card glass-card">
        <div class="doc-head">
          <div>
            <strong>{{ doc.name }}</strong>
            <small class="mono">{{ doc.type }}</small>
          </div>
          <n-tag
            round
            :type="doc.status === 'indexed' ? 'success' : doc.status === 'processing' ? 'warning' : 'error'"
            :bordered="false"
          >
            {{ formatStatus(doc.status) }}
          </n-tag>
        </div>
        <div class="doc-stats">
          <div><span>切片总数</span><strong>{{ doc.chunkCount }}</strong></div>
          <div><span>父块数量</span><strong>{{ doc.parentCount }}</strong></div>
          <div><span>子块数量</span><strong>{{ doc.childCount }}</strong></div>
        </div>
        <n-progress
          type="line"
          :percentage="doc.status === 'indexed' ? 100 : doc.status === 'processing' ? 64 : 32"
          :show-indicator="false"
        />
        <div class="doc-foot">
          <div>
            <span class="muted">索引时间</span>
            <strong>{{ doc.indexedAt }}</strong>
          </div>
          <n-button tertiary size="small" @click="openDetail(doc)">查看详情</n-button>
        </div>
      </article>
    </div>

    <n-drawer v-model:show="showDetail" width="420">
      <n-drawer-content title="文档索引详情" closable>
        <div v-if="selected" class="detail-panel">
          <div class="detail-item">
            <span>文档名称</span>
            <strong>{{ selected.name }}</strong>
          </div>
          <div class="detail-item">
            <span>向量状态</span>
            <strong>{{ formatPipelineStatus(selected.embeddingStatus) }}</strong>
          </div>
          <div class="detail-item">
            <span>BM25 状态</span>
            <strong>{{ formatPipelineStatus(selected.bm25Status) }}</strong>
          </div>
          <div class="detail-item">
            <span>父块 / 子块</span>
            <strong>{{ selected.parentCount }} / {{ selected.childCount }}</strong>
          </div>
          <div class="detail-item">
            <span>切片总数</span>
            <strong>{{ selected.chunkCount }}</strong>
          </div>
          <n-button type="primary" secondary disabled>重建索引功能开发中</n-button>
          <n-button type="error" tertiary @click="handleDelete(selected)">删除文档</n-button>
        </div>
      </n-drawer-content>
    </n-drawer>
  </section>
</template>

<style scoped>
.kb-wrap {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.upload-card,
.doc-card {
  border-radius: 30px;
}

.upload-card {
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding: 26px;
}

.upload-card h2 {
  margin: 8px 0 10px;
  font-size: 28px;
}

.upload-actions {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(280px, 0.9fr);
  gap: 18px;
}

.dropzone {
  min-height: 180px;
  display: grid;
  place-items: center;
  text-align: center;
  border-radius: 24px;
  border: 1px dashed rgba(15, 118, 110, 0.28);
  background: linear-gradient(180deg, rgba(236, 248, 247, 0.92), rgba(255, 255, 255, 0.9));
  cursor: pointer;
}

.dropzone span {
  color: var(--cp-text-soft);
}

.upload-meta {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 14px;
  padding: 20px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(66, 84, 108, 0.12);
}

.hidden-input {
  display: none;
}

.doc-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.doc-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
}

.doc-head,
.doc-foot {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.doc-head div {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.doc-head small {
  color: var(--cp-text-soft);
}

.doc-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.doc-stats div,
.detail-item {
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(66, 84, 108, 0.12);
}

.doc-stats span,
.detail-item span,
.doc-foot span {
  display: block;
  color: var(--cp-text-soft);
  font-size: 12px;
}

.doc-stats strong,
.detail-item strong,
.doc-foot strong {
  display: block;
  margin-top: 6px;
}

.detail-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

@media (max-width: 1180px) {
  .upload-actions,
  .doc-grid {
    grid-template-columns: 1fr;
  }
}
</style>
