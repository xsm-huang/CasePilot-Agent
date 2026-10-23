import assert from 'node:assert/strict';
import { test } from 'node:test';
import { ModelConfigurationError, readModelConfig } from '../../apps/api/src/model/config.ts';

const key = 'local-test-credential';

test('model configuration uses approved model roles and produces an immutable profile', () => {
  const config = readModelConfig({ ZHIPU_API_KEY: key });
  assert.equal(config.chatModel, 'glm-4.7-flash');
  assert.equal(config.embeddingModel, 'embedding-3');
  assert.equal(config.embeddingDimensions, 1024);
  assert.equal(Object.isFrozen(config), true);
});

test('missing credentials fail with a field name and no credential contents', () => {
  for (const invalidKey of ['', ' ', `first\n${key}`]) {
    assert.throws(() => readModelConfig({ ZHIPU_API_KEY: invalidKey }), (error: unknown) => {
      assert.ok(error instanceof ModelConfigurationError);
      assert.equal(error.field, 'ZHIPU_API_KEY');
      assert.equal(error.message.includes(key), false);
      return true;
    });
  }
});

test('model credentials cannot be sent to an alternate endpoint through configuration', () => {
  for (const url of ['https://example.com/api/paas/v4',
    'http://open.bigmodel.cn/api/paas/v4',
    'https://open.bigmodel.cn/api/paas/v4?token=private-value',
    'https://username:private-value@open.bigmodel.cn/api/paas/v4']) {
    assert.throws(() => readModelConfig({ ZHIPU_API_KEY: key, ZHIPU_BASE_URL: url }), (error: unknown) => {
      assert.ok(error instanceof ModelConfigurationError);
      assert.equal(error.field, 'ZHIPU_BASE_URL');
      assert.equal(error.message.includes('private-value'), false);
      return true;
    });
  }
});

test('invalid model names, dimensions and timeouts fail explicitly', () => {
  const invalidConfigs = [
    { CHAT_MODEL: 'other-model' }, { EMBEDDING_MODEL: 'other-embedding' },
    { EMBEDDING_DIMENSIONS: 'NaN' }, { EMBEDDING_DIMENSIONS: '1024.5' },
    { EMBEDDING_DIMENSIONS: '0' }, { EMBEDDING_DIMENSIONS: '2048' },
    { EMBEDDING_DIMENSIONS: '9007199254740992' },
    { MODEL_TIMEOUT_MS: '0' }, { MODEL_TIMEOUT_MS: '120001' },
  ];
  for (const invalid of invalidConfigs) {
    assert.throws(() => readModelConfig({ ZHIPU_API_KEY: key, ...invalid }), ModelConfigurationError);
  }
});
