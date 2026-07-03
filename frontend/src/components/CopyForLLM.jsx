import { useState } from 'react'
import { articleToMarkdown } from '../lib/domToMarkdown'

export default function CopyForLLM({ title, description, contentRef }) {
  const [copied, setCopied] = useState(false)

  function buildMarkdown() {
    const body = articleToMarkdown(contentRef.current)
    return [`# ${title}`, description, body].filter(Boolean).join('\n\n')
  }

  function buildPrompt() {
    const url = typeof window !== 'undefined' ? window.location.href : ''
    return `Read ${url} so I can ask you questions about the Somba API.`
  }

  async function onCopy() {
    await navigator.clipboard?.writeText(buildMarkdown())
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  const prompt = encodeURIComponent(buildPrompt())
  const itemClass =
    'rounded-sm border border-line px-2.5 py-1 transition-colors hover:border-settled hover:text-settled'

  return (
    <div className="mb-8 flex flex-wrap items-center gap-2 font-mono text-[12px] text-text-faint">
      <button type="button" onClick={onCopy} className={itemClass}>
        {copied ? 'copied' : 'copy page'}
      </button>
      <a href={`https://chatgpt.com/?q=${prompt}`} target="_blank" rel="noreferrer" className={itemClass}>
        open in chatgpt ↗
      </a>
      <a href={`https://claude.ai/new?q=${prompt}`} target="_blank" rel="noreferrer" className={itemClass}>
        open in claude ↗
      </a>
    </div>
  )
}
