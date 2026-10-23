import 'reflect-metadata';
import { describe, expect, it } from 'vitest';
import { AnalysisStore } from './analysis.store.js';
import { ClauseRepository } from './clause.repository.js';
import { WorkflowService } from './workflow.service.js';
import { cases } from './fixtures.js';
import { evaluateClaimRules } from './rules.js';

function setup() {
  const store = new AnalysisStore();
  return { store, workflow: new WorkflowService(new ClauseRepository(), store) };
}

describe('LangGraph analysis lifecycle', () => {
  it('pauses without a report, resumes the same task, and never repeats review or tools', async () => {
    const { store, workflow } = setup();
    const task = store.create(cases[0].id);
    await workflow.start(task.id, cases[0]);
    expect(task.status).toBe('waiting_review');
    expect(task.report).toBeUndefined();
    expect(task.findings).toHaveLength(2);
    expect(task.citations.map((citation) => citation.id)).toEqual(expect.arrayContaining(['AUTO-2025-01-04', 'AUTO-2025-01-18']));
    await workflow.resume(task.id, { decision: 'approve', comment: '核验后继续分析' });
    expect(task.status).toBe('completed');
    expect(task.report?.reviewerComment).toBe('核验后继续分析');
    expect(task.events.filter((event) => event.type === 'review_required')).toHaveLength(1);
    expect(task.events.filter((event) => event.type === 'tool')).toHaveLength(3);
    await expect(workflow.resume(task.id, { decision: 'approve', comment: '' })).rejects.toThrow('只有等待审核');
    expect(task.status).toBe('completed');
  });

  it('ends rejected tasks without generating a report', async () => {
    const { store, workflow } = setup();
    const task = store.create(cases[0].id);
    await workflow.start(task.id, cases[0]);
    await workflow.resume(task.id, { decision: 'reject', comment: '先补材料' });
    expect(task.status).toBe('rejected');
    expect(task.report).toBeUndefined();
    expect(task.events.at(-1)?.status).toBe('rejected');
  });

  it('completes clean cases directly and isolates simultaneous tasks', async () => {
    const { store, workflow } = setup();
    const first = store.create(cases[0].id);
    const second = store.create(cases[1].id);
    await Promise.all([workflow.start(first.id, cases[0]), workflow.start(second.id, cases[1])]);
    expect(first.status).toBe('waiting_review');
    expect(second.status).toBe('completed');
    expect(second.report?.caseId).toBe(cases[1].id);
    expect(second.report?.citations).toHaveLength(1);
  });

  it('detects conflicting dates across materials', () => {
    const claim = structuredClone(cases[1]);
    claim.materials[0].fields.accidentDate = '2026-09-13';
    expect(evaluateClaimRules(claim).map((finding) => finding.code)).toContain('ACCIDENT_DATE_CONFLICT');
  });
});
