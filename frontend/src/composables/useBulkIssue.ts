import { computed, onBeforeUnmount, readonly, shallowRef, watch } from 'vue'
import { issueCourse, type IssueResult } from '../api/issuance'

export function useBulkIssue(actorId: () => string, onIssued: () => void) {
  const busy = shallowRef(false)
  const error = shallowRef('')
  const result = shallowRef<IssueResult | null>(null)
  const operation = shallowRef<{ actor: string; course: string; key: string } | null>(null)
  const canRetry = computed(() => !!operation.value && !!error.value && !busy.value)
  let generation = 0
  let controller: AbortController | undefined

  function clear() {
    generation++
    controller?.abort()
    busy.value = false
    error.value = ''
    result.value = null
    operation.value = null
  }

  async function submit(courseId: string) {
    if (busy.value || !actorId() || !courseId) return
    clear()
    operation.value = { actor: actorId(), course: courseId, key: crypto.randomUUID() }
    await run()
  }

  async function retry() {
    if (!canRetry.value || operation.value?.actor !== actorId()) return
    await run()
  }

  async function run() {
    const pending = operation.value
    if (!pending || busy.value) return
    error.value = ''
    result.value = null
    const requestGeneration = generation
    const requestActor = pending.actor
    const request = new AbortController()
    controller = request
    busy.value = true
    const timeout = setTimeout(() => request.abort(), 15000)
    try {
      const response = await issueCourse(requestActor, pending.course, pending.key, request.signal)
      if (requestGeneration !== generation || requestActor !== actorId()) return
      result.value = response
      onIssued()
    } catch (cause) {
      if (requestGeneration !== generation || requestActor !== actorId()) return
      error.value = request.signal.aborted
        ? '等待结果超时，操作可能已完成。请重试原操作获取相同结果。'
        : cause instanceof Error ? cause.message : '未取得发证结果，请检查证书列表。'
    } finally {
      clearTimeout(timeout)
      if (requestGeneration === generation) busy.value = false
    }
  }

  watch(actorId, clear, { flush: 'sync' })
  onBeforeUnmount(clear)
  return { busy: readonly(busy), error: readonly(error), result: readonly(result), canRetry, submit, retry, clear }
}
