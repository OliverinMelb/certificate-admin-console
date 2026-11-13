<script setup lang="ts">
defineProps<{ localDate: string; localDatetime: string; timezone: string }>()
</script>

<template>
  <span class="certificate-time">
    <time :datetime="localDatetime" :title="localDatetime">{{ localDate }}</time>
    <span class="local-clock">{{ localDatetime.replace('T', ' ') }}</span>
    <span class="time-zone">{{ timezone }}</span>
  </span>
</template>

<style scoped>
.certificate-time { display: inline-flex; flex-direction: column; gap: 3px; font-variant-numeric: tabular-nums; }
.local-clock, .time-zone { color: #526575; font-size: 12px; }
</style>
