import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import type { V1KnowledgeGeneration } from '@casepilot/contracts';
import { ApiError } from '../api/http';
import { knowledgeApi } from '../api/knowledge';
import { createRequestScope } from '../domain/requestScope';

const terminal = (status: string) => status === 'ready' || status === 'failed';

export function useKnowledge() {
  const generations = ref<V1KnowledgeGeneration[]>([]);
  const selected = ref<V1KnowledgeGeneration>();
  const productCode = ref('AUTO-COMPREHENSIVE');
  const clauseVersion = ref('2025-01');
  const file = ref<File>();
  const confirmed = ref(false);
  const busy = ref(false);
  const polling = ref(false);
  const error = ref('');
  const scopes = createRequestScope();
  const retryKeys = new Map<string, string>();
  let timer: ReturnType<typeof setTimeout> | undefined;
  const publication = computed(() => generations.value.find(item => item.isActive
    && item.productCode === productCode.value.trim() && item.clauseVersion === clauseVersion.value.trim()));
  watch([productCode, clauseVersion, () => publication.value?.generationId], () => { confirmed.value = false; });

  function begin() {
    clearTimeout(timer);
    polling.value = false;
    busy.value = false;
    error.value = '';
    return scopes.next();
  }

  function update(item: V1KnowledgeGeneration) {
    selected.value = item;
    const index = generations.value.findIndex(row => row.generationId === item.generationId);
    if (index < 0) generations.value.unshift(item); else generations.value[index] = item;
  }

  async function read(item: V1KnowledgeGeneration, scope: ReturnType<typeof scopes.next>) {
    const current = await knowledgeApi.generation(item.generationId, scope.signal);
    if (!scope.isCurrent()) return;
    update(current);
    if (terminal(current.status)) {
      polling.value = false;
      const list = await knowledgeApi.list(scope.signal);
      if (scope.isCurrent()) generations.value = list;
    } else {
      polling.value = true;
      timer = setTimeout(() => { void poll(current, scope); }, 1500);
    }
  }

  async function poll(item: V1KnowledgeGeneration, scope: ReturnType<typeof scopes.next>) {
    try { await read(item, scope); }
    catch (cause) {
      if (scope.isCurrent()) { polling.value = false; error.value = `进度同步失败：${String(cause)}`; }
    }
  }

  async function select(item: V1KnowledgeGeneration) {
    const scope = begin();
    selected.value = item;
    await poll(item, scope);
  }

  function chooseFile(value?: File) {
    file.value = undefined;
    error.value = '';
    if (!value) return;
    if (!value.name.toLowerCase().endsWith('.pdf')) { error.value = '请选择 PDF 文件。'; return; }
    if (value.size === 0 || value.size > 10 * 1024 * 1024) { error.value = 'PDF 文件须大于 0 且不超过 10 MiB。'; return; }
    file.value = value;
  }

  async function upload() {
    if (busy.value) return;
    if (!file.value || !productCode.value.trim() || !clauseVersion.value.trim()) { error.value = '请选择 PDF，并填写险种代码和业务版本。'; return; }
    if (publication.value && !confirmed.value) { error.value = '请先确认替换该险种、业务版本的当前发布索引。'; return; }
    const body = new FormData();
    body.append('file', file.value);
    body.append('productCode', productCode.value.trim());
    body.append('clauseVersion', clauseVersion.value.trim());
    if (publication.value) body.append('expectedGenerationId', publication.value.generationId);
    const scope = begin();
    busy.value = true;
    try {
      const item = await knowledgeApi.upload(body, scope.signal);
      if (!scope.isCurrent()) return;
      update(item);
      confirmed.value = false;
      await poll(item, scope);
    } catch (cause) {
      if (!scope.isCurrent()) return;
      error.value = String(cause);
      if (cause instanceof ApiError && cause.status === 409) {
        confirmed.value = false;
        try { const list = await knowledgeApi.list(scope.signal); if (scope.isCurrent()) generations.value = list; }
        catch { /* Preserve the conflict until the user refreshes. */ }
      }
    } finally { if (scope.isCurrent()) busy.value = false; }
  }

  async function retry() {
    const item = selected.value;
    if (!item || item.status !== 'failed' || item.isActive || busy.value) return;
    const scope = begin();
    busy.value = true;
    const operation = `${item.generationId}:${item.revision}`;
    const key = retryKeys.get(operation) ?? crypto.randomUUID();
    retryKeys.set(operation, key);
    try {
      const current = await knowledgeApi.retry(item.generationId, item.revision, key, scope.signal);
      if (!scope.isCurrent()) return;
      update(current);
      await poll(current, scope);
    } catch (cause) {
      if (!scope.isCurrent()) return;
      error.value = String(cause);
      if (cause instanceof ApiError && cause.status === 409) {
        try { await read(item, scope); } catch { /* Preserve the conflict. */ }
      }
    } finally { if (scope.isCurrent()) busy.value = false; }
  }

  function pause() { begin(); }
  async function refresh() {
    const scope = begin();
    busy.value = true;
    try {
      const list = await knowledgeApi.list(scope.signal);
      if (!scope.isCurrent()) return;
      generations.value = list;
      const current = list.find(item => item.generationId === selected.value?.generationId) ?? list[0];
      if (current) { update(current); await poll(current, scope); }
      else selected.value = undefined;
    } catch (cause) { if (scope.isCurrent()) error.value = String(cause); }
    finally { if (scope.isCurrent()) busy.value = false; }
  }

  onMounted(() => { void refresh(); });
  onBeforeUnmount(() => { clearTimeout(timer); scopes.dispose(); });
  return { generations, selected, productCode, clauseVersion, file, publication, confirmed, busy, polling, error,
    chooseFile, select, upload, retry, refresh, pause };
}
