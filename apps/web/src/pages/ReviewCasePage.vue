<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';
import type { ReviewCaseDetail } from '@casepilot/contracts';
import ReviewCaseDetailView from '../components/ReviewCaseDetail.vue';
import { reviewCasesApi } from '../api/reviewCases';
import { createRequestScope } from '../domain/requestScope';

const props = defineProps<{ caseId: string }>();
defineEmits<{ back: [] }>();
const detail = ref<ReviewCaseDetail>();
const pending = ref(false);
const error = ref('');
const scopes = createRequestScope();
async function load() {
  const scope = scopes.next(); pending.value = true; error.value = ''; detail.value = undefined;
  try { const value = await reviewCasesApi.detail(props.caseId, scope.signal); if (scope.isCurrent()) detail.value = value; }
  catch (cause) { if (scope.isCurrent()) error.value = String(cause); }
  finally { if (scope.isCurrent()) pending.value = false; }
}
onMounted(() => { void load(); });
onBeforeUnmount(() => scopes.dispose());
</script>

<template>
  <main>
    <header><div><span class="eyebrow">CASEPILOT / CASE DETAIL</span><h1>案件完整详情</h1></div><button type="button" class="secondary" @click="$emit('back')">返回案件工作台</button></header>
    <div v-if="error" class="error-banner" role="alert">{{ error }} <button type="button" class="secondary" @click="load">重新加载</button></div>
    <div v-if="pending" class="panel empty detail-page-state"><div class="orbit">···</div><h2>正在加载案件详情</h2></div>
    <ReviewCaseDetailView v-else-if="detail" :detail="detail" class="detail-page-content" />
  </main>
</template>
