<script setup lang="ts">
import { onBeforeUnmount, shallowRef, useId, watch } from 'vue'
import { revokeCertificate } from '../../api/revocation'

const props = defineProps<{ actorId: string; certificateId: string; status: string }>()
const emit = defineEmits<{ revoked: [] }>()
const titleId = useId()
const confirming = shallowRef(false)
const busy = shallowRef(false)
const error = shallowRef('')
const completed = shallowRef(false)
let generation = 0
let controller: AbortController | undefined

function clear() {
  generation++
  controller?.abort()
  confirming.value = false
  busy.value = false
  error.value = ''
  completed.value = false
}

function cancel() {
  if (busy.value) return
  confirming.value = false
  error.value = ''
}

async function confirm() {
  if (!confirming.value || busy.value || props.status !== 'ACTIVE' || completed.value) return
  const requestGeneration = ++generation
  const request = new AbortController()
  controller = request
  busy.value = true
  error.value = ''
  const timeout = setTimeout(() => request.abort(), 15000)
  try {
    await revokeCertificate(props.actorId, props.certificateId, request.signal)
    if (generation !== requestGeneration) return
    completed.value = true
    confirming.value = false
    emit('revoked')
  } catch (cause) {
    if (generation !== requestGeneration) return
    error.value = request.signal.aborted
      ? '等待撤销结果超时，操作可能已完成。可安全重试确认。'
      : cause instanceof Error ? cause.message : '未取得撤销结果，请重试确认。'
  } finally {
    clearTimeout(timeout)
    if (generation === requestGeneration) busy.value = false
  }
}

watch(() => [props.actorId, props.certificateId, props.status], clear, { flush: 'sync' })
onBeforeUnmount(clear)
</script>

<template>
  <section class="revoke-section">
    <p v-if="status !== 'ACTIVE' || completed" role="status" class="muted">证书已撤销，不能恢复或重新发证。</p>
    <template v-else>
      <button v-if="!confirming" type="button" class="danger" @click="confirming = true">撤销证书</button>
      <div v-else class="confirmation" role="alertdialog" :aria-labelledby="titleId" :aria-busy="busy">
        <h3 :id="titleId">确认撤销这张证书？</h3>
        <p>撤销后不可恢复，也不能重新发证。</p>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <p v-if="busy" role="status">正在撤销…</p>
        <div class="actions">
          <button type="button" :disabled="busy" @click="cancel">取消撤销</button>
          <button type="button" class="danger" :disabled="busy" @click="confirm">{{ error ? '重试确认撤销' : '确认撤销' }}</button>
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.revoke-section { margin-top: 24px; padding-top: 20px; border-top: 1px solid #dbe3e9; }
.danger { color: #a3382c; border-color: #d8a49d; }
.confirmation { border: 1px solid #d8a49d; border-radius: 8px; padding: 16px; background: #fff8f6; }
.confirmation h3 { margin: 0; font-size: 16px; }
.actions { display: flex; flex-wrap: wrap; gap: 12px; justify-content: flex-end; }
</style>
