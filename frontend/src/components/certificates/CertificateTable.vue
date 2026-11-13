<script setup lang="ts">
import type { Certificate } from '../../api/certificates'
import CertificateTime from './CertificateTime.vue'
defineProps<{ items: readonly Certificate[]; loading: boolean; error: string; hasActor: boolean }>()
const emit = defineEmits<{ detail: [id: string]; retry: [] }>()
</script>

<template>
  <div :aria-busy="loading">
    <p v-if="loading" class="state" role="status">正在加载证书…</p>
    <div v-else-if="error" class="state error" role="alert"><p>{{ error }}</p><button type="button" @click="emit('retry')">重试证书列表</button></div>
    <p v-else-if="!hasActor" class="state muted" role="status">请选择演示身份以查看证书。</p>
    <p v-else-if="!items.length" class="state muted" role="status">暂无匹配的证书，请尝试其他姓名或编号。</p>
    <div v-else class="table-scroll" tabindex="0" role="region" aria-label="证书列表，可横向滚动">
      <table class="table">
        <thead><tr><th scope="col">证书编号</th><th scope="col">学员</th><th scope="col">课程</th><th scope="col">颁发时间（租户当地）</th><th scope="col">状态</th><th scope="col">详情</th></tr></thead>
        <tbody><tr v-for="item in items" :key="item.id">
          <td class="serial">{{ item.serial_number }}</td><td>{{ item.learner_name }}</td><td>{{ item.course_title }}</td>
          <td class="timestamp"><CertificateTime :local-date="item.issued_local_date" :local-datetime="item.issued_local_datetime" :timezone="item.timezone" /></td>
          <td><span class="badge" :class="{ revoked: item.status === 'REVOKED' }">{{ item.status === 'ACTIVE' ? '有效' : '已撤销' }}</span></td>
          <td><button type="button" class="detail-button" :aria-label="`查看证书 ${item.serial_number} 的详情`" @click="emit('detail', item.id)">查看详情</button></td>
        </tr></tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.state { text-align: center; padding: 44px 16px; background: #f7f9fb; border-radius: 8px; }
.table-scroll { overflow-x: auto; }
.table { width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }
.table th { color: #526575; background: #f4f7f9; font-weight: 600; white-space: nowrap; }
.table th, .table td { padding: 14px 12px; border-bottom: 1px solid #e6edf1; }
.serial { font-weight: 600; white-space: nowrap; }
.timestamp { white-space: nowrap; font-variant-numeric: tabular-nums; font-size: 12px; }
.badge { display: inline-block; border-radius: 20px; padding: 2px 10px; background: #e7f4ed; color: #236546; white-space: nowrap; }
.revoked { background: #f8ebe8; color: #943e32; }
.detail-button { white-space: nowrap; }
</style>
