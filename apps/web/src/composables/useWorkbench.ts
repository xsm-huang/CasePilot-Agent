import { computed, onBeforeUnmount, onMounted, ref, toRaw } from 'vue';
import type { V0AnalysisTask, V0ClaimCase } from '@casepilot/contracts';
import { workbenchApi } from '../api/workbench';
import { ApiError } from '../api/http';
import { mergeAnalysisEvent } from '../domain/analysisEvents';
import { isTerminal } from '../domain/presentation';
import { createRequestScope } from '../domain/requestScope';
import { useAnalysisStream } from './useAnalysisStream';

const defaultComment = '请重点核验事故发生时间，并补充维修发票。';

export function useWorkbench() {
  const cases = ref<V0ClaimCase[]>([]);
  const history = ref<V0AnalysisTask[]>([]);
  const selectedId = ref('CASE-2026-001');
  const task = ref<V0AnalysisTask>();
  const taskClaim = ref<V0ClaimCase>();
  const comments = ref<Record<string, string>>({});
  const pending = ref(false);
  const error = ref('');
  const scopes = createRequestScope();
  const stream = useAnalysisStream();
  const selected = computed(() => task.value ? taskClaim.value : cases.value.find((item) => item.id === selectedId.value));
  const running = computed(() => pending.value || task.value?.status === 'running');
  const comment = computed({
    get: () => task.value ? comments.value[task.value.id] ?? defaultComment : defaultComment,
    set: (value: string) => { if (task.value) comments.value[task.value.id] = value; }
  });

  function remember(current: V0AnalysisTask) {
    const index = history.value.findIndex((item) => item.id === current.id);
    if (index < 0) history.value.unshift(current); else history.value[index] = current;
    try { localStorage.setItem(`casepilot:${current.caseId}`, current.id); } catch { /* Browser preferences are optional. */ }
  }

  function beginSelection() {
    const scope = scopes.next();
    stream.close();
    pending.value = false;
    error.value = '';
    return scope;
  }

  function display(current: V0AnalysisTask, scope: ReturnType<typeof scopes.next>) {
    selectedId.value = current.caseId;
    task.value = current;
    // V0 has no server caseSnapshot. Bind a copy to this task, never another selected case.
    taskClaim.value = structuredClone(toRaw(cases.value.find((item) => item.id === current.caseId)));
    remember(current);
    if (isTerminal(current.status)) { stream.close('执行结束'); return; }
    stream.connect(current.id, {
      isCurrent: () => scope.isCurrent() && task.value?.id === current.id,
      onEvent(event) {
        if (!task.value) return;
        const result = mergeAnalysisEvent(task.value, event);
        if (result.kind === 'duplicate') return;
        if (result.kind === 'gap') { stream.close('同步任务状态'); void openTask(current.id); return; }
        task.value = result.task;
        remember(result.task);
        if (event.type === 'error') error.value = event.detail ?? '工作流执行失败';
        if (isTerminal(result.task.status)) stream.close('执行结束');
      },
      onInvalid: () => { if (scope.isCurrent()) error.value = '收到无法读取的任务事件，请重新打开任务以同步状态。'; }
    });
  }

  async function openTask(id: string) {
    const scope = beginSelection();
    task.value = undefined;
    taskClaim.value = undefined;
    pending.value = true;
    try {
      const current = await workbenchApi.task(id, scope.signal);
      if (scope.isCurrent()) display(current, scope);
    } catch (cause) { if (scope.isCurrent()) error.value = String(cause); }
    finally { if (scope.isCurrent()) pending.value = false; }
  }

  function selectCase(id: string) {
    beginSelection();
    selectedId.value = id;
    task.value = undefined;
    taskClaim.value = undefined;
    const existing = history.value.find((item) => item.caseId === id);
    if (existing) void openTask(existing.id);
  }

  async function start() {
    if (pending.value) return;
    const scope = beginSelection();
    pending.value = true;
    try {
      const current = await workbenchApi.start(selectedId.value, scope.signal);
      if (scope.isCurrent()) display(current, scope);
    } catch (cause) { if (scope.isCurrent()) error.value = String(cause); }
    finally { if (scope.isCurrent()) pending.value = false; }
  }

  async function review(decision: 'approve' | 'reject') {
    if (!task.value || pending.value) return;
    const id = task.value.id;
    const draft = comment.value;
    const scope = beginSelection();
    pending.value = true;
    try {
      await workbenchApi.review(id, decision, draft, scope.signal);
      const current = await workbenchApi.task(id, scope.signal);
      if (scope.isCurrent()) display(current, scope);
    } catch (cause) {
      if (!scope.isCurrent()) return;
      error.value = String(cause);
      if (cause instanceof ApiError && cause.status === 409) {
        try {
          const current = await workbenchApi.task(id, scope.signal);
          if (scope.isCurrent()) display(current, scope);
        } catch { /* Keep the original conflict visible if the resync fails. */ }
      }
    }
    finally { if (scope.isCurrent()) pending.value = false; }
  }

  onMounted(async () => {
    const scope = beginSelection();
    pending.value = true;
    try {
      const [loadedCases, loadedHistory] = await Promise.all([workbenchApi.cases(scope.signal), workbenchApi.history(scope.signal)]);
      if (!scope.isCurrent()) return;
      cases.value = loadedCases;
      history.value = loadedHistory;
      let saved: string | null = null;
      try { saved = localStorage.getItem(`casepilot:${selectedId.value}`); } catch { /* Browser preferences are optional. */ }
      const previous = loadedHistory.find((item) => item.id === saved) ?? loadedHistory[0];
      if (previous) await openTask(previous.id);
    } catch (cause) { if (scope.isCurrent()) error.value = `无法连接服务，请确认 API 已启动。${String(cause)}`; }
    finally { if (scope.isCurrent()) pending.value = false; }
  });
  onBeforeUnmount(() => { scopes.dispose(); stream.close(); });

  return { cases, history, selectedId, task, selected, pending, running, error, comment,
    connection: stream.connection, selectCase, openTask, start, review };
}
