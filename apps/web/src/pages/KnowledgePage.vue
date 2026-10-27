<script setup lang="ts">
import { useKnowledge } from '../composables/useKnowledge';
import type { V1KnowledgeGeneration } from '@casepilot/contracts';

const stateText: Record<V1KnowledgeGeneration['status'], string> = {
  queued: '等待处理', parsing: '解析 PDF', chunking: '条款分块', embedding: '生成向量', ready: '索引就绪', failed: '导入失败',
};
const { generations, selected, productCode, clauseVersion, file, publication, confirmed, busy, polling, error,
  chooseFile, select, upload, retry, refresh, pause } = useKnowledge();

function fileChanged(event: Event) { chooseFile((event.target as HTMLInputElement).files?.[0]); }
const time = (value: string) => new Date(value).toLocaleString('zh-CN');
</script>

<template>
  <main>
    <header><div><span class="eyebrow">CASEPILOT / KNOWLEDGE</span><h1>条款知识库</h1></div><button class="secondary" :disabled="busy" @click="refresh">刷新状态</button></header>
    <p class="prototype-note">上传条款 PDF，按险种和业务版本发布检索索引。新会话使用与案件匹配的当前发布索引；已有会话继续使用创建时固定的知识版本。</p>
    <div v-if="error" class="error-banner" role="alert">{{ error }}</div>
    <div class="knowledge-layout">
      <section class="panel import-panel">
        <h2>导入条款 PDF</h2>
        <p class="muted">支持包含可提取文字的 PDF，最大 10 MiB、100 页。扫描件暂不支持 OCR；空白、加密或损坏的文件会明确报错。</p>
        <form @submit.prevent="upload">
          <label for="knowledge-file">条款文件</label>
          <input id="knowledge-file" type="file" accept="application/pdf,.pdf" :disabled="busy" @change="fileChanged">
          <small v-if="file">{{ file.name }} · {{ (file.size / 1024).toFixed(1) }} KiB</small>
          <label for="knowledge-product">险种代码</label>
          <input id="knowledge-product" v-model="productCode" maxlength="100" required :disabled="busy" placeholder="例如 AUTO-COMPREHENSIVE">
          <label for="knowledge-version">业务条款版本</label>
          <input id="knowledge-version" v-model="clauseVersion" maxlength="100" required :disabled="busy" placeholder="例如 2025-01">
          <div v-if="publication" class="replacement-note">
            <strong>该险种与版本已有发布索引</strong>
            <p>{{ publication.fileName }}<br><code>{{ publication.generationId }}</code></p>
            <label class="checkbox-label"><input v-model="confirmed" type="checkbox" :disabled="busy">确认以新索引替换当前发布版本。处理成功前，当前索引继续生效；旧索引仍保留供历史引用使用。</label>
          </div>
          <button class="primary" :disabled="busy || !file || (!!publication && !confirmed)">{{ busy ? '正在提交…' : '上传并创建索引' }}</button>
        </form>
      </section>

      <section class="knowledge-results">
        <div class="panel generation-detail" aria-live="polite">
          <template v-if="selected">
            <div class="status-row"><h2>{{ selected.fileName }}</h2><span class="status" :class="selected.status === 'failed' ? 'failed' : selected.status === 'ready' ? 'completed' : ''">{{ stateText[selected.status] }}</span></div>
            <p><strong>{{ selected.productCode }} / {{ selected.clauseVersion }}</strong> · 第 {{ selected.attempt }} 次处理</p>
            <p class="publication-state">{{ selected.isActive ? '当前发布索引' : selected.status === 'ready' ? '已就绪，当前未发布' : '尚未发布，现有发布索引不受影响' }}</p>
            <dl class="knowledge-stats"><div><dt>PDF 页数</dt><dd>{{ selected.pageCount }}</dd></div><div><dt>条款分块</dt><dd>{{ selected.chunkCount }}</dd></div><div><dt>已生成向量</dt><dd>{{ selected.embeddedCount }}</dd></div></dl>
            <progress v-if="selected.status === 'embedding' && selected.chunkCount > 0" :value="selected.embeddedCount" :max="selected.chunkCount" aria-label="向量生成进度" />
            <p class="muted"><code>{{ selected.generationId }}</code><br>更新时间 {{ time(selected.updatedAt) }}</p>
            <div v-if="selected.error" class="error-banner"><strong>{{ selected.error.code }}</strong><p>{{ selected.error.message }}</p></div>
            <div class="actions">
              <button v-if="selected.status === 'failed' && !selected.isActive" class="primary" :disabled="busy" @click="retry">重试导入</button>
              <button v-if="polling" class="secondary" :disabled="busy" @click="pause">暂停进度同步</button>
              <button v-else class="secondary" :disabled="busy" @click="select(selected)">重新同步</button>
            </div>
            <p class="muted">{{ polling ? '正在自动更新进度。' : '进度同步已停止。' }}离开页面或暂停同步不会取消服务器上的导入。</p>
            <details v-if="selected.attempts.length"><summary>处理记录（{{ selected.attempts.length }}）</summary><article v-for="attempt in selected.attempts" :key="attempt.attempt" class="attempt-row"><strong>第 {{ attempt.attempt }} 次 · {{ stateText[attempt.status] }}</strong><p>{{ time(attempt.startedAt) }}<template v-if="attempt.finishedAt"> → {{ time(attempt.finishedAt) }}</template></p><p v-if="attempt.error">{{ attempt.error.code }} · {{ attempt.error.message }}</p></article></details>
          </template>
          <template v-else><h2>{{ busy ? '正在读取知识库…' : '尚无条款索引' }}</h2><p>选择 PDF 并提交，查看解析、分块和向量生成进度。</p></template>
        </div>

        <section class="panel generation-list">
          <h2>索引版本 <span class="count">{{ generations.length }}</span></h2>
          <p class="muted">“索引就绪”表示处理成功；只有标记“当前发布”的版本用于新检索。已被替换的版本仍保留。</p>
          <button v-for="item in generations" :key="item.generationId" class="generation-card" :class="{ active: selected?.generationId === item.generationId }" :disabled="busy" @click="select(item)">
            <span><strong>{{ item.fileName }}</strong><small>{{ item.productCode }} / {{ item.clauseVersion }} · {{ time(item.createdAt) }}</small></span>
            <span>{{ stateText[item.status] }}<small>{{ item.isActive ? '当前发布' : item.status === 'ready' ? '历史版本' : '未发布' }}</small></span>
          </button>
        </section>
      </section>
    </div>
  </main>
</template>
