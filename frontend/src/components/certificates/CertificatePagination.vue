<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ page: number; pageSize: number; total: number; disabled: boolean; unavailable: boolean }>()
const emit = defineEmits<{ page: [value: number]; pageSize: [value: number] }>()
const pages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
</script>

<template>
  <nav class="pagination" aria-label="证书分页">
    <label class="size">每页
      <select :value="pageSize" :disabled="unavailable" aria-label="每页证书数" @change="emit('pageSize', Number(($event.target as HTMLSelectElement).value))">
        <option v-for="size in [5, 10, 50, 100]" :key="size" :value="size">{{ size }}</option>
      </select> 条
    </label>
    <span class="muted" role="status">{{ disabled ? '正在更新…' : `共 ${total} 条 · 第 ${page} / ${pages} 页` }}</span>
    <div class="buttons">
      <button type="button" :disabled="disabled || unavailable || page <= 1" @click="emit('page', page - 1)">上一页</button>
      <button type="button" :disabled="disabled || unavailable || page >= pages" @click="emit('page', page + 1)">下一页</button>
    </div>
  </nav>
</template>

<style scoped>
.pagination { display: flex; flex-wrap: wrap; align-items: center; gap: 16px; margin-top: 24px; font-size: 14px; }
.size, .buttons { display: flex; align-items: center; gap: 8px; }
.buttons { margin-left: auto; }
</style>
