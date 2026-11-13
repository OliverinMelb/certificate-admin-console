export interface Actor {
  id: string
  email: string
  tenant_id: string
  tenant_name: string
  timezone: string
}

export interface Course { id: string; title: string }
export interface AuditEvent { id: string; actor_id: string; event_type: 'ISSUED' | 'REVOKED'; occurred_at: string }
export interface Certificate {
  id: string
  serial_number: string
  learner_id: string
  learner_name: string
  course_id: string
  course_title: string
  issued_at: string
  issued_local_date: string
  issued_local_datetime: string
  timezone: string
  status: 'ACTIVE' | 'REVOKED'
}
export interface Items<T> { items: T[] }
export interface CertificateList extends Items<Certificate> {
  total: number
  page: number
  page_size: number
}
export type CertificateSort = 'serial_number' | 'learner_name' | 'issue_date'
export type SortOrder = 'asc' | 'desc'

export async function get<T>(path: string, signal: AbortSignal, actorId?: string): Promise<T> {
  const response = await fetch(`/api/${path}`, {
    signal,
    cache: 'no-store',
    headers: actorId ? { 'X-Actor-Id': actorId } : undefined,
  })
  if (!response.ok) {
    if (response.status === 401) throw new Error('身份无效，请重新选择演示身份。')
    if (response.status === 404) throw new Error('找不到该证书，或当前身份无权查看。')
    throw new Error('暂时无法加载，请重试。')
  }
  return response.json() as Promise<T>
}

export function formatUtc(value: string): string {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : `${date.toISOString().replace('T', ' ').replace(/\.\d{3}Z$/, '')} UTC`
}
