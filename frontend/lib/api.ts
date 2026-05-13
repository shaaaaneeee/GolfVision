const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export type SkillLevel = 'beginner' | 'intermediate' | 'advanced'
export type JobStatus = 'queued' | 'processing' | 'complete' | 'failed'

export interface FaultResult {
  name: string
  severity: number
}

export interface AnalysisResult {
  job_id: string
  status: JobStatus
  faults: FaultResult[] | null
  coaching: string | null
  features: Record<string, number> | null
  error: string | null
}

export async function submitVideo(
  file: File,
  skillLevel: SkillLevel
): Promise<{ job_id: string }> {
  const form = new FormData()
  form.append('video', file)
  form.append('skill_level', skillLevel)

  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    body: form,
  })

  const data = await res.json()
  if (!res.ok) {
    throw new Error(data.detail ?? 'Upload failed')
  }
  return data as { job_id: string }
}

export async function getResult(jobId: string): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/result/${jobId}`)
  const data = await res.json()
  if (!res.ok) {
    throw new Error(data.detail ?? 'Failed to fetch result')
  }
  return data as AnalysisResult
}
