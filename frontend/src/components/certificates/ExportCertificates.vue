<script setup lang="ts">
import { onBeforeUnmount, shallowRef, watch } from 'vue'
import { exportCertificates } from '../../api/export'

const props = defineProps<{ actorId: string; q: string; sort: string; order: string }>()
const busy = shallowRef(false)
const message = shallowRef('')
let generation = 0
let controller: AbortController | undefined

function cancel() {
  generation++
  controller?.abort()
  busy.value = false
  message.value = ''
}

async function download() {
  if (busy.value || !props.actorId) return
  cancel()
  const current = generation
  const request = new AbortController()
  controller = request
  busy.value = true
  try {
    const blob = await exportCertificates(props.actorId, props.q, props.sort, props.order, request.signal)
    if (current !== generation) return
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'certificates.csv'
    document.body.appendChild(link)
    try {
      link.click()
    } finally {
      link.remove()
      // Let the browser begin consuming the object URL before releasing it.
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    }
    message.value = 'CSV 已下载，包含所有匹配证书（含已撤销）。'
  } catch (cause) {
    if (current !== generation) return
    message.value = cause instanceof Error ? cause.message : 'CSV 导出失败，请重试。'
  } finally {
    if (current === generation) busy.value = false
  }
}

watch(() => props.actorId, cancel, { flush: 'sync' })
onBeforeUnmount(cancel)
</script>

<template>
  <div class="export-controls">
    <button type="button" :disabled="busy || !actorId" @click="download">
      {{ busy ? '正在导出…' : '导出全部匹配 CSV' }}
    </button>
    <button v-if="busy" type="button" @click="cancel">取消导出</button>
    <p v-if="message" role="status">{{ message }}</p>
  </div>
</template>
