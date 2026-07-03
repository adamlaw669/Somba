import { useRef } from 'react'
import { Link } from 'react-router-dom'
import { adjacentDocs } from '../data/docsNav'
import CopyForLLM from './CopyForLLM'

export default function ApiPage({ eyebrow, title, description, path, children }) {
  const { prev, next } = adjacentDocs(path)
  const proseRef = useRef(null)

  return (
    <div className="px-8 py-10 lg:px-10">
      <article className="max-w-[900px]">
        {eyebrow && (
          <div className="mb-2 font-mono text-[12px] uppercase tracking-wider text-text-faint">
            {eyebrow}
          </div>
        )}
        <h1 className="mb-3 font-mono text-[28px] font-medium tracking-tight text-text">
          {title}
        </h1>
        {description && (
          <p className="mb-4 max-w-[640px] text-[15px] leading-7 text-text-muted">
            {description}
          </p>
        )}

        <CopyForLLM title={title} description={description} contentRef={proseRef} />

        <div ref={proseRef} className="doc-prose flex flex-col">
          {children}
        </div>

        <div className="mt-6 flex items-center justify-between border-t border-line pt-6 font-mono text-[13px]">
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
    </div>
  )
}
