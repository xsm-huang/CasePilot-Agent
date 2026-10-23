<script setup lang="ts">
import type { V0Finding } from '@casepilot/contracts';
import { findingSourceText } from '../domain/presentation';
defineProps<{ findings: V0Finding[]; comment: string; pending: boolean }>();
defineEmits<{ 'update:comment': [value: string]; review: [decision: 'approve' | 'reject'] }>();
</script>
<template>
  <div class="panel review">
    <span class="warning">人工审核节点</span><h2>请核验案件疑点</h2>
    <ul><li v-for="finding in findings" :key="finding.code"><span class="finding-source" :class="finding.source">{{ findingSourceText[finding.source] }}</span><strong>{{ finding.title }}</strong><br><span>{{ finding.detail }}</span></li></ul>
    <p>通过后继续生成分析报告；驳回后结束本次任务。</p>
    <label for="review-comment">审核意见</label>
    <textarea id="review-comment" :value="comment" maxlength="2000" @input="$emit('update:comment', ($event.target as HTMLTextAreaElement).value)"></textarea>
    <div class="actions"><button class="danger" :disabled="pending" @click="$emit('review', 'reject')">驳回任务</button><button class="primary" :disabled="pending" @click="$emit('review', 'approve')">通过并继续</button></div>
  </div>
</template>
