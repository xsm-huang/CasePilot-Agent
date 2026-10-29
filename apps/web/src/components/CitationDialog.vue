<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import type { CitationContext } from '@casepilot/contracts';
import CollapsibleText from './CollapsibleText.vue';
defineProps<{ citation: CitationContext }>();
const emit = defineEmits<{ close: [] }>();
const dialog = ref<HTMLDialogElement>();
onMounted(() => dialog.value?.showModal());
onBeforeUnmount(() => dialog.value?.close());
</script>
<template>
  <dialog ref="dialog" class="report-dialog citation-dialog" aria-label="引用依据" @close="emit('close')"><header><h2>{{ citation.citation.fileName }} · 第 {{ citation.citation.page }} 页</h2><button class="secondary" autofocus @click="dialog?.close()">关闭</button></header><p class="muted">{{ citation.citation.clauseVersion }} · 固定知识版本 {{ citation.citation.generationId.slice(0, 12) }}</p><h3>引用原文</h3><CollapsibleText :text="citation.citation.content" /><details><summary>相邻原文</summary><h4>前一段</h4><CollapsibleText :text="citation.previous?.content ?? '已到文档开头。'" /><h4>后一段</h4><CollapsibleText :text="citation.next?.content ?? '已到文档末尾。'" /><p class="muted">相邻段落仅辅助阅读，不自动作为本次判断依据。</p></details></dialog>
</template>
