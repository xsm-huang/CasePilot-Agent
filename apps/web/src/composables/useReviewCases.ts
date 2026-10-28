import { onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import type { ReviewCaseListItem } from '@casepilot/contracts';
import { reviewCasesApi, type ReviewCaseFilters } from '../api/reviewCases';
import { createRequestScope } from '../domain/requestScope';

const emptyFilters = (): ReviewCaseFilters => ({
  queryType: 'claim_number',
  query: '',
  closedFrom: '',
  closedTo: '',
  injuryStatus: '',
  reviewStatus: '',
});

export function useReviewCases() {
  const filters = reactive<ReviewCaseFilters>(emptyFilters());
  const cases = ref<ReviewCaseListItem[]>([]);
  const dataStatus = ref<'ready' | 'not_imported'>('ready');
  const selectedId = ref('');
  const pending = ref(false);
  const error = ref('');
  const scopes = createRequestScope();

  function select(id: string) { selectedId.value = id; }

  async function search() {
    const scope = scopes.next();
    pending.value = true;
    error.value = '';
    try {
      const response = await reviewCasesApi.list(filters, scope.signal);
      if (!scope.isCurrent()) return;
      cases.value = response.items;
      dataStatus.value = response.dataStatus;
      const nextId = response.items.some(item => item.id === selectedId.value)
        ? selectedId.value
        : response.items[0]?.id ?? '';
      selectedId.value = nextId;
    } catch (cause) {
      if (scope.isCurrent()) error.value = String(cause);
    } finally {
      if (scope.isCurrent()) pending.value = false;
    }
  }

  function reset() {
    Object.assign(filters, emptyFilters());
    void search();
  }

  onMounted(() => { void search(); });
  onBeforeUnmount(() => scopes.dispose());
  return { filters, cases, dataStatus, selectedId, pending, error, search, reset, select };
}
