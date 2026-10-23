<script setup lang="ts">
import type { V0ClaimCase, V0AnalysisTask } from '@casepilot/contracts';
import { statusText } from '../domain/presentation';
defineProps<{ cases: V0ClaimCase[]; history: V0AnalysisTask[]; selectedId: string; taskId?: string; pending: boolean }>();
defineEmits<{ selectCase: [id: string]; openTask: [id: string] }>();
</script>
<template>
  <aside class="panel cases">
    <h2>案件中心 <span class="count">{{ cases.length }}</span></h2>
    <button v-for="item in cases" :key="item.id" class="case-card" :class="{ active: selectedId === item.id }" :disabled="pending" @click="$emit('selectCase', item.id)">
      <span class="case-id">{{ item.id }}</span><strong>{{ item.claimant }} · 车损理赔</strong>
      <small>事故 {{ item.accidentDate }} · ¥{{ item.claimAmount.toLocaleString() }}</small>
    </button>
    <h3>历史分析任务</h3><p v-if="!history.length" class="muted">尚无历史任务</p>
    <button v-for="item in history" :key="item.id" class="history-card" :class="{ active: taskId === item.id }" :disabled="pending" @click="$emit('openTask', item.id)">
      <span>{{ item.caseId }}<small>{{ item.id.slice(0, 8) }}</small></span><span>{{ statusText[item.status] }}</span>
    </button>
  </aside>
</template>
