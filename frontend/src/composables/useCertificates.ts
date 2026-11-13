import { computed, onMounted, onScopeDispose, shallowRef } from 'vue'
import type { AuditEvent } from '../api/certificates'
import { get, type Actor, type Course, type Certificate, type CertificateList, type Items, type CertificateSort, type SortOrder } from '../api/certificates'

// Each resource has an independent generation: even an uncancellable late response
// cannot update state after invalidation, retry, identity change, or unmount.
function useResource<T>(empty: () => T) {
  const data = shallowRef<T>(empty())
  const loading = shallowRef(false)
  const error = shallowRef('')
  let generation = 0
  let controller: AbortController | undefined

  function clear() {
    generation++
    controller?.abort()
    controller = undefined
    data.value = empty()
    loading.value = false
    error.value = ''
  }

  async function load(path: string, actorId?: string) {
    clear()
    const current = generation
    const request = new AbortController()
    controller = request
    loading.value = true
    const timeout = window.setTimeout(() => request.abort(), 15000)
    try {
      const result = await get<T>(path, request.signal, actorId)
      if (current === generation) data.value = result
    } catch (cause) {
      if (current === generation) {
        error.value = request.signal.aborted ? '请求超时，请重试。' : cause instanceof Error ? cause.message : '暂时无法加载，请重试。'
      }
    } finally {
      window.clearTimeout(timeout)
      if (current === generation) loading.value = false
    }
  }

  onScopeDispose(clear)
  return { data, loading, error, clear, load }
}

export function useCertificates() {
  const actors = useResource<Items<Actor>>(() => ({ items: [] }))
  const courses = useResource<Items<Course>>(() => ({ items: [] }))
  const certificates = useResource<CertificateList>(() => ({ items: [], total: 0, page: 1, page_size: 50 }))
  const detail = useResource<Certificate | null>(() => null)
  const audit = useResource<Items<AuditEvent>>(() => ({ items: [] }))
  const actorId = shallowRef('')
  const query = shallowRef('')
  const sort = shallowRef<CertificateSort>('serial_number')
  const order = shallowRef<SortOrder>('asc')
  const page = shallowRef(1)
  const pageSize = shallowRef(50)
  const detailId = shallowRef('')
  const searching = shallowRef(false)
  let debounce: ReturnType<typeof setTimeout> | undefined
  const actor = computed(() => actors.data.value.items.find(item => item.id === actorId.value))
  const busy = computed(() => searching.value || certificates.loading.value)

  function cancelDebounce() {
    clearTimeout(debounce)
    searching.value = false
  }
  function closeDetail() {
    detailId.value = ''
    detail.clear()
    audit.clear()
  }
  function loadList() {
    cancelDebounce()
    if (!actorId.value) return
    const params = new URLSearchParams({ q: query.value.trim(), sort: sort.value, order: order.value, page: String(page.value), page_size: String(pageSize.value) })
    void certificates.load(`certificates?${params}`, actorId.value)
  }
  function loadCourses() {
    if (actorId.value) void courses.load('courses', actorId.value)
  }
  function selectActor(id: string) {
    cancelDebounce()
    certificates.clear()
    courses.clear()
    closeDetail()
    actorId.value = actors.data.value.items.some(item => item.id === id) ? id : ''
    page.value = 1
    query.value = ''
    loadCourses()
    loadList()
  }
  async function loadActors() {
    await actors.load('actors')
    if (!actorId.value && actors.data.value.items[0]) selectActor(actors.data.value.items[0].id)
  }
  function search(value: string) {
    query.value = value
    page.value = 1
    cancelDebounce()
    certificates.clear()
    if (!actorId.value) return
    searching.value = true
    debounce = setTimeout(loadList, 300)
  }
  function changeSort(value: CertificateSort) { sort.value = value; page.value = 1; loadList() }
  function changeOrder(value: SortOrder) { order.value = value; page.value = 1; loadList() }
  function changePageSize(value: number) { pageSize.value = value; page.value = 1; loadList() }
  function changePage(value: number) { page.value = value; loadList() }
  function openDetail(id: string) {
    if (!actorId.value) return
    detailId.value = id
    void detail.load(`certificates/${encodeURIComponent(id)}`, actorId.value)
    void audit.load(`certificates/${encodeURIComponent(id)}/audit`, actorId.value)
  }
  onMounted(loadActors)
  onScopeDispose(cancelDebounce)

  return { actors, courses, certificates, detail, audit, actorId, actor, query, sort, order, page, pageSize, detailId, busy,
    selectActor, loadActors, loadCourses, loadList, search, changeSort, changeOrder, changePageSize, changePage, openDetail, closeDetail }
}
