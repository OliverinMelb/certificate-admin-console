export interface RevocationResult {
  certificate_id: string
  status: 'revoked'
  changed: boolean
}

export async function revokeCertificate(actorId: string, certificateId: string, signal: AbortSignal): Promise<RevocationResult> {
  const response = await fetch(`/api/certificates/${encodeURIComponent(certificateId)}/revoke`, {
    method: 'POST', headers: { 'X-Actor-Id': actorId }, signal,
  })
  if (!response.ok) {
    if (response.status === 401) throw new Error('身份无效，请重新选择演示身份。')
    if (response.status === 404) throw new Error('证书不存在，或当前身份无权撤销。')
    if (response.status === 503) throw new Error('服务繁忙，请稍后重试撤销。')
    throw new Error('未取得撤销结果。可重试；重复撤销不会重复记录。')
  }
  return response.json() as Promise<RevocationResult>
}
