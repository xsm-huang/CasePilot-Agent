<script setup lang="ts">
import type { V0TimelineEvent } from '@casepilot/contracts';
defineProps<{ events: V0TimelineEvent[] }>();

const eventPresentation: Record<V0TimelineEvent['type'], { icon: string; label: string }> = {
  status: { icon: '•', label: '任务状态' },
  node: { icon: '✓', label: '节点完成' },
  tool: { icon: '⌘', label: '工具调用' },
  review_required: { icon: '!', label: '等待人工审核' },
  report: { icon: '≡', label: '报告生成' },
  error: { icon: '×', label: '执行错误' }
};
</script>
<template>
  <section class="panel timeline">
    <h2>执行时间线</h2>
    <article v-for="event in events" :key="event.id" class="event">
      <span class="event-icon" :class="event.type" :title="eventPresentation[event.type].label" :aria-label="eventPresentation[event.type].label">{{ eventPresentation[event.type].icon }}</span>
      <div><strong>{{ event.title }}</strong><p>{{ event.detail }}</p><time>{{ new Date(event.at).toLocaleTimeString('zh-CN') }}</time></div>
    </article>
  </section>
</template>
