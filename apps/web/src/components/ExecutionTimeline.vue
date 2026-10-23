<script setup lang="ts">
import type { V0TimelineEvent } from '@casepilot/contracts';
defineProps<{ events: V0TimelineEvent[] }>();
</script>
<template>
  <section class="panel timeline">
    <h2>执行时间线</h2>
    <article v-for="event in events" :key="event.id" class="event">
      <span class="event-icon">{{ event.type === 'tool' ? '⌘' : event.type === 'review_required' ? '!' : '✓' }}</span>
      <div><strong>{{ event.title }}</strong><p>{{ event.detail }}</p><time>{{ new Date(event.at).toLocaleTimeString('zh-CN') }}</time></div>
    </article>
  </section>
</template>
