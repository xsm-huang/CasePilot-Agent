<script setup lang="ts">
import type { V1AnalysisTask } from '@casepilot/contracts';

type ModelFinding = V1AnalysisTask['modelFindings'][number];

defineProps<{ finding: ModelFinding }>();
defineEmits<{ citation: [citationId: string] }>();
</script>

<template>
  <article class="finding">
    <span class="finding-source ai">{{ finding.evidenceStatus === 'insufficient' ? '依据不足' : '有依据支持' }}</span>
    <strong>{{ finding.title }}</strong>
    <p>{{ finding.inference }}</p>
    <small v-if="finding.factRefs.length">事实依据：{{ finding.factRefs.join('、') }}</small>
    <div v-if="finding.citationRefs.length" class="evidence-actions">
      <button
        v-for="id in finding.citationRefs"
        :key="id"
        type="button"
        class="secondary"
        @click="$emit('citation', id)"
      >查看依据 {{ id }}</button>
    </div>
    <div v-if="finding.pendingItems.length" class="pending-items">
      <strong>待核查事项</strong>
      <ul><li v-for="item in finding.pendingItems" :key="item">{{ item }}</li></ul>
    </div>
  </article>
</template>
