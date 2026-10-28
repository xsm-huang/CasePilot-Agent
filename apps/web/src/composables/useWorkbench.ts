import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import type { AnalysisTask, Conversation, ConversationSummary, CitationContext } from '@casepilot/contracts';
import { workbenchApi } from '../api/workbench';
import { reviewCasesApi } from '../api/reviewCases';
import { ApiError } from '../api/http';
import { mergeAnalysisEvent } from '../domain/analysisEvents';
import { isTerminal } from '../domain/presentation';
import { createRequestScope } from '../domain/requestScope';
import { useAnalysisStream } from './useAnalysisStream';

export function useWorkbench() {
  const history = ref<AnalysisTask[]>([]);
  const conversations = ref<ConversationSummary[]>([]), conversation = ref<Conversation>();
  const selectedId = ref(''), task = ref<AnalysisTask>();
  const pending = ref(false), error = ref(''), citation = ref<CitationContext>();
  const drafts = ref<Record<string, string>>({}), comments = ref<Record<string, string>>({});
  const scopes = createRequestScope(), stream = useAnalysisStream();
  // Keep the same key when retrying an uncertain response, including after navigation.
  const commandKeys = new Map<string, string>();
  let conversationRead = 0;
  let citationRead = 0;
  const keyFor = (body: unknown) => { const fingerprint = JSON.stringify(body); if (!commandKeys.has(fingerprint)) commandKeys.set(fingerprint, crypto.randomUUID()); return commandKeys.get(fingerprint)!; };
  const running = computed(() => pending.value || !!conversation.value?.activeAnalysisId);
  const question = computed({ get: () => drafts.value[conversation.value?.id ?? selectedId.value] ?? '', set: (v: string) => { drafts.value[conversation.value?.id ?? selectedId.value] = v; } });
  const comment = computed({ get: () => comments.value[task.value?.id ?? ''] ?? '', set: (v: string) => { if (task.value) comments.value[task.value.id] = v; } });

  function begin() { citationRead += 1; const scope = scopes.next(); stream.close(); pending.value = false; error.value = ''; citation.value = undefined; return scope; }
  function remember(current: AnalysisTask) {
    const i = history.value.findIndex(t => t.id === current.id);
    if (i < 0) history.value.unshift(current); else history.value[i] = current;
    try { localStorage.setItem('casepilot:last-task', current.id); } catch { /* Optional browser preference. */ }
  }
  async function refreshConversation(scope: ReturnType<typeof begin>) {
    const read = ++conversationRead;
    const id = conversation.value?.id;
    if (!id) return;
    const value = await workbenchApi.conversation(id, scope.signal);
    if (scope.isCurrent() && conversation.value?.id === id && read === conversationRead) {
      conversation.value = value;
      const index = conversations.value.findIndex(c => c.id === value.id);
      if (index < 0) conversations.value.unshift(value); else conversations.value[index] = value;
    }
  }
  function display(current: AnalysisTask, scope: ReturnType<typeof begin>) {
    task.value = current; selectedId.value = current.caseId; remember(current);
    if (isTerminal(current.status)) { stream.close('执行已暂停或结束'); return; }
    stream.connect(current.id, current.lastEventSeq, {
      isCurrent: () => scope.isCurrent() && task.value?.id === current.id,
      onEvent(event) {
        if (!task.value) return;
        const result = mergeAnalysisEvent(task.value, event);
        if (result.kind === 'duplicate') return;
        if (result.kind === 'gap') { void openTask(current.id); return; }
        task.value = result.task; remember(result.task);
        if (isTerminal(result.task.status)) {
          stream.close('执行已暂停或结束');
          void refreshConversation(scope).catch(cause => { if (scope.isCurrent()) error.value = String(cause); });
        }
      },
      onInvalid: () => { if (scope.isCurrent()) void openTask(current.id); },
      onDisconnect: () => { if (scope.isCurrent()) void openTask(current.id); },
    });
  }
  async function openTask(id: string) {
    const scope = begin(); pending.value = true; task.value = undefined; conversation.value = undefined;
    try {
      const current = await workbenchApi.task(id, scope.signal);
      const [list, detail] = await Promise.all([workbenchApi.conversations(current.caseId, scope.signal), workbenchApi.conversation(current.conversationId, scope.signal)]);
      if (scope.isCurrent()) { conversations.value = list; conversation.value = detail; display(current, scope); }
    } catch (cause) { if (scope.isCurrent()) error.value = String(cause); }
    finally { if (scope.isCurrent()) pending.value = false; }
  }
  async function selectCase(id: string) {
    const scope = begin(); selectedId.value = id; task.value = undefined; conversation.value = undefined; conversations.value = []; pending.value = true;
    try { const list = await workbenchApi.conversations(id, scope.signal); if (scope.isCurrent()) conversations.value = list; }
    catch (cause) { if (scope.isCurrent()) error.value = String(cause); }
    finally { if (scope.isCurrent()) pending.value = false; }
  }
  async function openConversation(id: string) {
    const scope = begin(); pending.value = true; task.value = undefined; conversation.value = undefined;
    try {
      const value = await workbenchApi.conversation(id, scope.signal);
      const analysisId = value.activeAnalysisId ?? value.analysisIds.at(-1);
      const current = analysisId ? await workbenchApi.task(analysisId, scope.signal) : undefined;
      if (scope.isCurrent()) { conversation.value = value; selectedId.value = value.caseId; if (current) display(current, scope); }
    } catch (cause) { if (scope.isCurrent()) error.value = String(cause); }
    finally { if (scope.isCurrent()) pending.value = false; }
  }
  async function start(newConversation = false, caseIdOverride?: string, expectedInputVersion?: string, predecessorAnalysisId?: string, supplementIds: string[] = []) {
    if (pending.value) return;
    const draft = question.value, caseId = caseIdOverride ?? selectedId.value;
    if (caseIdOverride) selectedId.value = caseIdOverride;
    let currentConversation = newConversation ? undefined : conversation.value;
    const scope = begin(); pending.value = true;
    try {
      if (!currentConversation) {
        const created = await workbenchApi.createConversation(caseId, scope.signal);
        currentConversation = await workbenchApi.conversation(created.id, scope.signal);
      }
      if (!scope.isCurrent()) return;
      drafts.value[currentConversation.id] = draft;
      conversation.value = currentConversation;
      const kind = currentConversation.messages.some(m => m.role === 'assistant') ? 'followup' as const : 'initial' as const;
      const body = { conversationId: currentConversation.id, kind, question: draft || '请审查当前已结案案件。', expectedInputVersion: kind === 'initial' ? expectedInputVersion : undefined, predecessorAnalysisId, supplementIds };
      const current = await workbenchApi.start(body, keyFor(body), scope.signal);
      commandKeys.delete(JSON.stringify(body));
      if (scope.isCurrent()) { drafts.value[currentConversation.id] = ''; display(current, scope); await refreshConversation(scope); }
    } catch (cause) { if (scope.isCurrent()) error.value = String(cause); }
    finally { if (scope.isCurrent()) pending.value = false; }
  }
  async function command(decision?: 'approve' | 'reject') {
    const current = task.value;
    if (pending.value || !current) return;
    const scope = begin(); pending.value = true;
    try {
      if (decision && current.pendingReview) {
        const body = { decision, comment: comment.value, interruptKey: current.pendingReview.interruptKey, expectedRevision: current.revision, supplementIds: current.evidenceSupplements.map(item => item.supplementId) };
        await workbenchApi.review(current.id, body, keyFor({ id: current.id, ...body }), scope.signal);
      } else if (!decision) await workbenchApi.recover(current.id, current.revision, keyFor({ recover: current.id, revision: current.revision }), scope.signal);
      const updated = await workbenchApi.task(current.id, scope.signal);
      if (scope.isCurrent()) display(updated, scope);
    } catch (cause) {
      if (!scope.isCurrent()) return;
      error.value = String(cause);
      if (cause instanceof ApiError && cause.status === 409) {
        try { const updated = await workbenchApi.task(current.id, scope.signal); if (scope.isCurrent()) display(updated, scope); }
        catch { /* Preserve the original conflict. */ }
      }
    } finally { if (scope.isCurrent()) pending.value = false; }
  }
  async function showCitation(id: string) {
    const current = task.value, scope = scopes.current();
    if (!current) return;
    const read = ++citationRead;
    citation.value = undefined;
    try {
      const value = await workbenchApi.citation(current.id, id, scope.signal);
      if (scope.isCurrent() && task.value?.id === current.id && read === citationRead) citation.value = value;
    }
    catch (cause) {
      if (scope.isCurrent() && task.value?.id === current.id && read === citationRead) error.value = String(cause);
    }
  }
  async function olderMessages() {
    const current = conversation.value, scope = scopes.current();
    if (!current?.nextBefore) return;
    try {
      const older = await workbenchApi.conversation(current.id, scope.signal, current.nextBefore);
      const latest = conversation.value;
      if (scope.isCurrent() && latest?.id === current.id && latest.nextBefore === current.nextBefore) {
        const seen = new Set(latest.messages.map(m => m.id));
        conversation.value = { ...latest, messages: [...older.messages.filter(m => !seen.has(m.id)), ...latest.messages], nextBefore: older.nextBefore };
      }
    }
    catch (cause) { if (scope.isCurrent()) error.value = String(cause); }
  }
  async function addSupplement(file: File, title: string, materialType: string) {
    const current = task.value;
    if (!current || pending.value) return;
    const scope = begin(); pending.value = true;
    const body = new FormData();
    body.set('file', file); body.set('title', title); body.set('materialType', materialType); body.set('entityIds', '[]');
    try {
      await workbenchApi.supplement(current.id, body, scope.signal);
      const updated = await workbenchApi.task(current.id, scope.signal);
      if (scope.isCurrent()) display(updated, scope);
    } catch (cause) { if (scope.isCurrent()) error.value = String(cause); }
    finally { if (scope.isCurrent()) pending.value = false; }
  }
  async function reanalyze() {
    const current = task.value;
    if (!current || pending.value) return;
    const scope = scopes.current();
    try {
      const preflight = await reviewCasesApi.preflight(current.caseId, scope.signal);
      await start(true, current.caseId, preflight.expectedInputVersion, current.id, current.evidenceSupplements.map(item => item.supplementId));
    } catch (cause) { if (scope.isCurrent()) error.value = String(cause); }
  }
  onMounted(async () => {
    const scope = begin(); pending.value = true;
    try {
      const loadedHistory = await workbenchApi.history(scope.signal);
      if (scope.isCurrent()) {
        history.value = loadedHistory;
        let saved: string | null = null;
        try { saved = localStorage.getItem('casepilot:last-task'); } catch { /* Optional browser preference. */ }
        if (saved && loadedHistory.some(t => t.id === saved)) await openTask(saved);
      }
    } catch (cause) { if (scope.isCurrent()) error.value = String(cause); }
    finally { if (scope.isCurrent()) pending.value = false; }
  });
  onBeforeUnmount(() => { scopes.dispose(); stream.close(); });
  return { history, selectedId, task, pending, running, error, question, comment, conversation, conversations, citation, connection: stream.connection, selectCase, openTask, openConversation, start, startReview: (caseId: string, inputVersion: string) => start(true, caseId, inputVersion), addSupplement, reanalyze, review: command, recover: () => command(), showCitation, olderMessages };
}
