<script setup lang="ts">
import { computed } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { NAvatar, NBadge, NButton, NTag } from "naive-ui";

const route = useRoute();

const navItems = [
  { to: "/workspace", label: "对话工作台", short: "对话" },
  { to: "/knowledge", label: "知识库", short: "知识" },
  { to: "/memory", label: "记忆中心", short: "记忆" },
];

const activePath = computed(() => route.path);
</script>

<template>
  <div class="app-shell">
    <aside class="shell-rail">
      <div class="brand-block glass-card">
        <div class="brand-mark">CP</div>
        <div class="brand-copy">
          <strong>ContextPilot</strong>
          <span>知识工作台</span>
        </div>
      </div>

      <nav class="nav-list glass-card">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          :class="{ active: activePath === item.to }"
        >
          <span>{{ item.short }}</span>
          <small>{{ item.label }}</small>
        </RouterLink>
      </nav>

      <div class="rail-footer glass-card">
        <n-badge dot color="#0f766e">
          <n-avatar round size="large">AI</n-avatar>
        </n-badge>
        <n-tag round size="small" type="success" :bordered="false">运行中</n-tag>
        <n-button secondary type="primary" size="small">文档</n-button>
      </div>
    </aside>

    <main class="shell-main">
      <header class="shell-header glass-card">
        <div>
          <p class="section-title">AI 应用工程练手项目</p>
          <h1>RAG + Agent + Memory 知识工作台</h1>
        </div>
        <div class="header-summary">
          <div>
            <span class="muted">当前技术栈</span>
            <strong>Vue 3 + Flask + LangChain 1.2</strong>
          </div>
          <div>
            <span class="muted">当前模式</span>
            <strong>专业知识工作台</strong>
          </div>
        </div>
      </header>

      <section class="shell-content">
        <slot />
      </section>
    </main>
  </div>
</template>

<style scoped>
.shell-rail {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 22px 18px;
  border-right: 1px solid rgba(57, 73, 94, 0.08);
  background: linear-gradient(180deg, rgba(245, 249, 250, 0.78) 0%, rgba(237, 243, 246, 0.62) 100%);
}

.brand-block,
.nav-list,
.rail-footer,
.shell-header {
  border-radius: 28px;
}

.brand-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 18px 16px;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 16px;
  background: linear-gradient(135deg, #0f766e 0%, #335cff 100%);
  color: white;
  font-weight: 700;
}

.brand-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
  color: var(--cp-text-soft);
}

.brand-copy strong {
  color: var(--cp-text);
  font-size: 15px;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 10px;
}

.nav-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: center;
  justify-content: center;
  min-height: 84px;
  padding: 8px 6px;
  border-radius: 22px;
  color: var(--cp-text-muted);
  text-align: center;
  transition: 180ms ease;
}

.nav-item.active,
.nav-item:hover {
  background: rgba(255, 255, 255, 0.72);
  color: var(--cp-text);
  box-shadow: inset 0 0 0 1px rgba(15, 118, 110, 0.18);
}

.nav-item span {
  font-weight: 700;
  font-size: 14px;
}

.nav-item small {
  font-size: 12px;
}

.rail-footer {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 16px 10px;
}

.shell-main {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px;
}

.shell-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22px 28px;
}

.shell-header h1 {
  margin: 8px 0 0;
  font-size: 30px;
  line-height: 1.15;
}

.header-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(180px, 1fr));
  gap: 14px;
  min-width: 360px;
}

.header-summary div {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(66, 84, 108, 0.12);
}

.header-summary span,
.header-summary strong {
  display: block;
}

.header-summary strong {
  margin-top: 6px;
  font-size: 14px;
}

.shell-content {
  min-height: 0;
}

@media (max-width: 1080px) {
  .shell-rail {
    flex-direction: row;
    align-items: stretch;
    justify-content: space-between;
    padding-bottom: 0;
    border-right: none;
    border-bottom: 1px solid rgba(57, 73, 94, 0.08);
  }

  .nav-list {
    flex-direction: row;
  }

  .nav-item {
    min-width: 108px;
    min-height: 70px;
  }

  .rail-footer {
    margin-top: 0;
    flex-direction: row;
  }

  .shell-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .header-summary {
    width: 100%;
    min-width: 0;
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .shell-main {
    padding: 14px;
  }

  .shell-header h1 {
    font-size: 22px;
  }
}
</style>
