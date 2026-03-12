<script setup lang="ts">
import { RouterView } from "vue-router";
import { NConfigProvider, zhCN, dateZhCN } from "naive-ui";

import AppShell from "@/components/layout/AppShell.vue";
import { themeOverrides } from "@/styles/theme";
</script>

<template>
  <n-config-provider
    :theme-overrides="themeOverrides"
    :locale="zhCN"
    :date-locale="dateZhCN"
  >
    <AppShell>
      <RouterView />
    </AppShell>
  </n-config-provider>
</template>
