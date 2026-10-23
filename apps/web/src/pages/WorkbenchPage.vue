<script setup lang="ts">
import CaseNavigation from '../components/CaseNavigation.vue';
import CaseSummary from '../components/CaseSummary.vue';
import ExecutionTimeline from '../components/ExecutionTimeline.vue';
import ReviewPanel from '../components/ReviewPanel.vue';
import ReportPanel from '../components/ReportPanel.vue';
import { useWorkbench } from '../composables/useWorkbench';
import { statusText } from '../domain/presentation';

const { cases, history, selectedId, task, selected, pending, running, error, comment,
  connection, selectCase, openTask, start, review } = useWorkbench();
const steps = ['案件查询', '规则核验', '条款检索', '人工审核', '报告生成'];
</script>

<template>
  <main>
    <header><div><span class="eyebrow">CASEPILOT / CLAIM INTELLIGENCE</span><h1>理赔案件分析工作台</h1></div><span class="api-dot">● {{ connection }}</span></header>
    <div class="prototype-note">功能验证原型 · 数据和条款均为虚构示例 · 规则驱动分析 / 关键词检索 · 结果仅供演示</div>
    <div v-if="error" class="error-banner" role="alert">{{ error }}</div>
    <section class="layout">
      <CaseNavigation :cases="cases" :history="history" :selected-id="selectedId" :task-id="task?.id" :pending="pending" @select-case="selectCase" @open-task="openTask" />
      <section class="workspace">
        <CaseSummary v-if="selected" :selected="selected" :running="running" @start="start" />
        <div class="workflow-strip"><span v-for="(step, index) in steps" :key="step">{{ index + 1 }}. {{ step }}</span></div>
        <div v-if="!task" class="empty panel"><div class="orbit">CP</div><h2>从事实到依据，串联每一步分析</h2><p>选择案件并启动分析，实时查看核验结果与条款依据。<br>疑点案件暂停等待审核，常规案件直接生成报告。</p></div>
        <template v-else>
          <div class="status-row"><span class="status" :class="task.status">{{ statusText[task.status] }}</span><code>{{ task.id.slice(0, 8) }}</code></div>
          <div class="grid">
            <ExecutionTimeline :events="task.events" />
            <section>
              <ReviewPanel v-if="task.status === 'waiting_review'" v-model:comment="comment" :findings="task.findings" :pending="pending" @review="review" />
              <ReportPanel v-else-if="task.report" :report="task.report" :claim="selected" />
              <div v-else class="panel result-placeholder"><h2>{{ task.status === 'rejected' ? '本次分析已驳回' : task.status === 'failed' ? '分析执行失败' : '正在分析案件' }}</h2><p>{{ task.events.at(-1)?.detail }}</p></div>
            </section>
          </div>
        </template>
      </section>
    </section>
  </main>
</template>
