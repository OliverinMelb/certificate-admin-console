<script setup lang="ts">
import { onMounted, onUnmounted, shallowRef } from 'vue'

const state = shallowRef<'loading' | 'ready' | 'error'>('loading')
let controller: AbortController | undefined

async function checkStatus() {
  controller?.abort()
  const request = new AbortController()
  controller = request
  state.value = 'loading'
  const timeout = window.setTimeout(() => request.abort(), 5000)
  try {
    const response = await fetch('/api/health', { signal: request.signal, cache: 'no-store' })
    if (!response.ok) throw new Error('Health request failed')
    const result: unknown = await response.json()
    if (typeof result !== 'object' || result === null || !('status' in result) || result.status !== 'ok') {
      throw new Error('Unexpected health response')
    }
    if (controller === request) state.value = 'ready'
  } catch {
    if (controller === request) state.value = 'error'
  } finally {
    window.clearTimeout(timeout)
  }
}

onMounted(checkStatus)
onUnmounted(() => { controller?.abort(); controller = undefined })
</script>

<template>
  <section class="status-card" aria-labelledby="connection-title">
    <h2 id="connection-title" class="heading">服务连接</h2>
    <p class="message" role="status" aria-live="polite">
      <span class="indicator" :class="state" aria-hidden="true"></span>
      <span v-if="state === 'loading'">正在连接服务…</span>
      <span v-else-if="state === 'ready'">服务已连接</span>
      <span v-else>暂时无法连接服务，请检查服务是否启动后重试。</span>
    </p>
    <button class="retry" type="button" :disabled="state === 'loading'" @click="checkStatus">
      {{ state === 'loading' ? '连接中…' : '重新检查' }}
    </button>
  </section>
</template>

<style scoped>
.status-card { background: white; border: 1px solid #dbe3e9; border-radius: 16px; padding: 28px; }
.heading { margin: 0; font-size: 18px; }
.message { display: flex; gap: 10px; align-items: center; min-height: 32px; }
.indicator { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; background: #7c8b97; }
.indicator.ready { background: #16805b; }
.indicator.error { background: #b74838; }
.retry { background: #153e56; color: white; padding: 9px 18px; border: 0; border-radius: 8px; cursor: pointer; }
.retry:disabled { opacity: 0.65; cursor: wait; }
</style>
