<script setup lang="ts">
import { onMounted, useTemplateRef } from 'vue'
import type { Certificate } from '../../api/certificates'
import CertificateTime from './CertificateTime.vue'
defineProps<{ item: Certificate | null; loading: boolean; error: string }>()
const emit = defineEmits<{ close: []; retry: [] }>()
const dialog = useTemplateRef<HTMLDialogElement>('dialog')
onMounted(() => dialog.value?.showModal())
</script>

<template>
  <dialog ref="dialog" class="detail" aria-labelledby="detail-title" @cancel.prevent="emit('close')">
    <header class="detail-header"><div><p class="muted">只读记录</p><h2 id="detail-title" class="section-title">证书详情</h2></div><button type="button" autofocus @click="emit('close')">关闭</button></header>
    <p v-if="loading" role="status">正在加载详情…</p>
    <div v-else-if="error" role="alert" class="error"><p>{{ error }}</p><button type="button" @click="emit('retry')">重试详情</button></div>
    <dl v-else-if="item" class="fields">
      <dt>证书编号</dt><dd>{{ item.serial_number }}</dd>
      <dt>学员姓名</dt><dd>{{ item.learner_name }}</dd>
      <dt>学员 ID</dt><dd>{{ item.learner_id }}</dd>
      <dt>课程</dt><dd>{{ item.course_title }}</dd>
      <dt>课程 ID</dt><dd>{{ item.course_id }}</dd>
      <dt>颁发时间（租户当地）</dt><dd><CertificateTime :local-date="item.issued_local_date" :local-datetime="item.issued_local_datetime" :timezone="item.timezone" /></dd>
      <dt>状态</dt><dd>{{ item.status === 'ACTIVE' ? '有效' : '已撤销' }}</dd>
      <dt>证书 ID</dt><dd>{{ item.id }}</dd>
    </dl>
  </dialog>
</template>

<style scoped>
.detail { width: min(560px, calc(100% - 32px)); max-height: 85vh; overflow-y: auto; border: 1px solid #dbe3e9; border-radius: 16px; padding: 28px; color: #172b3a; }
.detail::backdrop { background: rgb(15 35 50 / 45%); }
.detail-header { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 24px; }
.detail-header p { margin: 0 0 4px; }
.fields { display: grid; grid-template-columns: 140px minmax(0, 1fr); gap: 14px; font-size: 14px; }
.fields dt { color: #526575; }
.fields dd { margin: 0; overflow-wrap: anywhere; }
@media (max-width: 420px) { .fields { grid-template-columns: 1fr; gap: 6px; } .fields dd { margin-bottom: 12px; } }
</style>
