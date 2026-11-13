export async function exportCertificates(
  actorId: string, q: string, sort: string, order: string, signal: AbortSignal,
): Promise<Blob> {
  const query = new URLSearchParams({ q, sort, order })
  const response = await fetch(`/api/certificates/export.csv?${query}`, {
    headers: { 'X-Actor-Id': actorId }, signal,
  })
  if (!response.ok) {
    if (response.status === 401) throw new Error('身份无效，请重新选择演示身份。')
    throw new Error('CSV 导出失败，请重试。')
  }
  // Reject a truncated network transfer: blob() only resolves after complete receipt.
  return response.blob()
}
