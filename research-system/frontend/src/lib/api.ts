import type { GraphData, GraphNode, GraphEdge, PaperNode, PaperDetail, ConceptMapping, PaperCard } from '../types'

const BASE = import.meta.env.VITE_API_URL

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, options)
  if (!resp.ok) {
    throw new Error(`API error ${resp.status}: ${path}`)
  }
  return resp.json() as Promise<T>
}

export async function getFullGraph(): Promise<GraphData> {
  const raw = await request<{ nodes: Array<Record<string, unknown>>; edges: GraphEdge[] }>(
    '/graph/full',
  )
  // Backend returns `type` field; frontend GraphNode expects `__type`
  const nodes = raw.nodes.map((n) => ({
    ...n,
    __type: (n.type as string) === 'paper' ? 'paper' : 'entity',
  })) as GraphNode[]
  return { nodes, edges: raw.edges }
}

export async function searchGraph(query: string): Promise<PaperNode[]> {
  const raw = await request<Array<{ paper_id: string; title: string; score: number }>>(
    `/graph/search?q=${encodeURIComponent(query)}`,
  )
  // Backend returns `paper_id`; frontend expects `id`
  return raw.map((r) => ({
    id: r.paper_id,
    title: r.title,
    year: null,
    is_read: false,
    community_id: null,
  }))
}

export async function getPaper(id: string): Promise<PaperDetail> {
  return request<PaperDetail>(`/papers/${id}`)
}

export async function getPaperCard(id: string): Promise<PaperCard> {
  return request<PaperCard>(`/papers/${id}/card`)
}

export async function getConnectionReport(paperId: string): Promise<string> {
  const data = await request<{ content: string }>(`/reports/connection/${paperId}`)
  return data.content
}

export async function markAsRead(paperId: string): Promise<void> {
  await request(`/papers/${paperId}/read`, { method: 'PATCH' })
}

export async function getAgenda(): Promise<string> {
  const data = await request<{ agenda: string }>('/agenda')
  return data.agenda
}

export async function updatePriorities(content: string): Promise<void> {
  await request('/agenda/priorities', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  })
}

export async function getPendingConcepts(): Promise<ConceptMapping[]> {
  return request<ConceptMapping[]>('/concepts/pending')
}

export async function approveConcept(id: string): Promise<void> {
  await request(`/concepts/${id}/approve`, { method: 'POST' })
}

export async function rejectConcept(id: string): Promise<void> {
  await request(`/concepts/${id}/reject`, { method: 'POST' })
}

export async function triggerGapAgent(): Promise<void> {
  await request('/reports/gaps', { method: 'POST' })
}

export async function getLatestGapReport(): Promise<string> {
  // 404 is expected when no gap report exists yet — return empty string, don't throw
  try {
    const data = await request<{ content: string }>('/reports/gaps/latest')
    return data.content
  } catch {
    return ''
  }
}

export async function ingestArxiv(arxivId: string): Promise<void> {
  await request('/ingest/arxiv', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ arxiv_id: arxivId }),
  })
}

export async function ingestUrl(url: string): Promise<void> {
  await request('/ingest/url', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })
}

export async function ingestGithub(repoUrl: string): Promise<void> {
  await request('/ingest/github', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl }),
  })
}

export async function ingestPdf(file: File): Promise<void> {
  const formData = new FormData()
  formData.append('file', file)
  const resp = await fetch(`${BASE}/ingest/pdf`, { method: 'POST', body: formData })
  if (!resp.ok) throw new Error(`API error ${resp.status}: /ingest/pdf`)
}

export async function* streamChat(
  paperId: string | null,
  query: string,
): AsyncGenerator<string> {
  const resp = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ paper_id: paperId, query }),
  })
  if (!resp.ok || !resp.body) {
    throw new Error(`Chat API error ${resp.status}`)
  }
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    yield decoder.decode(value)
  }
}
