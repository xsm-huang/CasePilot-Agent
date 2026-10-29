<script setup lang="ts">
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue';
import type { AnalysisTask, Citation } from '@casepilot/contracts';
import CollapsibleText from './CollapsibleText.vue';
import { sectionNames } from '../domain/reviewExecution';
const props = defineProps<{ task: AnalysisTask; version?: number }>();
const emit = defineEmits<{ close: []; citation: [id: string] }>();
const dialog = ref<HTMLDialogElement>();
const selectedVersion = ref(props.version ?? props.task.report?.version ?? props.task.reports?.at(-1)?.version ?? 1);
const reports = computed(() => props.task.reports?.length ? props.task.reports : props.task.report ? [props.task.report] : []);
const report = computed(() => reports.value.find(r => r.version === selectedVersion.value) ?? props.task.report);
const frozenCitations = computed(() => (report.value?.snapshot.citations ?? []) as unknown as Citation[]);
watch(() => props.version, value => { if (value) selectedVersion.value = value; });
onMounted(() => dialog.value?.showModal());
onBeforeUnmount(() => dialog.value?.close());
</script>
<template>
  <dialog ref="dialog" class="report-dialog" aria-label="案件分析报告" @close="emit('close')">
    <header><div><span class="eyebrow">{{ report?.kind === 'final' ? '车损最终审查报告' : report?.kind === 'pending_review' ? '待复核报告' : '阶段报告' }}</span><h2>案件分析报告 · {{ task.caseId }}</h2></div><button type="button" class="secondary" autofocus @click="dialog?.close()">关闭</button></header>
    <label v-if="reports.length > 1" class="report-version">报告版本<select v-model="selectedVersion"><option v-for="item in reports" :key="item.version" :value="item.version">v{{ item.version }} · {{ item.generatedAt ? new Date(item.generatedAt).toLocaleString('zh-CN') : '历史版本' }}{{ item.version !== task.report?.version ? '（已被后续版本替代）' : '' }}</option></select></label>
    <p class="muted">审查编号 {{ task.id }} · 输入版本 {{ task.context.inputVersion.slice(0, 12) }}</p>
    <p v-if="report?.generatedAt" class="muted">v{{ report.version }} · 生成于 {{ new Date(report.generatedAt).toLocaleString('zh-CN') }}<span v-if="report.operatorId"> · 复核人 {{ report.operatorId }}</span></p>
    <p v-if="report" class="report-conclusion">{{ report.conclusion }}</p>
    <p v-if="report" class="muted">修订说明：{{ report.revisionReason }}<span v-if="task.status !== 'completed' && report.kind === 'final'"> · 已进入后续复核，本版为此前最终结论</span></p>
    <article v-for="(section, index) in report?.sections ?? []" :key="index" class="report-section"><h3>{{ sectionNames[section.sectionKey] }}</h3><CollapsibleText :text="section.content" /><div class="evidence-actions"><button v-for="id in section.citationRefs" :key="id" class="text-button" @click="emit('citation', id)">查看依据 · 第 {{ frozenCitations.find(c => c.citationId === id)?.page }} 页</button></div></article>
  </dialog>
</template>
