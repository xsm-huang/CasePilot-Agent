<script setup lang="ts">
import type { ReviewEvidenceSource } from '@casepilot/contracts';
import { label } from '../domain/reviewCases';
const props = defineProps<{ caseId: string; sources: ReviewEvidenceSource[] }>();
function openSource(source: ReviewEvidenceSource) {
  if (source.sourceType !== 'case_document' || !source.documentId) return;
  const page = source.page ? `#page=${source.page}` : '';
  window.open(`/api/review-cases/${encodeURIComponent(props.caseId)}/documents/${encodeURIComponent(source.documentId)}/content${page}`, '_blank', 'noopener');
}
</script>

<template>
  <div v-if="sources.length" class="evidence-actions">
    <button v-for="source in sources" :key="source.evidenceId" type="button" class="source-link"
      :disabled="source.sourceType !== 'case_document' || !source.documentId" @click="openSource(source)">
      {{ label(source.sourceType) }} · {{ source.title }}<template v-if="source.page"> · 第 {{ source.page }} 页</template>
      <small v-if="source.recordPointer">{{ source.recordPointer }}</small>
    </button>
  </div>
  <small v-else class="source-missing">来源不足，当前无法定位。</small>
</template>
