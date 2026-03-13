<script setup lang="ts">
import { onMounted } from "vue";

import MemoryBoard from "@/components/memory/MemoryBoard.vue";
import { useWorkspaceStore } from "@/stores/workspace";

const store = useWorkspaceStore();

onMounted(() => {
  void store.ensureInitialized().catch(() => undefined);
});
</script>

<template>
  <MemoryBoard />
</template>
