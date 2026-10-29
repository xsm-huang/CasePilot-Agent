<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue';
import type { ReviewPreflight, AnalysisTask } from '@casepilot/contracts';
import { reviewCasesApi } from '../api/reviewCases';
import { createRequestScope } from '../domain/requestScope';

const props = defineProps<{ caseId: string; busy?: boolean; task?: AnalysisTask }>();
const emit = defineEmits<{ start: [caseId: string, inputVersion: string] }>();
const preflight = ref<ReviewPreflight>();
const pending = ref(false);
const error = ref('');
const scopes = createRequestScope();

async function load() {
  const scope = scopes.next();
  pending.value = true;
  error.value = '';
  preflight.value = undefined;
  if (props.task) { pending.value = false; return; }
  try {
    const value = await reviewCasesApi.preflight(props.caseId, scope.signal);
    if (scope.isCurrent()) preflight.value = value;
  } catch (cause) {
    if (scope.isCurrent()) error.value = String(cause);
  } finally {
    if (scope.isCurrent()) pending.value = false;
  }
}

watch(() => [props.caseId, props.task?.id], () => { void load(); }, { immediate: true });
onBeforeUnmount(() => scopes.dispose());
</script>

<template>
  <section class="panel review-preflight compact-preflight">
    <template v-if="task">
      <div class="preflight-heading"><strong>启动前检查</strong><span class="muted">本次任务固定输入 · {{ task.context.inputVersion.slice(0, 12) }}</span></div>
      <details><summary>查看审查范围、资料及条款版本</summary><p>固定材料 {{ Array.isArray(task.caseSnapshot.payload.documents) ? task.caseSnapshot.payload.documents.length : 0 }} 份 · 条款 {{ task.context.knowledgeBindings.length }} 个版本</p><p v-for="item in task.caseSnapshot.scopeItems" :key="item.scopeItemId">{{ item.title }} · {{ item.status === 'executable' ? '可执行' : '受限' }}<span v-if="item.reason">：{{ item.reason }}</span></p><p v-for="item in task.context.knowledgeBindings" :key="item.documentId">{{ item.documentId }} · {{ item.version }} · {{ item.status === 'ready' ? '版本已固定' : '索引未取得' }}</p></details>
      <p v-for="item in task.caseSnapshot.scopeItems.filter(s => s.status !== 'executable')" :key="item.scopeItemId" class="preflight-warning">{{ item.reason }}</p>
    </template>
    <div v-else-if="pending" class="muted">正在核对审查输入…</div>
    <div v-else-if="error" class="error-banner" role="alert">{{ error }} <button type="button" class="secondary" @click="load">重新加载</button></div>
    <template v-else-if="preflight">
      <div class="preflight-heading"><strong>启动前检查</strong><span class="status-pill">{{ preflight.status === 'ready' ? '可启动' : preflight.status === 'partial' ? '部分资料不足，可继续' : '无法启动' }}</span><button type="button" class="primary" :disabled="busy || preflight.status === 'blocked'" @click="emit('start', props.caseId, preflight.expectedInputVersion)">{{ busy ? '正在启动…' : '确认并启动审查' }}</button></div>
      <p>目标赔案 {{ preflight.reviewObjects.targetClaimIds.length }} 笔 · 材料 {{ preflight.materialSummary.available }} 份 · 未取得 {{ preflight.materialSummary.notObtained }} 份 · 条款 {{ preflight.knowledgeBindings.length }} 个版本</p>
      <p v-for="item in preflight.scopeItems.filter(s => s.status !== 'executable')" :key="item.scopeItemId" class="preflight-warning">{{ item.reason }}</p>
      <details><summary>查看完整检查信息</summary>
      <p>审查对象：目标赔案 {{ preflight.reviewObjects.targetClaimIds.join('、') }}<span v-if="preflight.reviewObjects.relatedClaimIds.length"> · 关联赔案 {{ preflight.reviewObjects.relatedClaimIds.join('、') }}</span> · 车辆 {{ preflight.reviewObjects.vehicleIds.length }} 台 · 损失项目 {{ preflight.reviewObjects.lossIds.length }} 项</p>
      <p>人伤提示：{{ preflight.injuryStatus }}<span v-if="preflight.injuredPersonIds.length"> · 已知伤者 {{ preflight.injuredPersonIds.join('、') }}</span> · 已取得材料 {{ preflight.materialSummary.available }} 份 · 未取得 {{ preflight.materialSummary.notObtained }} 份</p>
      <div class="grid">
        <div><h3>审查范围</h3><p v-for="item in preflight.scopeItems" :key="item.scopeItemId"><strong>{{ item.title }}</strong> · {{ item.status === 'executable' ? '可执行' : item.status === 'limited' ? '受限' : '阻塞' }}<small v-if="item.reason"> · {{ item.reason }}</small></p></div>
        <div><h3>适用保单与条款</h3><p v-for="item in preflight.applicablePolicies" :key="item.policyId"><strong>{{ item.policyId }}</strong> · {{ item.policyType }} · {{ item.coverageCodes.join('、') || '未识别承保险种' }}</p><p v-for="item in preflight.knowledgeBindings" :key="`${item.documentId}:${item.version}`"><strong>{{ item.documentId }}</strong> · {{ item.version }} · {{ item.status === 'ready' ? '版本已固定' : '索引未取得，条款核验受限' }}</p></div>
      </div>
      <div v-if="preflight.blockingReasons.length" class="error-banner">{{ preflight.blockingReasons.join('；') }}</div>
      </details>
    </template>
  </section>
</template>
