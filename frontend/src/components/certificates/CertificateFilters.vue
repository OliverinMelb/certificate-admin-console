<script setup lang="ts">
import type { CertificateSort, SortOrder } from '../../api/certificates'
defineProps<{ query: string; sort: CertificateSort; order: SortOrder; disabled: boolean }>()
const emit = defineEmits<{ search: [value: string]; sort: [value: CertificateSort]; order: [value: SortOrder] }>()
</script>

<template>
  <div class="filters">
    <label class="field search">搜索证书
      <input type="search" :value="query" :disabled="disabled" placeholder="输入学员姓名或证书编号" @input="emit('search', ($event.target as HTMLInputElement).value)" />
    </label>
    <label class="field">排序字段
      <select :value="sort" :disabled="disabled" @change="emit('sort', ($event.target as HTMLSelectElement).value as CertificateSort)">
        <option value="serial_number">证书编号</option><option value="learner_name">学员姓名</option>
      </select>
    </label>
    <label class="field">排序方向
      <select :value="order" :disabled="disabled" @change="emit('order', ($event.target as HTMLSelectElement).value as SortOrder)">
        <option value="asc">升序</option><option value="desc">降序</option>
      </select>
    </label>
  </div>
</template>

<style scoped>
.filters { display: flex; flex-wrap: wrap; gap: 16px; margin: 24px 0; }
.search { flex: 1 1 260px; }
</style>
