import { createRouter, createWebHistory } from "vue-router";

import ChatWorkspaceView from "@/views/ChatWorkspaceView.vue";
import KnowledgeBaseView from "@/views/KnowledgeBaseView.vue";
import MemoryStudioView from "@/views/MemoryStudioView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/workspace" },
    { path: "/workspace", name: "workspace", component: ChatWorkspaceView },
    { path: "/knowledge", name: "knowledge", component: KnowledgeBaseView },
    { path: "/memory", name: "memory", component: MemoryStudioView },
  ],
});

export default router;
