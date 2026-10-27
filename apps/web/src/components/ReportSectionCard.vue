<script setup lang="ts">
import type { ReportSection } from '@casepilot/contracts';

defineProps<{ section: ReportSection; title: string }>();
defineEmits<{ citation: [citationId: string] }>();
</script>

<template>
  <article>
    <h3>{{ title }}</h3>
    <p class="preserve-text">{{ section.content }}</p>
    <small v-if="section.factRefs.length">事实依据：{{ section.factRefs.join('、') }}</small>
    <div v-if="section.citationRefs.length" class="evidence-actions">
      <button
        v-for="id in section.citationRefs"
        :key="id"
        type="button"
        class="secondary"
        @click="$emit('citation', id)"
      >查看依据 {{ id }}</button>
    </div>
  </article>
</template>
