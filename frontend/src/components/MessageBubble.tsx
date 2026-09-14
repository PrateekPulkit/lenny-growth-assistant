import { ExternalLink, Sparkles } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ChatMessage } from '../types'

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isAssistant = message.role === 'assistant'
  return <article className={`message ${isAssistant ? 'assistant-message' : 'user-message'}`}>
    {isAssistant && <div className="assistant-avatar" aria-hidden="true"><Sparkles size={15} /></div>}
    <div className="message-content">
      <div className="message-label">{isAssistant ? 'Lenny Growth Assistant' : 'You'}</div>
      <div className="message-copy"><ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown></div>
      {isAssistant && message.citations.length > 0 && <details className="sources"><summary>Grounded in {message.citations.length} transcript source{message.citations.length > 1 ? 's' : ''}</summary><div>{message.citations.map((citation, index) => <a key={`${citation.source_url}-${index}`} href={citation.source_url} target="_blank" rel="noreferrer"><strong>{citation.title}</strong><span>{citation.excerpt}</span><ExternalLink size={13} /></a>)}</div></details>}
    </div>
  </article>
}
