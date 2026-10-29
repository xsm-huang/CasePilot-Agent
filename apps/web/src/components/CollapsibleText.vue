<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
const props = defineProps<{ text: string }>();
const element = ref<HTMLElement>();
const expanded = ref(false), overflowing = ref(false);
let observer: ResizeObserver | undefined;
function measure() {
  if (!element.value) return;
  overflowing.value = element.value.scrollHeight > Number.parseFloat(getComputedStyle(element.value).lineHeight) * 5 + 2;
}
watch(() => props.text, async () => { expanded.value = false; await nextTick(); measure(); });
onMounted(() => { measure(); observer = new ResizeObserver(measure); if (element.value) observer.observe(element.value); });
onBeforeUnmount(() => observer?.disconnect());
</script>
<template>
  <div class="collapsible-text">
    <div ref="element" class="preserve-text five-line-text" :class="{ clamped: !expanded }">{{ text }}</div>
    <button v-if="overflowing" type="button" class="text-button" :aria-expanded="expanded" @click="expanded = !expanded">{{ expanded ? '收起' : '展开全部' }}</button>
  </div>
</template>
