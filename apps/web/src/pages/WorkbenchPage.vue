<script setup lang="ts">
import { computed, ref } from 'vue';
import CaseSummary from '../components/CaseSummary.vue';
import ModelFindingCard from '../components/ModelFindingCard.vue';
import ReportPanel from '../components/ReportPanel.vue';
import ReportSectionCard from '../components/ReportSectionCard.vue';
import ReviewCaseSummary from '../components/ReviewCaseSummary.vue';
import RuleFindingCard from '../components/RuleFindingCard.vue';
import { useReviewCases } from '../composables/useReviewCases';
import { useWorkbench } from '../composables/useWorkbench';
import { label } from '../domain/reviewCases';
import { statusText } from '../domain/presentation';
import ReviewCasePage from './ReviewCasePage.vue';

const { history, task, selected, pending, running, error, question, comment,
  conversation, conversations, citation, connection, openTask, openConversation, start, review, recover, showCitation, olderMessages } = useWorkbench();
const reviewCases = useReviewCases();
const detailCaseId = ref('');
const selectedReviewCase = computed(() => reviewCases.cases.value.find(item => item.id === reviewCases.selectedId.value));
const sectionNames = { summary: '案件摘要', findings: '疑点与依据', recommendations: '处理建议' };
const executionStatus = { running: '执行中', completed: '已完成', failed: '失败' };
const executionRecords = computed(() => {
  if (task.value?.schemaVersion !== 1) return [];
  const entries = [...task.value.execution.nodes, ...task.value.execution.tools];
  return task.value.execution.timeline.filter(e => e.type === 'node.started' || e.type === 'tool.started').flatMap(e => {
    if (e.type !== 'node.started' && e.type !== 'tool.started') return [];
    const entry = entries.find(x => x.executionId === e.data.executionId);
    return entry ? [entry] : [];
  });
});

function clearReviewCase() {
  reviewCases.selectedId.value = '';
}
async function showTask(id: string) { clearReviewCase(); await openTask(id); }
async function showConversation(id: string) { clearReviewCase(); await openConversation(id); }
</script>

<template>
  <ReviewCasePage v-if="detailCaseId" :case-id="detailCaseId" @back="detailCaseId = ''" />
  <main v-else>
    <header><div><span class="eyebrow">CASEPILOT / AGENT WORKSPACE</span><h1>理赔案件分析工作台</h1></div><span class="api-dot">● {{ connection }}</span></header>
    <div class="prototype-note">演示案件 · C01–C03 支持查询、详情及材料查看 · 分析结果仍需由业务人员核验</div>
    <div v-if="error" class="error-banner" role="alert">{{ error }}</div>
    <section class="layout">
      <aside class="panel case-browser">
        <h2>案件</h2>
        <form class="case-search" @submit.prevent="reviewCases.search">
          <div class="search-row"><select v-model="reviewCases.filters.queryType" aria-label="查询类型"><option value="claim_number">赔案号</option><option value="report_number">报案号</option><option value="plate_number">车牌号</option></select><input v-model="reviewCases.filters.query" maxlength="100" placeholder="输入查询关键字" /></div>
          <details><summary>筛选条件</summary><label>结案开始日期<input v-model="reviewCases.filters.closedFrom" type="date" /></label><label>结案结束日期<input v-model="reviewCases.filters.closedTo" type="date" /></label><label>人伤情况<select v-model="reviewCases.filters.injuryStatus"><option value="">全部</option><option value="no_injury_reported">原档案记录未报人伤</option><option value="injury_reported">原档案记录有人伤</option><option value="unknown">原档案未明确</option><option value="conflicting_information">信息冲突</option></select></label><label>审查进度<select v-model="reviewCases.filters.reviewStatus"><option value="">全部</option><option value="not_started">未启动</option><option value="running">执行中</option><option value="pending_review">待人工复核</option><option value="pending_verification">待核实</option><option value="vehicle_review_completed">车损审查完成</option><option value="failed">执行失败</option><option value="awaiting_recovery">待恢复</option></select></label></details>
          <div class="search-actions"><button type="button" class="secondary" @click="reviewCases.reset">重置</button><button type="submit" class="primary" :disabled="reviewCases.pending.value">查询</button></div>
        </form>
        <p v-if="reviewCases.pending.value && !reviewCases.cases.value.length" class="muted">正在加载案件…</p>
        <p v-else-if="reviewCases.dataStatus.value === 'not_imported'" class="muted">尚未导入案件数据。</p>
        <p v-else-if="!reviewCases.cases.value.length" class="muted">没有符合当前条件的案件。</p>
        <button v-for="claim in reviewCases.cases.value" :key="claim.id" class="case-card compact-case-card" :class="{ active: claim.id === reviewCases.selectedId.value }" @click="reviewCases.select(claim.id)">
          <span class="case-card-heading"><strong>{{ claim.id }}</strong><span class="status-pill">{{ label(claim.latestReviewStatus) }}</span></span>
          <small class="truncate" :title="claim.targetClaims.map(item => item.claimNumber).join('、')">{{ claim.targetClaims.map(item => item.claimNumber).join('、') }}</small>
          <small class="case-card-meta"><span class="truncate">{{ claim.vehicles.map(item => item.plateNumber).join('、') }}</span><time>{{ claim.targetClaims[0]?.closedAt.slice(0, 10) }}</time></small>
        </button>
        <div v-if="reviewCases.error.value" class="error-inline" role="alert">{{ reviewCases.error.value }}<button type="button" class="secondary" @click="reviewCases.search">重新加载</button></div>
        <template v-if="!reviewCases.selectedId.value">
          <h3>当前案件会话</h3>
          <button v-for="item in conversations" :key="item.id" class="history-card" :class="{ active: conversation?.id === item.id }" @click="showConversation(item.id)">{{ item.title }}<small>{{ item.id.slice(0, 8) }}</small></button>
        </template>
        <h3>历史分析任务</h3>
        <button v-for="item in history" :key="item.id" class="history-card" :class="{ active: task?.id === item.id && !reviewCases.selectedId.value }" @click="showTask(item.id)"><span>{{ item.schemaVersion === 0 ? '历史报告 · 只读' : 'V1 分析' }}<small>{{ item.id.slice(0, 8) }}</small></span>{{ statusText[item.status] }}</button>
      </aside>
      <section class="workspace">
        <template v-if="reviewCases.selectedId.value">
          <ReviewCaseSummary v-if="selectedReviewCase" :summary="selectedReviewCase" @open="detailCaseId = selectedReviewCase.id" />
          <div v-else-if="reviewCases.pending.value" class="panel empty"><div class="orbit">···</div><h2>正在加载案件摘要</h2></div>
        </template>
        <template v-else>
          <CaseSummary v-if="selected" :selected="selected" :running="pending" @start="start(true)" />
          <section v-if="conversation" class="panel conversation">
            <h2>{{ conversation.title }}</h2><button v-if="conversation.nextBefore" class="secondary" @click="olderMessages">加载更早消息</button>
            <article v-for="message in conversation.messages" :key="message.id" :class="['message', message.role]"><strong>{{ message.role === 'user' ? '提问' : '已完成回答' }}</strong><p>{{ message.content }}</p><button class="secondary" @click="showTask(message.analysisId)">查看对应任务</button></article><p v-if="!conversation.messages.length">会话还没有消息。</p>
          </section>
          <form class="panel composer" @submit.prevent="start(false)"><label for="analysis-question">{{ conversation ? '继续当前会话' : '开始案件分析' }}</label><textarea id="analysis-question" v-model="question" maxlength="2000" placeholder="输入问题，例如：本案还需要补充哪些材料？" /><button class="primary" :disabled="running">{{ running ? '当前会话有任务执行或等待处理' : '发送并分析' }}</button></form>
          <template v-if="task">
            <div class="status-row"><span class="status" :class="task.status">{{ statusText[task.status] }}</span><code>{{ task.id }}</code></div>
            <template v-if="task.schemaVersion === 0"><p class="warning">历史报告只读，保留原有分析内容。</p><ReportPanel v-if="task.report" :report="task.report" :claim="selected" /></template>
            <template v-else-if="task.schemaVersion === 1">
              <div v-if="task.error" class="error-banner" role="alert">{{ task.error.message }}<small> {{ task.error.code }} · {{ task.error.requestId }}</small></div><button v-if="task.status === 'recoverable'" class="primary" :disabled="pending" @click="recover">从已保存进度恢复</button>
              <div class="grid"><section class="panel"><h2>执行记录</h2><p v-if="!task.execution.nodes.length && !task.execution.tools.length">任务已接收，等待执行。</p><article v-for="entry in executionRecords" :key="entry.executionId" class="finding"><strong>{{ entry.name }}</strong><p>{{ executionStatus[entry.status] }} · 第 {{ entry.attempt }} 次 · {{ entry.durationMs }} ms</p><small>{{ entry.summary }}</small></article><h3>规则核验</h3><RuleFindingCard v-for="finding in task.ruleFindings" :key="finding.code" :finding="finding" /><h3>模型发现</h3><ModelFindingCard v-for="(finding, i) in task.modelFindings" :key="i" :finding="finding" @citation="showCitation" /></section>
                <section><section v-if="task.pendingReview && task.status === 'waiting_review'" class="panel review"><h2>等待人工审核</h2><p>{{ task.pendingReview.reason }}</p><label for="review-comment">审核意见</label><textarea id="review-comment" v-model="comment" maxlength="2000" /><div class="actions"><button class="danger" :disabled="pending" @click="review('reject')">驳回</button><button class="primary" :disabled="pending" @click="review('approve')">通过并继续</button></div></section><section class="panel report"><h2>{{ task.report ? '案件分析报告' : '报告生成进度' }}</h2><p v-if="!task.report" class="warning">{{ task.status === 'rejected' ? '本次分析已驳回。' : '以下为已保存的段落，完整报告尚未形成。' }}</p><p v-if="task.report?.insufficientEvidence" class="warning">依据不足，请补充材料或条款后核验。</p><ReportSectionCard v-for="section in task.sections" :key="section.sectionKey" :section="section" :title="sectionNames[section.sectionKey]" @citation="showCitation" /></section></section></div>
              <section v-if="citation" class="panel citation" aria-label="引用依据"><h2>{{ citation.citation.fileName }} · 第 {{ citation.citation.page }} 页</h2><small>{{ citation.citation.productCode }} / {{ citation.citation.clauseVersion }} · 知识版本 {{ citation.citation.generationId }}</small><h3>引用原文</h3><p class="preserve-text">{{ citation.citation.content }}</p><h3>前一段<span v-if="citation.previous"> · 第 {{ citation.previous.page }} 页</span></h3><p class="preserve-text">{{ citation.previous?.content ?? '已到文档开头。' }}</p><h3>后一段<span v-if="citation.next"> · 第 {{ citation.next.page }} 页</span></h3><p class="preserve-text">{{ citation.next?.content ?? '已到文档末尾。' }}</p><small>相邻段落仅辅助阅读，不自动成为本报告已引用的依据。</small></section>
            </template>
          </template>
        </template>
      </section>
    </section>
  </main>
</template>
