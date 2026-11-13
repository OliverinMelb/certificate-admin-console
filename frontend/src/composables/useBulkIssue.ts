import { onBeforeUnmount, readonly, shallowRef, watch } from 'vue'
import { issueCourse, type IssueResult } from '../api/issuance'

export function useBulkIssue(actorId: () => string, onIssued: () => void) {
  const busy = shallowRef(false)
  const error = shallowRef('')
  const result = shallowRef<IssueResult | null>(null)
  let generation = 0
  let controller: AbortController | undefined

  function clear() {
    generation++
    controller?.abort()
    busy.value = false
    error.value = ''
    result.value = null
  }

  async function submit(courseId: string) {
    if (busy.value || !actorId() || !courseId) return
    clear()
    const requestGeneration = generation
    const requestActor = actorId()
    const request = new AbortController()
    controller = request
    busy.value = true
    const timeout = setTimeout(() => request.abort(), 15000)
    try {
      const response = await issueCourse(requestActor, courseId, request.signal)
      if (requestGeneration !== generation || requestActor !== actorId()) return
      result.value = response
      onIssued()
    } catch (cause) {
      if (requestGeneration !== generation || requestActor !== actorId()) return
      error.value = request.signal.aborted
        ? '等待发证结果超时，操作可能已完成。请检查证书列表后再决定是否重试。'
        : cause instanceof Error ? cause.message : '未取得发证结果，请检查证书列表。'
    } finally {
      clearTimeout(timeout)
      if (requestGeneration === generation) busy.value = false
    }
  }

  watch(actorId, clear, { flush: 'sync' })
  onBeforeUnmount(clear)
  return { busy: readonly(busy), error: readonly(error), result: readonly(result), submit, clear }
}
