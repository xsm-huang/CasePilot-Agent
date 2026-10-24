import assert from 'node:assert/strict';
import { test } from 'node:test';
import { v0AnalysisTaskSchema, v0TimelineEventSchema, v0ReviewAcceptedSchema } from '../dist/index.js';

const event = {
  id: 1, type: 'node', at: '2026-10-23T01:00:00.000Z',
  title: '读取案件', status: 'running',
};

test('Python event contract rejects invalid sequence, status and datetime', () => {
  assert.deepEqual(v0TimelineEventSchema.parse(event), event);
  for (const patch of [{ id: 0 }, { id: 1.5 }, { id: Number.MAX_SAFE_INTEGER + 1 }, { status: 'finished' }, { at: 'yesterday' }]) {
    assert.throws(() => v0TimelineEventSchema.parse({ ...event, ...patch }));
  }
});

test('Python task contract validates nested findings rather than trusting TypeScript', () => {
  const task = { id: 'a', caseId: 'c', status: 'running', events: [event], findings: [], citations: [] };
  assert.deepEqual(v0AnalysisTaskSchema.array().parse([task]), [task]);
  assert.throws(() => v0AnalysisTaskSchema.parse({ ...task, events: [{ ...event, id: '1' }] }));
  assert.throws(() => v0AnalysisTaskSchema.parse({ ...task, findings: [{ source: 'rule' }] }));
});

test('review acceptance must identify the accepted task and literal true', () => {
  assert.deepEqual(v0ReviewAcceptedSchema.parse({ accepted: true, taskId: 'a' }), { accepted: true, taskId: 'a' });
  assert.throws(() => v0ReviewAcceptedSchema.parse({ accepted: false, taskId: 'a' }));
  assert.throws(() => v0ReviewAcceptedSchema.parse({ accepted: true }));
});
