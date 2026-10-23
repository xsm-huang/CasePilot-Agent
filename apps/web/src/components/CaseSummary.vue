<script setup lang="ts">
import type { V0ClaimCase } from '@casepilot/contracts';
defineProps<{ selected: V0ClaimCase; running: boolean }>();
defineEmits<{ start: [] }>();
</script>
<template>
  <div class="panel case-summary">
    <div><span class="label">当前案件</span><h2>{{ selected.id }} · {{ selected.claimant }}</h2>
      <p>{{ selected.materials.length }} 份材料 · 申请金额 ¥{{ selected.claimAmount.toLocaleString() }}</p>
      <small>保单生效 {{ selected.policyEffectiveDate }} · 条款版本 {{ selected.clauseVersion }}</small>
    </div>
    <button class="primary" :disabled="running" @click="$emit('start')">{{ running ? '分析执行中…' : '启动新分析' }}</button>
  </div>
  <div class="material-strip"><span v-for="(material, index) in selected.materials" :key="`${material.type}:${index}`">▤ {{ material.name }}</span></div>
</template>
