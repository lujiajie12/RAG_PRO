<script setup lang="ts">
import { onMounted } from "vue";

import DocumentLibrary from "@/components/knowledge/DocumentLibrary.vue";
import { useWorkspaceStore } from "@/stores/workspace";

const store = useWorkspaceStore();

onMounted(() => {
  void store.ensureInitialized().catch(() => undefined);
});
</script>

<template>
  <DocumentLibrary />
</template>
