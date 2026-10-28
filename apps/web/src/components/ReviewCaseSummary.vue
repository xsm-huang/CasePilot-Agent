<script setup lang="ts">
import type { ReviewCaseListItem } from '@casepilot/contracts';
import { formatDateTime, formatMoney, label } from '../domain/reviewCases';
defineProps<{ summary: ReviewCaseListItem }>();
defineEmits<{ open: [] }>();
</script>

<template>
  <section class="review-case-summary">
    <section class="panel case-overview">
      <div><span class="label">当前案件</span><h2>{{ summary.id }}</h2><p>出险时间：{{ formatDateTime(summary.accidentAt) }}</p><small>{{ label(summary.injuryStatus) }} · 最近审查状态：{{ label(summary.latestReviewStatus) }}</small></div>
      <div class="summary-actions"><div class="amount-summary"><span>原核赔金额<strong>{{ formatMoney(summary.originalApprovedAmount) }}</strong></span><span>有效实付金额<strong>{{ formatMoney(summary.effectivePaidAmount) }}</strong></span></div><button type="button" class="primary" @click="$emit('open')">查看完整详情</button></div>
    </section>
    <section class="detail-grid two-columns">
      <article class="panel"><h2>赔案范围</h2><div v-for="claim in summary.targetClaims" :key="claim.claimId" class="summary-row"><span class="tag">目标赔案</span><div><strong>{{ claim.claimNumber }}</strong><small>报案号 {{ claim.reportNumber }} · {{ label(claim.closureType) }} · {{ label(claim.originalPaymentStatus) }}</small></div></div><div v-for="claim in summary.relatedClaims" :key="claim.claimId" class="summary-row"><span class="tag secondary-tag">关联赔案</span><div><strong>{{ claim.claimNumber }}</strong><small>报案号 {{ claim.reportNumber }} · {{ label(claim.closureType) }}</small></div></div><p v-if="!summary.relatedClaims.length" class="muted">没有关联赔案。</p></article>
      <article class="panel"><h2>车辆</h2><div v-for="vehicle in summary.vehicles" :key="vehicle.vehicleId" class="summary-row"><span class="tag">{{ label(vehicle.role) }}</span><div><strong>{{ vehicle.plateNumber }}</strong><small>{{ vehicle.vehicleId }}</small></div></div></article>
    </section>
    <section class="panel summary-notice"><strong>当前为案件摘要</strong><p>完整事故事实、保单和承保险种、损失、理算核赔支付、作业时间线、资料缺口及材料目录请进入详情页查看。</p></section>
  </section>
</template>
