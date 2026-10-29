<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { AnalysisTask, BusinessNode, ManualFindingRequest, ReviewRecordRequest } from '@casepilot/contracts';
import CollapsibleText from './CollapsibleText.vue';

const props = defineProps<{ task: AnalysisTask; nodeKey: BusinessNode['nodeKey']; busy: boolean }>();
const emit = defineEmits<{ save: [action: string, body: Omit<ReviewRecordRequest, 'expectedRevision'> | Omit<ManualFindingRequest, 'expectedRevision'>] }>();
const action = ref('findings'), targetId = ref(''), comment = ref(''), result = ref(''), steps = ref('');
const title = ref(''), entityId = ref(''), recipient = ref(''), source = ref(''), state = ref('');
const inputs = ref(''), operation = ref<'sum' | 'difference'>('sum'), resultFen = ref<number>();
const factRefs = ref<string[]>([]), citationRefs = ref<string[]>([]), supplementIds = ref<string[]>([]), checkIds = ref<string[]>([]);
const search = ref(''), viewedFact = ref('');
const completed = computed(() => props.task.status === 'completed');
const options = computed(() => completed.value
  ? props.nodeKey === 'report' ? { 'reopen-review': '更正审查结论' } : { 'followup-records': '更新后续办理' }
  : { findings: '补充发现', 'human-completions': '记录人工补做', 'scope-adjustments': '调整本次范围', 'professional-records': '记录专业复核', 'followup-records': '记录后续办理', 'business-records': '补充业务记录' });
const plans = computed(() => props.task.reviewState.checkPlan.filter(p => p.nodeKey === props.nodeKey));
const findings = computed(() => props.task.reviewState.findings.filter(f => f.nodeKey === props.nodeKey && f.active));
const targets = computed(() => action.value === 'human-completions' ? plans.value.map(p => ({ id: p.checkId, title: p.title })) : findings.value.map(f => ({ id: f.findingId, title: f.title })));
const facts = computed(() => props.task.facts.filter(f => !search.value || (f.fieldPath + JSON.stringify(f.value)).includes(search.value)));
const selectedFact = computed(() => props.task.facts.find(f => f.factId === viewedFact.value));
const objects = computed(() => [...new Set(props.task.facts.flatMap(f => f.value && typeof f.value === 'object' && !Array.isArray(f.value) ? Object.entries(f.value).filter(([k, v]) => k.endsWith('Id') && typeof v === 'string').map(([, v]) => String(v)) : []))]);
const stateOptions = computed(() => action.value === 'scope-adjustments' ? { exclude: '排除所选检查', restore: '恢复所选检查' } : action.value === 'professional-records' ? { registered: '登记接收对象', following: '跟进中', opinion_received: '收到专业意见' } : { unhandled: '尚未办理', following: '办理中', completed: '已办理' });
watch([completed, action], () => {
  if (!(action.value in options.value)) action.value = Object.keys(options.value)[0];
  targetId.value = ''; state.value = Object.keys(stateOptions.value)[0];
}, { immediate: true });

function base(): Omit<ReviewRecordRequest, 'expectedRevision'> {
  return { nodeKey: props.nodeKey, targetId: targetId.value, comment: comment.value,
    factRefs: factRefs.value, citationRefs: citationRefs.value as ReviewRecordRequest['citationRefs'], supplementIds: supplementIds.value as ReviewRecordRequest['supplementIds'],
    checkIds: checkIds.value, steps: steps.value, result: result.value, recipient: recipient.value,
    source: source.value, state: action.value === 'human-completions' ? 'completed' : state.value };
}
function view(refs: Pick<ReviewRecordRequest, 'factRefs' | 'citationRefs' | 'supplementIds'>) {
  emit('save', 'evidence-views', { nodeKey: props.nodeKey, comment: '已打开本节点的原始依据', ...refs });
}
function save() {
  if (action.value === 'findings') {
    emit('save', action.value, { nodeKey: props.nodeKey, title: title.value, detail: comment.value,
      entityIds: [entityId.value], factRefs: factRefs.value, citationRefs: citationRefs.value as ManualFindingRequest['citationRefs'],
      supplementIds: supplementIds.value as ManualFindingRequest['supplementIds'], recommendation: result.value });
    return;
  }
  const body = base();
  if (action.value === 'human-completions' && props.nodeKey === 'amount') {
    body.inputsFen = inputs.value.split(/[,，\s]+/).filter(Boolean).map(Number);
    body.operation = operation.value; body.resultFen = resultFen.value;
  }
  emit('save', action.value, body);
}
</script>

<template>
  <details v-if="!['queued', 'running', 'resuming', 'rejected'].includes(task.status)" class="review-actions">
    <summary>本节点人工操作</summary>
    <form class="inline-review" @submit.prevent="save">
      <label>操作<select v-model="action"><option v-for="(name, key) in options" :key="key" :value="key">{{ name }}</option></select></label>
      <template v-if="action === 'findings'">
        <label>问题标题<input v-model="title" maxlength="200" required /></label>
        <label>涉及对象<select v-model="entityId" required><option value="" disabled>请选择</option><option v-for="id in objects" :key="id">{{ id }}</option></select></label>
      </template>
      <label v-if="['human-completions', 'professional-records', 'followup-records'].includes(action)">对应事项<select v-model="targetId" required><option value="" disabled>请选择</option><option v-for="target in targets" :key="target.id" :value="target.id">{{ target.title }}</option></select></label>
      <div v-if="action === 'scope-adjustments'"><label v-for="item in plans" :key="item.checkId"><input v-model="checkIds" type="checkbox" :value="item.checkId" />{{ item.title }}</label></div>
      <label>意见或变更原因<textarea v-model="comment" minlength="5" maxlength="2000" required /></label>
      <label v-if="action !== 'reopen-review'">结果、影响或后续建议<textarea v-model="result" maxlength="3000" required /></label>
      <label v-if="action === 'human-completions'">实际检查步骤<textarea v-model="steps" maxlength="3000" required /></label>
      <template v-if="action === 'human-completions' && nodeKey === 'amount'">
        <label>计算输入（单位：分，逗号分隔）<input v-model="inputs" required /></label>
        <label>运算<select v-model="operation"><option value="sum">加总</option><option value="difference">差额</option></select></label>
        <label>核算结果（分）<input v-model.number="resultFen" type="number" step="1" required /></label>
      </template>
      <template v-if="['professional-records', 'followup-records'].includes(action)">
        <label>接收人员或责任岗位<input v-model="recipient" maxlength="200" required /></label>
      </template>
      <label v-if="['professional-records', 'followup-records', 'scope-adjustments'].includes(action)">状态<select v-model="state"><option v-for="(name, key) in stateOptions" :key="key" :value="key">{{ name }}</option></select></label>
      <label v-if="['professional-records', 'followup-records', 'business-records'].includes(action)">意见或记录来源<input v-model="source" maxlength="500" required /></label>
      <details v-if="!completed || action === 'followup-records'">
        <summary>选择并查看依据</summary>
        <input v-model="search" placeholder="筛选原始记录" aria-label="筛选原始记录" />
        <div v-for="fact in facts" :key="fact.factId" class="evidence-choice">
          <label><input v-model="factRefs" type="checkbox" :value="fact.factId" />{{ fact.fieldPath }}</label>
          <button class="text-button" type="button" :disabled="busy" @click="viewedFact = fact.factId; view({ factRefs: [fact.factId] })">查看记录</button>
        </div>
        <CollapsibleText v-if="selectedFact" :text="typeof selectedFact.value === 'string' ? selectedFact.value : JSON.stringify(selectedFact.value, null, 2)" />
        <div v-for="citation in task.citations" :key="citation.citationId" class="evidence-choice">
          <label><input v-model="citationRefs" type="checkbox" :value="citation.citationId" />{{ citation.fileName }} · 第 {{ citation.page }} 页</label>
          <details @toggle="(event) => { if ((event.target as HTMLDetailsElement).open) view({ citationRefs: [citation.citationId] }); }"><summary>查看条款</summary>{{ citation.content }}</details>
        </div>
        <div v-for="supplement in task.evidenceSupplements" :key="supplement.supplementId" class="evidence-choice">
          <label><input v-model="supplementIds" type="checkbox" :value="supplement.supplementId" />{{ supplement.title }}</label>
          <a :href="`/api/analyses/${task.id}/supplements/${supplement.supplementId}/content`" target="_blank" rel="noopener" @click="view({ supplementIds: [supplement.supplementId] })">打开原文</a>
        </div>
      </details>
      <button class="secondary" :disabled="busy || task.operatorId === 'unidentified_operator'">保存人工记录</button>
    </form>
  </details>
</template>
