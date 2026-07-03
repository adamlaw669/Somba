import { useState } from 'react'

export default function CodeBlock({ title, lang, children }) {
  const [copied, setCopied] = useState(false)
  const code = typeof children === 'string' ? children.replace(/\n$/, '') : ''

  function onCopy() {
    navigator.clipboard?.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div data-codeblock className="overflow-hidden rounded-sm border border-line bg-panel">
      {title && (
        <div className="flex items-center justify-between border-b border-line px-4 py-2">
          <span data-codeblock-title className="font-mono text-[12px] text-text-muted">
            {title}
          </span>
          <button
            type="button"
            onClick={onCopy}
            className="rounded-sm border border-line px-2 py-0.5 font-mono text-[11px] text-text-faint transition-colors hover:border-settled hover:text-settled"
          >
            {copied ? 'copied' : 'copy'}
          </button>
        </div>
      )}
      <pre className="overflow-x-auto px-4 py-3 text-[13px] leading-[1.7]">
        <code className={`font-mono text-text ${lang ? `language-${lang}` : ''}`}>
          {code}
        </code>
      </pre>
    </div>
  )
}
