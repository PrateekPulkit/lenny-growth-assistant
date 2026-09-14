import { useCallback, useEffect, useState } from 'react'
import { BookOpenText, ChevronDown, Command, FilePlus2, MessageSquarePlus, PanelRight, Send, Sparkles, X } from 'lucide-react'
import { api } from './api'
import { ArtifactViewer } from './components/ArtifactViewer'
import { MessageBubble } from './components/MessageBubble'
import type { Artifact, ChatMessage, Session } from './types'

const starterQuestions = [
  'What are the strongest ways to find early product-market fit?',
  'How should a product team think about activation?',
  'Turn the current answer into a Ship 30 essay.',
]

export default function App() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [activeSession, setActiveSession] = useState<Session | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [artifact, setArtifact] = useState<Artifact | null>(null)
  const [sessionArtifacts, setSessionArtifacts] = useState<Artifact[]>([])
  const [input, setInput] = useState('')
  const [provider, setProvider] = useState<Session['provider']>('ollama')
  const [artifactMode, setArtifactMode] = useState(false)
  const [artifactKind, setArtifactKind] = useState<Artifact['kind']>('markdown')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => { api.sessions().then(setSessions).catch(() => setError('Could not reach the API. Start the local stack, then refresh.')) }, [])
  useEffect(() => {
    if (!activeSession) return
    Promise.all([api.messages(activeSession.id), api.artifacts(activeSession.id)]).then(([nextMessages, artifacts]) => {
      setMessages(nextMessages)
      setSessionArtifacts(artifacts)
      setArtifact(artifacts[0] ?? null)
    }).catch((reason: Error) => setError(reason.message))
  }, [activeSession])

  const newChat = useCallback(async () => {
    try {
      setError(null); setLoading(true)
      const session = await api.createSession(provider)
      setSessions(items => [session, ...items]); setActiveSession(session); setMessages([]); setArtifact(null); setSidebarOpen(false)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not start a conversation.') } finally { setLoading(false) }
  }, [provider])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        newChat()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [newChat])

  async function submit(event?: React.FormEvent, suggested?: string) {
    event?.preventDefault()
    const content = (suggested ?? input).trim()
    if (!content || loading) return
    let session = activeSession
    try {
      setError(null); setLoading(true)
      if (!session) {
        session = await api.createSession(provider); setSessions(items => [session!, ...items]); setActiveSession(session)
      }
      const optimistic: ChatMessage = { id: `optimistic-${Date.now()}`, role: 'user', content, citations: [], created_at: new Date().toISOString() }
      setMessages(items => [...items, optimistic]); setInput('')
      const response = await api.send(session.id, content, artifactMode, artifactKind)
      setMessages(items => [...items.filter(item => item.id !== optimistic.id), response.message])
      if (response.artifact) {
        setArtifact(response.artifact)
        setSessionArtifacts(items => [response.artifact!, ...items])
      }
      setSessions(items => items.map(item => item.id === session!.id ? { ...item, title: item.title === 'New conversation' ? content.slice(0, 76) : item.title, updated_at: new Date().toISOString() } : item))
    } catch (reason) { setMessages(items => items.filter(item => !item.id.startsWith('optimistic-'))); setError(reason instanceof Error ? reason.message : 'Could not send your message.') } finally { setLoading(false) }
  }

  return <main className={`app-shell ${artifact ? 'artifact-open' : ''}`}>
    <button className="mobile-scrim" aria-label="Close navigation" onClick={() => setSidebarOpen(false)} />
    <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
      <div className="brand"><div className="brand-mark"><Sparkles size={19} /></div><div><strong>Lenny Growth</strong><span>Research workspace</span></div><button className="sidebar-close icon-button" onClick={() => setSidebarOpen(false)} aria-label="Close navigation"><X size={18}/></button></div>
      <button className="new-chat" onClick={newChat} disabled={loading}><MessageSquarePlus size={17} /> New conversation <kbd>⌘ K</kbd></button>
      <nav aria-label="Conversations"><p className="sidebar-label">Recent conversations</p>{sessions.length ? sessions.map(session => <button key={session.id} className={`session-link ${activeSession?.id === session.id ? 'active' : ''}`} onClick={() => { setActiveSession(session); setSidebarOpen(false) }}><BookOpenText size={16}/><span>{session.title}</span></button>) : <p className="empty-sessions">Your conversations will stay here.</p>}</nav>
      <div className="sidebar-footer"><div className="grounded-badge"><span></span> Transcript-grounded answers</div><p>Sources are attached to every answer.</p></div>
    </aside>
    <section className="chat-column">
      <header className="topbar"><button className="mobile-menu icon-button" onClick={() => setSidebarOpen(true)} aria-label="Open navigation"><Command size={18}/></button><div className="conversation-title"><span>{activeSession?.title ?? 'New conversation'}</span><small>Private workspace</small></div><div className="topbar-actions"><label className="provider-select"><span>Model</span><select value={activeSession?.provider ?? provider} onChange={e => { const next = e.target.value as Session['provider']; setProvider(next); if (activeSession) setError('Start a new conversation to use a different provider.'); }}><option value="ollama">Ollama</option><option value="anthropic">Anthropic</option></select><ChevronDown size={14}/></label><button className="artifact-toggle icon-button" onClick={() => setArtifact(value => value ? null : (sessionArtifacts[0] ?? null))} aria-label="Toggle artifact viewer"><PanelRight size={19}/></button></div></header>
      <div className="chat-scroll">
        {messages.length === 0 ? <section className="welcome"><div className="welcome-spark"><Sparkles size={28}/></div><p className="eyebrow">The Lenny Growth Assistant</p><h1>Turn conversations into<br/><em>product momentum.</em></h1><p className="welcome-copy">Research product and growth questions from Lenny’s Podcast transcripts. Every response stays grounded, sourced, and ready to share.</p><div className="starter-grid">{starterQuestions.map(question => <button key={question} onClick={() => submit(undefined, question)}><span>{question}</span><Send size={15}/></button>)}</div></section> : <section className="thread">{messages.map(message => <MessageBubble key={message.id} message={message}/>) }{loading && <div className="thinking"><span></span><span></span><span></span> Researching the transcripts</div>}</section>}
      </div>
      <footer className="composer-wrap"><div className="composer-tools"><button className={artifactMode ? 'active' : ''} onClick={() => setArtifactMode(value => !value)}><FilePlus2 size={15}/> Create artifact</button>{artifactMode && <div className="format-switch"><button className={artifactKind === 'markdown' ? 'active' : ''} onClick={() => setArtifactKind('markdown')}>Markdown</button><button className={artifactKind === 'html' ? 'active' : ''} onClick={() => setArtifactKind('html')}>HTML/CSS</button></div>}</div>{error && <div className="error-banner" role="alert">{error}<button onClick={() => setError(null)} aria-label="Dismiss error"><X size={15}/></button></div>}<form className="composer" onSubmit={submit}><textarea value={input} onChange={e => setInput(e.target.value)} placeholder="Ask about product, growth, activation, or retention..." rows={2} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit() } }} aria-label="Message"/><button type="submit" disabled={!input.trim() || loading} aria-label="Send message"><Send size={18}/></button></form><p className="composer-hint">Answers are grounded in indexed transcripts. Shift + Enter adds a line.</p></footer>
    </section>
    <ArtifactViewer artifact={artifact} onClose={() => setArtifact(null)} />
  </main>
}
