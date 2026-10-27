import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import type { WorkbenchTask, V0ClaimCase, Conversation, ConversationSummary, CitationContext } from '@casepilot/contracts';
import { workbenchApi } from '../api/workbench';
import { ApiError } from '../api/http';
import { mergeAnalysisEvent } from '../domain/analysisEvents';
import { isTerminal } from '../domain/presentation';
import { createRequestScope } from '../domain/requestScope';
import { useAnalysisStream } from './useAnalysisStream';

export function useWorkbench() {
  const cases = ref<V0ClaimCase[]>([]), history = ref<WorkbenchTask[]>([]);
  const conversations = ref<ConversationSummary[]>([]), conversation = ref<Conversation>();
  const selectedId = ref('CASE-2026-001'), task = ref<WorkbenchTask>();
  const pending = ref(false), error = ref(''), citation = ref<CitationContext>();
  const drafts = ref<Record<string, string>>({}), comments = ref<Record<string, string>>({});
  const scopes = createRequestScope(), stream = useAnalysisStream();
  // Keep the same key when retrying an uncertain response, including after navigation.
  const commandKeys = new Map<string, string>();
  let conversationRead = 0;
  let citationRead = 0;
  const keyFor = (body: unknown) => { const fingerprint = JSON.stringify(body); if (!commandKeys.has(fingerprint)) commandKeys.set(fingerprint, crypto.randomUUID()); return commandKeys.get(fingerprint)!; };
  const selected = computed(() => task.value?.schemaVersion === 1 ? task.value.caseSnapshot : cases.value.find(c => c.id === selectedId.value));
  const running = computed(() => pending.value || !!conversation.value?.activeAnalysisId);
  const question = computed({ get: () => drafts.value[conversation.value?.id ?? selectedId.value] ?? '', set: (v: string) => { drafts.value[conversation.value?.id ?? selectedId.value] = v; } });
  const comment = computed({ get: () => comments.value[task.value?.id ?? ''] ?? '', set: (v: string) => { if (task.value) comments.value[task.value.id] = v; } });

  function begin() { citationRead += 1; const scope = scopes.next(); stream.close(); pending.value = false; error.value = ''; citation.value = undefined; return scope; }
  function remember(current: WorkbenchTask) {
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
  function display(current: WorkbenchTask, scope: ReturnType<typeof begin>) {
    task.value = current; selectedId.value = current.caseId; remember(current);
    if (current.schemaVersion !== 1 || isTerminal(current.status)) { stream.close('执行已暂停或结束'); return; }
    stream.connect(current.id, current.lastEventSeq, {
      isCurrent: () => scope.isCurrent() && task.value?.id === current.id,
      onEvent(event) {
        if (task.value?.schemaVersion !== 1) return;
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
      const [list, detail] = await Promise.all([workbenchApi.conversations(current.caseId, scope.signal), current.schemaVersion === 1 ? workbenchApi.conversation(current.conversationId, scope.signal) : Promise.resolve(undefined)]);
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
  async function start(newConversation = false) {
    if (pending.value) return;
    const draft = question.value, caseId = selectedId.value;
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
      const body = { conversationId: currentConversation.id, kind: currentConversation.messages.some(m => m.role === 'assistant') ? 'followup' as const : 'initial' as const, question: draft || '请分析当前案件。' };
      const current = await workbenchApi.start(body, keyFor(body), scope.signal);
      commandKeys.delete(JSON.stringify(body));
      if (scope.isCurrent()) { drafts.value[currentConversation.id] = ''; display(current, scope); await refreshConversation(scope); }
    } catch (cause) { if (scope.isCurrent()) error.value = String(cause); }
    finally { if (scope.isCurrent()) pending.value = false; }
  }
  async function command(decision?: 'approve' | 'reject') {
    const current = task.value;
    if (pending.value || current?.schemaVersion !== 1) return;
    const scope = begin(); pending.value = true;
    try {
      if (decision && current.pendingReview) {
        const body = { decision, comment: comment.value, interruptKey: current.pendingReview.interruptKey, expectedRevision: current.revision };
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
    if (current?.schemaVersion !== 1) return;
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
  onMounted(async () => {
    const scope = begin(); pending.value = true;
    try {
      const [loadedCases, loadedHistory, list] = await Promise.all([workbenchApi.cases(scope.signal), workbenchApi.history(scope.signal), workbenchApi.conversations(selectedId.value, scope.signal)]);
      if (scope.isCurrent()) {
        cases.value = loadedCases; history.value = loadedHistory; conversations.value = list;
        let saved: string | null = null;
        try { saved = localStorage.getItem('casepilot:last-task'); } catch { /* Optional browser preference. */ }
        if (saved && loadedHistory.some(t => t.id === saved)) await openTask(saved);
      }
    } catch (cause) { if (scope.isCurrent()) error.value = String(cause); }
    finally { if (scope.isCurrent()) pending.value = false; }
  });
  onBeforeUnmount(() => { scopes.dispose(); stream.close(); });
  return { cases, history, selectedId, task, selected, pending, running, error, question, comment, conversation, conversations, citation, connection: stream.connection, selectCase, openTask, openConversation, start, review: command, recover: () => command(), showCitation, olderMessages };
}
