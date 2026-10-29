<script setup lang="ts">
import { computed, ref } from 'vue';
import type { AnalysisTask, Finding, FindingReviewRequest, ReviewRecordRequest } from '@casepilot/contracts';
import CollapsibleText from './CollapsibleText.vue';
import { checkLabels, decisionLabels } from '../domain/reviewExecution';

const props = defineProps<{ finding: Finding; task: AnalysisTask; busy: boolean }>();
const emit = defineEmits<{
  save: [id: string, body: Omit<FindingReviewRequest, 'expectedRevision'>];
  view: [value: Pick<ReviewRecordRequest, 'factRefs' | 'citationRefs' | 'supplementIds'>];
}>();
const comment = ref(''), followup = ref(''), changeReason = ref('');
const recipient = ref(''), missingItems = ref(''), evidenceViewed = ref(false);
const decision = ref<FindingReviewRequest['decision']>('pending');
const factRefs = ref<string[]>([]), citationRefs = ref<string[]>([]), supplementIds = ref<string[]>([]);
const viewingFact = ref('');
const reviews = computed(() => (props.task.reviewHistory ?? []).filter(r => r.findingId === props.finding.findingId));
const latest = computed(() => reviews.value.at(-1));
const facts = computed(() => props.task.facts.filter(f => (props.finding.factRefs ?? []).includes(f.factId)));
const selectedFact = computed(() => props.task.facts.find(f => f.factId === viewingFact.value));
const sources = computed(() => {
  const found = new Map<string, { documentId: string; page?: number }>();
  const add = (value: unknown) => {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return;
    const record = value as Record<string, unknown>;
    if (typeof record.documentId === 'string') found.set(record.documentId, {
      documentId: record.documentId, page: typeof record.page === 'number' ? record.page : undefined,
    });
  };
  for (const fact of facts.value) {
    add(fact.value);
    if (!fact.value || typeof fact.value !== 'object' || Array.isArray(fact.value)) continue;
    const refs = (fact.value as Record<string, unknown>).evidenceRefs;
    for (const ref of Array.isArray(refs) ? refs : []) add(props.task.facts.find(f => f.factId === `evidence:${ref}`)?.value);
  }
  return [...found.values()];
});
const editable = computed(() => ['waiting_review', 'failed', 'recoverable'].includes(props.task.status));
function save() {
  emit('save', props.finding.findingId, {
    decision: decision.value, comment: comment.value, factRefs: factRefs.value,
    citationRefs: citationRefs.value as FindingReviewRequest['citationRefs'], supplementIds: supplementIds.value as FindingReviewRequest['supplementIds'],
    followup: followup.value, changeReason: changeReason.value,
    findingVersion: props.finding.version, previousReviewId: latest.value?.reviewId ?? '',
    recipient: recipient.value, missingItems: missingItems.value, evidenceViewed: evidenceViewed.value,
  });
}
</script>

<template>
  <article class="node-finding" :class="finding.status">
    <div class="execution-heading">
      <span class="tag">{{ checkLabels[finding.status] }}</span><strong>{{ finding.title }}</strong>
      <span class="finding-source">{{ (finding.sources ?? []).length ? (finding.sources ?? []).join(' / ') : finding.source === 'human' ? '人工' : finding.source === 'ai' ? 'AI' : '规则' }}</span>
    </div>
    <p class="muted">{{ finding.findingId }} · {{ (finding.entityIds ?? []).join('、') }}</p>
    <CollapsibleText :text="finding.detail" />
    <p v-if="latest" class="muted">当前处理：{{ decisionLabels[latest.decision] }} · {{ latest.operatorId }} · {{ new Date(latest.at).toLocaleString('zh-CN') }}</p>
    <details class="finding-evidence">
      <summary>原始证据与判断依据</summary>
      <p v-if="!facts.length && !(finding.citationRefs ?? []).length" class="warning">本项原始依据不足，请补充核实。</p>
      <div v-for="fact in facts" :key="fact.factId" class="evidence-choice">
        <label><input v-model="factRefs" type="checkbox" :value="fact.factId" />作为复核依据</label>
        <button class="text-button" type="button" :disabled="busy" @click="viewingFact = fact.factId; emit('view', { factRefs: [fact.factId] })">查看 {{ fact.fieldPath }}</button>
        <a v-if="fact.materialId && fact.factId.startsWith('material_pages:')" :href="`/api/analyses/${task.id}/materials/${encodeURIComponent(fact.materialId)}/content#page=${fact.factId.split(':').at(-1)}`" target="_blank" rel="noopener">打开对应原始 PDF 页</a>
      </div>
      <CollapsibleText v-if="selectedFact" :text="typeof selectedFact.value === 'string' ? selectedFact.value : JSON.stringify(selectedFact.value, null, 2)" />
      <div v-for="source in sources" :key="source.documentId" class="evidence-choice"><a :href="`/api/analyses/${task.id}/materials/${encodeURIComponent(source.documentId)}/content${source.page ? '#page=' + source.page : ''}`" target="_blank" rel="noopener">查看原始材料 · {{ source.documentId }}<span v-if="source.page"> · 第 {{ source.page }} 页</span></a></div>
      <div v-for="id in finding.citationRefs" :key="id" class="evidence-choice">
        <label><input v-model="citationRefs" type="checkbox" :value="id" />作为条款依据</label>
        <button class="text-button" :disabled="busy" @click="emit('view', { citationRefs: [id] })">查看条款原文 · 第 {{ task.citations.find(c => c.citationId === id)?.page }} 页</button>
      </div>
      <div v-for="item in task.evidenceSupplements" :key="item.supplementId" class="evidence-choice">
        <label><input v-model="supplementIds" type="checkbox" :value="item.supplementId" />作为补充依据</label>
        <a :href="`/api/analyses/${task.id}/supplements/${item.supplementId}/content`" target="_blank" rel="noopener" @click="emit('view', { supplementIds: [item.supplementId] })">{{ item.title }} · v{{ item.version }}</a>
      </div>
    </details>
    <details v-if="editable" class="review-actions">
      <summary>{{ latest ? '修改本项复核' : '人工复核本项' }}</summary>
      <form class="inline-review" @submit.prevent="save">
        <p class="muted">当前复核人：{{ task.operatorId }}</p>
        <label>人工处理<select v-model="decision"><option v-for="(name, key) in decisionLabels" :key="key" :value="key">{{ name }}</option></select></label>
        <label>事实、判断理由及意见<textarea v-model="comment" maxlength="2000" required /></label>
        <label v-if="decision !== 'excluded'">建议后续动作<textarea v-model="followup" maxlength="1000" required /></label>
        <label v-if="decision === 'pending' || decision === 'referred'">跟进人员或接收岗位<input v-model="recipient" maxlength="200" required /></label>
        <label v-if="decision === 'pending'">缺少资料及待核实内容<textarea v-model="missingItems" maxlength="1000" required /></label>
        <label v-if="reviews.length">变更原因<input v-model="changeReason" maxlength="1000" required /></label>
        <label v-if="decision === 'confirmed' || decision === 'excluded'" class="checkbox-label"><input v-model="evidenceViewed" type="checkbox" required />已打开并查看所选依据</label>
        <button class="secondary" type="submit" :disabled="busy || task.operatorId === 'unidentified_operator'">保存本项复核</button>
      </form>
    </details>
    <details v-if="reviews.length"><summary>历次人工记录 · {{ reviews.length }}</summary>
      <div v-for="item in reviews" :key="item.reviewId" class="node-event">
        <p>{{ item.operatorId }} · {{ new Date(item.at).toLocaleString('zh-CN') }} · {{ decisionLabels[item.decision] }}</p>
        <CollapsibleText :text="item.comment + (item.changeReason ? '\n变更原因：' + item.changeReason : '')" />
      </div>
    </details>
  </article>
</template>
