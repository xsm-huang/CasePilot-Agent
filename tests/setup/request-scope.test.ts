import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createRequestScope } from '../../apps/web/src/domain/requestScope.ts';

test('selecting another task aborts the old request and invalidates all captured callbacks', () => {
  const scope = createRequestScope();
  const first = scope.next();
  assert.equal(first.isCurrent(), true);
  assert.equal(first.signal.aborted, false);
  const second = scope.next();
  assert.equal(first.signal.aborted, true);
  assert.equal(first.isCurrent(), false);
  assert.equal(second.signal.aborted, false);
  assert.equal(second.isCurrent(), true);
  const third = scope.next();
  assert.equal(first.isCurrent(), false);
  assert.equal(second.isCurrent(), false);
  assert.equal(second.signal.aborted, true);
  assert.equal(third.isCurrent(), true);
});

test('disposing a page invalidates current callbacks even when underlying work ignores abort', async () => {
  const scope = createRequestScope();
  const request = scope.next();
  let finish: () => void = () => { throw new Error('deferred work not initialized'); };
  const deferred = new Promise<void>((resolve) => { finish = resolve; });
  const lateResult = deferred.then(() => request.isCurrent());
  scope.dispose();
  finish();
  assert.equal(await lateResult, false);
  assert.equal(request.signal.aborted, true);
  const next = scope.next();
  assert.equal(next.isCurrent(), true);
  assert.equal(next.signal.aborted, false);
  assert.equal(request.isCurrent(), false);
});
