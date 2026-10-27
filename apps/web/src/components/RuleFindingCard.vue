<script setup lang="ts">
import type { V1AnalysisTask } from '@casepilot/contracts';

type RuleFinding = V1AnalysisTask['ruleFindings'][number];

defineProps<{ finding: RuleFinding }>();

const severityText: Record<RuleFinding['severity'], string> = {
  low: '低风险',
  medium: '中风险',
  high: '高风险',
};

function displayValue(value: RuleFinding['sourceValues'][number]['value']) {
  if (typeof value === 'string') return value;
  return JSON.stringify(value);
}
</script>

<template>
  <article class="finding">
    <span class="finding-source rule">规则核验 · {{ severityText[finding.severity] }}</span>
    <strong>{{ finding.title }}</strong>
    <p>{{ finding.detail }}</p>
    <dl v-if="finding.sourceValues.length" class="source-values">
      <div v-for="(source, index) in finding.sourceValues" :key="`${source.factId}:${index}`">
        <dt>{{ source.factId }}</dt>
        <dd>{{ displayValue(source.value) }}</dd>
      </div>
    </dl>
    <small v-if="finding.factRefs.length">事实依据：{{ finding.factRefs.join('、') }}</small>
  </article>
</template>
