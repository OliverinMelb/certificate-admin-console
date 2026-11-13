export interface IssueOutcome {
  learner_id: string
  outcome: 'issued' | 'skipped' | 'failed'
  reason: string
  certificate_id: string | null
}

export interface IssueResult { course_id: string; outcomes: IssueOutcome[] }

export async function issueCourse(actorId: string, courseId: string, key: string, signal: AbortSignal): Promise<IssueResult> {
  const response = await fetch(`/api/courses/${encodeURIComponent(courseId)}/issue`, {
    method: 'POST',
    headers: { 'X-Actor-Id': actorId, 'Idempotency-Key': key },
    signal,
  })
  if (!response.ok) {
    if (response.status === 401) throw new Error('身份无效，请重新选择演示身份。')
    if (response.status === 404) throw new Error('课程不存在，或当前身份无权发证。')
    if (response.status === 409) throw new Error('此操作标识已用于不同请求，请重新发起操作。')
    if (response.status === 503) throw new Error('服务暂时不可用，请稍后重试原操作。')
    throw new Error('未取得发证结果，可重试原操作获取结果。')
  }
  return response.json() as Promise<IssueResult>
}

export function issueReason(reason: string): string {
  const labels: Record<string, string> = {
    issued: '发证成功', already_certified: '已有证书（含已撤销），不重复发证',
    not_completed: '尚未完成课程', serial_conflict: '证书编号冲突，此学员未发证',
  }
  return labels[reason] ?? reason
}
