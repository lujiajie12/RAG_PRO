<script setup lang="ts">
import { ref } from "vue";
import { NButton, NDrawer, NDrawerContent, NProgress, NTag } from "naive-ui";

import { useWorkspaceStore } from "@/stores/workspace";
import type { KnowledgeDocument } from "@/types";

const store = useWorkspaceStore();
const selected = ref<KnowledgeDocument | null>(store.knowledgeDocuments[0] ?? null);
const showDetail = ref(false);

function openDetail(doc: KnowledgeDocument) {
  selected.value = doc;
  showDetail.value = true;
}
</script>

<template>
  <section class="kb-wrap">
    <div class="upload-card glass-card">
      <div>
        <p class="section-title">Knowledge Base</p>
        <h2>文档上传与索引状态</h2>
        <p class="muted">支持 PDF / DOCX / MD / TXT / HTML，上传后自动解析、切分、向量化并构建 BM25。</p>
      </div>
      <div class="upload-actions">
        <div class="dropzone">
          <strong>拖拽文件到这里</strong>
          <span>或点击选择文件，默认进入当前知识库</span>
        </div>
        <div class="upload-meta">
          <div>
            <span class="muted">支持格式</span>
            <strong>pdf / docx / md / txt / html</strong>
          </div>
          <div>
            <span class="muted">文件大小</span>
            <strong>建议小于 30MB</strong>
          </div>
          <n-button type="primary">上传文档</n-button>
        </div>
      </div>
    </div>

    <div class="doc-grid">
      <article v-for="doc in store.knowledgeDocuments" :key="doc.id" class="doc-card glass-card">
        <div class="doc-head">
          <div>
            <strong>{{ doc.name }}</strong>
            <small class="mono">{{ doc.type }}</small>
          </div>
          <n-tag round :type="doc.status === 'indexed' ? 'success' : doc.status === 'processing' ? 'warning' : 'error'" :bordered="false">
            {{ doc.status }}
          </n-tag>
        </div>
        <div class="doc-stats">
          <div><span>Chunks</span><strong>{{ doc.chunkCount }}</strong></div>
          <div><span>Parent</span><strong>{{ doc.parentCount }}</strong></div>
          <div><span>Child</span><strong>{{ doc.childCount }}</strong></div>
        </div>
        <n-progress
          type="line"
          :percentage="doc.status === 'indexed' ? 100 : doc.status === 'processing' ? 64 : 32"
          :show-indicator="false"
        />
        <div class="doc-foot">
          <div>
            <span class="muted">Indexed at</span>
            <strong>{{ doc.indexedAt }}</strong>
          </div>
          <n-button tertiary size="small" @click="openDetail(doc)">详情</n-button>
        </div>
      </article>
    </div>

    <n-drawer v-model:show="showDetail" width="420">
      <n-drawer-content title="文档索引详情" closable>
        <div v-if="selected" class="detail-panel">
          <div class="detail-item">
            <span>Document</span>
            <strong>{{ selected.name }}</strong>
          </div>
          <div class="detail-item">
            <span>Embedding</span>
            <strong>{{ selected.embeddingStatus }}</strong>
          </div>
          <div class="detail-item">
            <span>BM25</span>
            <strong>{{ selected.bm25Status }}</strong>
          </div>
          <div class="detail-item">
            <span>Parent / Child</span>
            <strong>{{ selected.parentCount }} / {{ selected.childCount }}</strong>
          </div>
          <div class="detail-item">
            <span>Chunk Count</span>
            <strong>{{ selected.chunkCount }}</strong>
          </div>
          <n-button type="primary" secondary>重建索引</n-button>
          <n-button type="error" tertiary>删除文档</n-button>
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
