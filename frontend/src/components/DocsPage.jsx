import { useRef } from 'react'
import { Link } from 'react-router-dom'
import { adjacentDocs } from '../data/docsNav'
import CopyForLLM from './CopyForLLM'

export default function DocsPage({ eyebrow, title, description, path, code, children }) {
  const { prev, next } = adjacentDocs(path)
  const proseRef = useRef(null)

  return (
    <div className="flex gap-10 px-8 py-10 lg:px-10">
      <article className={`min-w-0 flex-1 ${code ? 'max-w-[640px]' : 'max-w-[760px]'}`}>
        {eyebrow && (
          <div className="mb-2 font-mono text-[12px] uppercase tracking-wider text-text-faint">
            {eyebrow}
          </div>
        )}
        <h1 className="mb-3 font-mono text-[28px] font-medium tracking-tight text-text">
          {title}
        </h1>
        {description && (
          <p className="mb-6 text-[15px] leading-7 text-text-muted">{description}</p>
        )}

        <CopyForLLM title={title} description={description} contentRef={proseRef} />

        <div
          ref={proseRef}
          className="doc-prose flex flex-col gap-6 text-[15px] leading-7 text-text-muted"
        >
          {children}
        </div>

        <div className="mt-16 flex items-center justify-between border-t border-line pt-6 font-mono text-[13px]">
          {prev ? (
            <Link to={prev.path} className="text-text-muted transition-colors hover:text-settled">
              ← {prev.title}
            </Link>
          ) : (
            <span />
          )}
          {next ? (
            <Link to={next.path} className="text-text-muted transition-colors hover:text-settled">
              {next.title} →
            </Link>
          ) : (
            <span />
          )}
        </div>
      </article>

      {code && (
        <aside className="hidden w-[380px] shrink-0 lg:block">
          <div className="sticky top-24 flex max-h-[calc(100vh-7rem)] flex-col gap-4 overflow-y-auto pb-10">
            {code}
          </div>
        </aside>
      )}
    </div>
  )
}
