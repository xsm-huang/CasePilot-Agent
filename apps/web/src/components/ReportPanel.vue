<script setup lang="ts">
import type { V0AnalysisReport, V0ClaimCase } from '@casepilot/contracts';
defineProps<{ report: V0AnalysisReport; claim?: V0ClaimCase }>();
</script>
<template>
  <div class="panel report">
    <span class="success">分析完成</span><h2>案件分析报告</h2><h3>案件摘要</h3><p>{{ report.summary }}</p>
    <h3>疑点清单</h3><p v-if="!report.findings.length">未发现规则范围内的显著疑点。</p>
    <article v-for="finding in report.findings" :key="finding.code" class="finding"><strong>{{ finding.title }}</strong><p>{{ finding.detail }}</p></article>
    <h3>处理建议</h3><p class="recommendation">{{ report.recommendation }}</p>
    <h3>条款依据 · {{ claim?.clauseVersion }}</h3>
    <article v-for="citation in report.citations" :key="citation.id" class="citation"><strong>{{ citation.id }} · {{ citation.title }}</strong><p>{{ citation.content }}</p><small>来源：虚构示例条款集 / {{ claim?.productCode }}</small></article>
    <template v-if="report.reviewerComment"><h3>审核意见</h3><p>{{ report.reviewerComment }}</p></template>
  </div>
</template>
