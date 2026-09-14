export type Citation = { title: string; source_url: string; excerpt: string }
export type ChatMessage = { id: string; role: 'user' | 'assistant'; content: string; citations: Citation[]; created_at: string }
export type Session = { id: string; title: string; provider: 'ollama' | 'anthropic'; created_at: string; updated_at: string }
export type Artifact = { id: string; title: string; kind: 'markdown' | 'html'; content: string; created_at: string }
