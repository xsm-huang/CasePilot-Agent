<script setup lang="ts">
import { ref } from 'vue';
import WorkbenchPage from './pages/WorkbenchPage.vue';
import KnowledgePage from './pages/KnowledgePage.vue';
const page = ref<'workbench' | 'knowledge'>('workbench');
</script>

<template>
  <nav class="app-navigation" aria-label="主导航">
    <strong>CASEPILOT</strong>
    <button :class="{ active: page === 'workbench' }" :aria-current="page === 'workbench' ? 'page' : undefined" @click="page = 'workbench'">案件工作台</button>
    <button :class="{ active: page === 'knowledge' }" :aria-current="page === 'knowledge' ? 'page' : undefined" @click="page = 'knowledge'">条款知识库</button>
  </nav>
  <WorkbenchPage v-if="page === 'workbench'" />
  <KnowledgePage v-else />
</template>
