import { useState } from 'react'
import DOMPurify from 'dompurify'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Check, Code2, Copy, Download, FileText, X } from 'lucide-react'
import type { Artifact } from '../types'

type Props = { artifact: Artifact | null; onClose: () => void }

const artifactDocument = (html: string) => `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><style>html,body{margin:0;padding:0;background:#fff;color:#17213b;font-family:Inter,ui-sans-serif,system-ui,sans-serif}body{padding:24px;line-height:1.6}h1,h2,h3{line-height:1.15;color:#101a35}a{color:#2356d8}</style></head><body>${DOMPurify.sanitize(html, { FORBID_TAGS: ['script','iframe','object','embed','form','svg','math'], FORBID_ATTR: ['style','onerror','onload','onclick','srcset'] })}</body></html>`

export function ArtifactViewer({ artifact, onClose }: Props) {
  const [copied, setCopied] = useState(false)

  if (!artifact) return <aside className="artifact-empty"><div className="empty-icon"><FileText size={24} /></div><h2>Artifacts, where work becomes useful</h2><p>Ask for a Ship 30 essay, a strategy memo, or an HTML concept. It will appear here, rendered beside the conversation.</p><span className="security-note">HTML opens in a sandbox with scripts, forms, embeds, and event handlers removed.</span></aside>

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(artifact.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // fallback if clipboard API unavailable
    }
  }

  const download = () => {
    const blob = new Blob([artifact.content], { type: artifact.kind === 'html' ? 'text/html' : 'text/markdown' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `${artifact.title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.${artifact.kind === 'html' ? 'html' : 'md'}`
    link.click(); URL.revokeObjectURL(link.href)
  }

  return <aside className="artifact-panel" aria-label="Artifact viewer">
    <header className="artifact-header">
      <div>
        <span className="artifact-kicker"><Code2 size={13} /> {artifact.kind} artifact</span>
        <h2>{artifact.title}</h2>
      </div>
      <div className="artifact-actions">
        <button className="icon-button" onClick={copy} aria-label={copied ? 'Copied to clipboard' : 'Copy artifact'} title={copied ? 'Copied!' : 'Copy'}>
          {copied ? <Check size={18} /> : <Copy size={18} />}
        </button>
        <button className="icon-button" onClick={download} aria-label="Download artifact" title="Download">
          <Download size={18} />
        </button>
        <button className="icon-button" onClick={onClose} aria-label="Close artifact" title="Close">
          <X size={18} />
        </button>
      </div>
    </header>
    <div className="artifact-canvas">
      {artifact.kind === 'html' ? <iframe title={artifact.title} sandbox="" srcDoc={artifactDocument(artifact.content)} /> : <article className="markdown-document"><ReactMarkdown remarkPlugins={[remarkGfm]}>{artifact.content}</ReactMarkdown></article>}
    </div>
  </aside>
}
