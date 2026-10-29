<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { WorkspaceEvent, BusinessNode, ReviewRecordRequest } from '@casepilot/contracts';
import ReviewCasePreflight from '../components/ReviewCasePreflight.vue';
import CollapsibleText from '../components/CollapsibleText.vue';
import FindingReviewCard from '../components/FindingReviewCard.vue';
import NodeReviewActions from '../components/NodeReviewActions.vue';
import ReviewReportDialog from '../components/ReviewReportDialog.vue';
import CitationDialog from '../components/CitationDialog.vue';
import { useReviewCases } from '../composables/useReviewCases';
import { useWorkbench } from '../composables/useWorkbench';
import { label, formatMoney } from '../domain/reviewCases';
import { reviewStatus } from '../domain/presentation';
import { executionGroups, decisionLabels, recordLabels, unresolved } from '../domain/reviewExecution';
import ReviewCasePage from './ReviewCasePage.vue';

const { history, historyReady, task, pending, error, comment, citation, connection,
  selectCase, openTask, startReview, addSupplement, reanalyze, review, reviewFinding, saveReviewRecord, recover, showCitation } = useWorkbench();
const reviewCases = useReviewCases();
const detailCaseId = ref(''), preparing = ref(false), starting = ref(false);
const reportOpen = ref(false), reportVersion = ref<number>();
const evidenceOpen = ref(false), coverageConfirmed = ref(false);
const supplementFile = ref<File>(), supplementTitle = ref('');
const findingState = ref(''), findingSource = ref(''), findingObject = ref('');
const activeTask = computed(() => task.value?.caseId === reviewCases.selectedId.value ? task.value : undefined);
const caseHistory = computed(() => history.value.filter(t => t.caseId === reviewCases.selectedId.value));
const summary = computed(() => activeTask.value?.caseSummary ?? reviewCases.cases.value.find(c => c.id === reviewCases.selectedId.value));
const groups = computed(() => activeTask.value ? executionGroups(activeTask.value) : []);
const outstanding = computed(() => activeTask.value ? unresolved(activeTask.value) : []);
const latestReport = computed(() => activeTask.value?.report ?? activeTask.value?.reports?.at(-1));
const editable = computed(() => !!activeTask.value && ['waiting_review', 'failed', 'recoverable'].includes(activeTask.value.status));
function visibleFinding(finding: NonNullable<typeof activeTask.value>['reviewState']['findings'][number]) {
  const latest = activeTask.value?.reviewHistory?.filter(r => r.findingId === finding.findingId).at(-1);
  return (!findingState.value || (latest?.decision ?? 'pending_review') === findingState.value)
    && (!findingSource.value || finding.source === findingSource.value || (finding.sources ?? []).includes(findingSource.value as 'ai' | 'rule' | 'human'))
    && (!findingObject.value || (finding.entityIds ?? []).some(id => id.includes(findingObject.value)));
}
async function viewEvidence(nodeKey: BusinessNode['nodeKey'], refs: Pick<ReviewRecordRequest, 'factRefs' | 'citationRefs' | 'supplementIds'>) {
  await saveReviewRecord('evidence-views', { nodeKey, comment: '打开并查看当前事项的原始依据', ...refs });
  if (!error.value && refs.citationRefs?.length) await showEvidence(refs.citationRefs[0]);
}
let initialized = false;

watch([reviewCases.selectedId, historyReady], async ([id, ready]) => {
  reportOpen.value = false; evidenceOpen.value = false; preparing.value = false; coverageConfirmed.value = false;
  supplementFile.value = undefined; supplementTitle.value = '';
  if (ready && !initialized) {
    initialized = true;
    if (task.value && task.value.caseId !== id) { reviewCases.select(task.value.caseId); return; }
  }
  if (id && ready && task.value?.caseId !== id) await selectCase(id);
}, { immediate: true });
watch(() => activeTask.value?.id, () => { coverageConfirmed.value = false; reportOpen.value = false; evidenceOpen.value = false; supplementFile.value = undefined; supplementTitle.value = ''; });

async function startFromPreflight(caseId: string, inputVersion: string) {
  if (starting.value) return;
  starting.value = true;
  const predecessor = activeTask.value?.id;
  try { await startReview(caseId, inputVersion, predecessor); if (!error.value) preparing.value = false; }
  finally { starting.value = false; }
}
function showReport(version?: number) { reportVersion.value = version; reportOpen.value = true; }
async function showEvidence(id: string) { await showCitation(id); evidenceOpen.value = !!citation.value; }
function chooseSupplement(event: Event) {
  supplementFile.value = (event.target as HTMLInputElement).files?.[0];
  supplementTitle.value = supplementFile.value?.name.replace(/\.pdf$/i, '') ?? '';
}
async function upload(nodeKey: string) {
  if (!supplementFile.value || !supplementTitle.value.trim()) return;
  await addSupplement(supplementFile.value, supplementTitle.value, 'review_evidence', nodeKey);
  if (!error.value) { supplementFile.value = undefined; supplementTitle.value = ''; }
}
function eventText(event: WorkspaceEvent): string {
  switch (event.type) {
    case 'finding.reviewed': {
      const r = event.data.review;
      return `${r.operatorId} · ${decisionLabels[r.decision]}\n${r.comment}${r.followup ? '\n后续：' + r.followup : ''}${r.changeReason ? '\n变更原因：' + r.changeReason : ''}\n依据：${[...r.factRefs, ...r.citationRefs, ...r.supplementIds].join('、') || '已记录待核实内容'}`;
    }
    case 'review.accepted': return `${event.data.operatorId ?? '历史操作者未记录'} · ${event.data.decision === 'approve' ? '确认检查覆盖及报告内容' : '终止本次审查'}\n${event.data.comment ?? ''}`;
    case 'review.required': return event.data.reason;
    case 'report.saved': return `已生成${event.data.kind === 'final' ? '最终报告' : event.data.kind === 'stage' ? '阶段报告' : '待复核报告'} · v${event.data.version}\n${event.data.conclusion}`;
    case 'report.completed': return '最终审查报告已保存。';
    case 'evidence.supplemented': return `${event.data.supplement.addedBy} · 追加证据：${event.data.supplement.title} · v${event.data.supplement.version}`;
    default: return '';
  }
}
</script>

<template>
  <ReviewCasePage v-if="detailCaseId" :case-id="detailCaseId" @back="detailCaseId = ''" />
  <main v-else>
    <header><div><span class="eyebrow">CASEPILOT / REVIEW WORKSPACE</span><h1>结案赔案审查工作台</h1></div><span class="api-dot">● {{ connection }}</span></header>
    <div v-if="error" class="error-banner" role="alert">{{ error }}</div>
    <section class="layout">
      <aside class="panel case-browser" aria-label="案件查询">
        <h2>案件</h2>
        <form class="case-search" @submit.prevent="reviewCases.search">
          <div class="search-row"><select v-model="reviewCases.filters.queryType" aria-label="查询类型"><option value="claim_number">赔案号</option><option value="report_number">报案号</option><option value="plate_number">车牌号</option></select><input v-model="reviewCases.filters.query" maxlength="100" placeholder="输入查询关键字" /></div>
          <details><summary>筛选条件</summary><label>结案开始日期<input v-model="reviewCases.filters.closedFrom" type="date" /></label><label>结案结束日期<input v-model="reviewCases.filters.closedTo" type="date" /></label><label>人伤情况<select v-model="reviewCases.filters.injuryStatus"><option value="">全部</option><option value="no_injury_reported">原档案记录未报人伤</option><option value="injury_reported">原档案记录有人伤</option><option value="unknown">原档案未明确</option><option value="conflicting_information">信息冲突</option></select></label><label>审查进度<select v-model="reviewCases.filters.reviewStatus"><option value="">全部</option><option value="not_started">未启动</option><option value="running">执行中</option><option value="pending_review">待人工复核</option><option value="pending_verification">待核实</option><option value="vehicle_review_completed">车损审查完成</option><option value="failed">执行失败</option><option value="awaiting_recovery">待恢复</option></select></label></details>
          <div class="search-actions"><button type="button" class="secondary" @click="reviewCases.reset">重置</button><button type="submit" class="primary" :disabled="reviewCases.pending.value">查询</button></div>
        </form>
        <p v-if="reviewCases.pending.value" class="muted">正在加载案件…</p>
        <p v-else-if="reviewCases.dataStatus.value === 'not_imported'" class="muted">尚未导入案件数据。</p>
        <p v-else-if="!reviewCases.cases.value.length" class="muted">没有符合当前条件的案件。</p>
        <button v-for="claim in reviewCases.cases.value" :key="claim.id" class="case-card compact-case-card" :class="{ active: claim.id === reviewCases.selectedId.value }" @click="reviewCases.select(claim.id)">
          <span class="case-card-heading"><strong>{{ claim.id }}</strong><span class="status-pill">{{ history.find(t => t.caseId === claim.id) ? reviewStatus(history.find(t => t.caseId === claim.id)!) : label(claim.latestReviewStatus) }}</span></span><small class="truncate" :title="claim.targetClaims.map(c => c.claimNumber).join('、')">{{ claim.targetClaims.map(c => c.claimNumber).join('、') }}</small><small class="case-card-meta"><span class="truncate">{{ claim.vehicles.map(v => v.plateNumber).join('、') }}</span><time>{{ claim.targetClaims[0]?.closedAt.slice(0, 10) }}</time></small>
        </button>
        <div v-if="reviewCases.error.value" class="error-inline" role="alert">{{ reviewCases.error.value }}<button class="secondary" @click="reviewCases.search">重新加载</button></div>
      </aside>

      <section class="workspace unified-workspace" :aria-busy="pending">
        <section v-if="summary" class="panel current-case" aria-label="当前案件">
          <div class="case-overview"><div><span class="eyebrow">当前案件</span><h2>{{ summary.id }} <span class="status-pill">{{ activeTask ? reviewStatus(activeTask) : pending ? '正在加载审查记录' : '未启动审查' }}</span></h2><p>{{ summary.vehicles.map(v => v.plateNumber).join('、') }} · {{ label(summary.injuryStatus) }}</p><p class="muted">{{ summary.targetClaims.map(c => c.claimNumber).join('、') }}</p></div><div class="amount-summary"><span>原核赔金额<strong>{{ formatMoney(summary.originalApprovedAmount) }}</strong></span><span>有效实付金额<strong>{{ formatMoney(summary.effectivePaidAmount) }}</strong></span></div></div>
          <p v-if="latestReport" class="report-conclusion">{{ latestReport.conclusion ?? '历史报告，请核对审查范围及未决事项。' }}</p>
          <p v-if="activeTask" class="muted">当前任务 {{ activeTask.id.slice(0, 8) }} · 输入版本 {{ activeTask.context.inputVersion.slice(0, 12) }}<span v-if="activeTask.predecessorAnalysisId"> · 前序任务 {{ activeTask.predecessorAnalysisId.slice(0, 8) }}</span></p>
          <div class="case-actions"><button class="secondary" @click="detailCaseId = summary.id">案件详情</button><button class="primary" :disabled="!latestReport" @click="showReport()">案件分析报告</button><button v-if="activeTask" class="secondary" :disabled="pending" @click="preparing = !preparing">{{ preparing ? '取消重新审查' : '重新审查' }}</button><button v-if="activeTask?.evidenceSupplements.length" class="secondary" :disabled="pending" @click="reanalyze">基于补充资料重新审查</button></div>
          <details class="case-history"><summary>历史分析任务 · {{ caseHistory.length }}</summary><p v-if="!caseHistory.length" class="muted">当前案件尚无分析任务。</p><button v-for="item in caseHistory" :key="item.id" class="history-card" :class="{ active: activeTask?.id === item.id }" @click="openTask(item.id)"><span>{{ item.id.slice(0, 8) }} · {{ item.execution.timeline[0]?.at ? new Date(item.execution.timeline[0].at).toLocaleString('zh-CN') : '历史任务' }}<small>{{ item.report?.kind === 'final' ? '最终报告' : item.report ? '待复核 / 阶段报告' : '尚无报告' }}</small></span>{{ reviewStatus(item) }}</button></details>
        </section>

        <ReviewCasePreflight v-if="summary && (!pending || starting)" :case-id="summary.id" :task="preparing ? undefined : activeTask" :busy="starting" @start="startFromPreflight" />
        <section class="panel execution-panel" aria-label="执行记录">
          <div class="execution-heading"><h2>执行记录</h2><span v-if="activeTask && (activeTask.checks ?? []).length" class="muted">业务疑点 {{ (activeTask.checks ?? []).filter(c => c.status === 'issue').length }} · 受限事项 {{ (activeTask.checks ?? []).filter(c => c.status === 'limited').length }}</span></div>
          <p v-if="pending && !starting" class="muted">正在加载所选案件的审查记录…</p>
          <p v-else-if="!activeTask" class="muted">尚未启动审查。启动后将在这里显示实际执行流程和结论。</p>
          <template v-else>
            <div v-if="activeTask.error" class="error-inline">{{ activeTask.error.message }} · {{ activeTask.error.code }}<button v-if="activeTask.status === 'recoverable'" class="secondary" :disabled="pending" @click="recover">从已保存进度恢复</button></div>
            <div class="finding-filters"><label>处理状态<select v-model="findingState"><option value="">全部</option><option value="pending_review">待复核</option><option v-for="(name, key) in decisionLabels" :key="key" :value="key">{{ name }}</option></select></label><label>来源<select v-model="findingSource"><option value="">全部</option><option value="rule">规则</option><option value="ai">AI</option><option value="human">人工</option></select></label><label>涉及对象<input v-model="findingObject" placeholder="对象编号" /></label></div>
            <button v-if="activeTask.reviewState.businessNodes.some(n => n.status === 'failed') && editable" class="secondary" :disabled="pending" @click="recover">显式恢复失败检查</button>
            <article v-for="(group, index) in groups" :key="group.key" class="review-node" :data-node="group.key">
              <div class="node-marker">{{ index + 1 }}</div><div class="node-content"><div class="node-heading"><h3>{{ group.name }}</h3><span class="status-pill">{{ group.status }}</span></div>
                <p class="muted">{{ group.node.summary }} · {{ group.node.durationMs }} ms</p><p v-if="group.node.reason" class="warning">{{ group.node.reason }}</p>
                <details v-if="group.entries.length" class="node-tools"><summary>执行明细 · {{ group.entries.length }} 项</summary><div v-for="entry in group.entries" :key="entry.executionId" class="tool-record"><span>{{ entry.name }} <span v-if="entry.key.startsWith('model:')" class="ai-badge">AI</span></span><small>{{ entry.status === 'completed' ? '已完成' : entry.status === 'running' ? '执行中' : '执行失败' }} · 第 {{ entry.attempt }} 次 · {{ entry.durationMs }} ms<span v-if="entry.startedAt"> · {{ new Date(entry.startedAt).toLocaleString('zh-CN') }}</span></small><CollapsibleText :text="entry.summary" /></div></details>
                <CollapsibleText v-if="group.positiveText" :text="group.positiveText" />
                <FindingReviewCard v-for="finding in group.findings.filter(visibleFinding)" :key="activeTask.id + ':' + finding.findingId" :finding="finding" :task="activeTask" :busy="pending" @save="reviewFinding" @view="value => viewEvidence(group.key, value)" />
                <NodeReviewActions :task="activeTask" :node-key="group.key" :busy="pending" @save="saveReviewRecord" />
                <div v-for="record in group.records" :key="record.recordId" class="node-event"><time>{{ new Date(record.at).toLocaleString('zh-CN') }} · {{ record.operatorId }} · {{ recordLabels[record.kind] }}</time><CollapsibleText :text="[record.comment, record.steps, record.result, record.recipient, record.state, record.source].filter(Boolean).join('\n')" /></div>
                <div v-for="event in group.events" :key="event.seq" class="node-event"><time>{{ new Date(event.at).toLocaleString('zh-CN') }}</time><CollapsibleText :text="eventText(event)" /><button v-if="event.type === 'report.saved'" class="text-button" @click="showReport(event.data.version)">查看此版本报告</button></div>
                <details v-if="editable" class="node-supplement"><summary>补充本节点证据</summary><label>PDF 文件<input type="file" accept="application/pdf,.pdf" @change="chooseSupplement" /></label><label>材料名称<input v-model="supplementTitle" maxlength="200" /></label><button class="secondary" :disabled="pending || !supplementFile || !supplementTitle.trim()" @click="upload(group.key)">追加证据</button></details>
                <form v-if="group.key === 'report' && editable" class="coverage-review" @submit.prevent="review('approve')"><h4>人工确认检查覆盖及报告</h4><p class="muted">当前复核人：{{ activeTask.operatorId === 'unidentified_operator' ? '未识别' : activeTask.operatorId }}</p><p v-if="outstanding.length" class="preflight-warning">尚有 {{ outstanding.length }} 项未决检查，请到对应节点处理。可先查看阶段报告。</p><ul v-if="outstanding.length" class="preflight-warning"><li v-for="reason in outstanding" :key="reason">{{ reason }}</li></ul><label class="checkbox-label"><input v-model="coverageConfirmed" type="checkbox" />我已查看检查覆盖、范围限制及报告内容</label><label>复核意见<textarea v-model="comment" maxlength="2000" required placeholder="说明检查范围、覆盖情况及最终认定" /></label><p v-if="activeTask.operatorId === 'unidentified_operator'" class="warning">当前操作者未识别，暂不能完成正式审查。</p><div class="actions"><button type="button" class="secondary" :disabled="pending" @click="review('reject')">终止本次审查</button><button class="primary" type="submit" :disabled="pending || !coverageConfirmed || comment.trim().length < 5 || outstanding.length > 0 || activeTask.operatorId === 'unidentified_operator'">确认并生成最终报告</button></div></form>
              </div>
            </article>
          </template>
        </section>
      </section>
    </section>
    <ReviewReportDialog v-if="reportOpen && activeTask" :key="activeTask.id" :task="activeTask" :version="reportVersion" @close="reportOpen = false" @citation="showEvidence" />
    <CitationDialog v-if="evidenceOpen && citation" :citation="citation" @close="evidenceOpen = false" />
  </main>
</template>
