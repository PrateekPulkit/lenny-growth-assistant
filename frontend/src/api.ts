import type { Artifact, ChatMessage, Session } from './types'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, { headers: { 'Content-Type': 'application/json' }, ...init })
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    throw new Error(payload.detail ?? 'Something went wrong. Please try again.')
  }
  return response.json() as Promise<T>
}

export const api = {
  createSession: (provider: Session['provider']) => request<Session>('/sessions', { method: 'POST', body: JSON.stringify({ provider }) }),
  sessions: () => request<Session[]>('/sessions'),
  messages: (id: string) => request<ChatMessage[]>(`/sessions/${id}/messages`),
  artifacts: (id: string) => request<Artifact[]>(`/sessions/${id}/artifacts`),
  send: (id: string, content: string, createArtifact: boolean, artifactKind: Artifact['kind']) => request<{ message: ChatMessage; artifact: Artifact | null }>(`/sessions/${id}/messages`, { method: 'POST', body: JSON.stringify({ content, create_artifact: createArtifact, artifact_kind: artifactKind }) }),
}
