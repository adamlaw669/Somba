import MethodBadge from './MethodBadge'
import CodeBlock from './CodeBlock'

function Field({ label, rows }) {
  return (
    <div className="mb-5">
      <div className="mb-1.5 font-mono text-[11px] uppercase tracking-wider text-text-faint">
        {label}
      </div>
      <div className="flex flex-col gap-1.5">
        {rows.map((r) => (
          <div key={r.name} className="flex gap-3 font-mono text-[13px]">
            <span className="w-40 shrink-0 text-text">{r.name}</span>
            <span className="text-text-muted">
              {r.type}
              {r.required ? ', required' : r.type ? ', optional' : ''}
              {r.note ? ` — ${r.note}` : ''}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Endpoint({
  id,
  method,
  path,
  description,
  headers = [],
  body = [],
  returns,
  errors = [],
  curl,
  response,
}) {
  return (
    <section id={id} className="scroll-mt-24 border-t border-line-soft py-10 first:border-t-0 first:pt-0">
      <div className="grid grid-cols-1 gap-10 lg:grid-cols-2">
        <div>
          <div className="mb-3 flex items-center gap-2">
            <MethodBadge method={method} />
            <code className="font-mono text-[14px] text-text">{path}</code>
          </div>
          <p className="mb-6 text-[14px] leading-6 text-text-muted">{description}</p>

          {headers.length > 0 && <Field label="Headers" rows={headers} />}
          {body.length > 0 && <Field label="Body" rows={body} />}

          {returns && (
            <div className="mb-5">
              <div className="mb-1.5 font-mono text-[11px] uppercase tracking-wider text-text-faint">
                Returns
              </div>
              <p className="text-[13px] text-text-muted">{returns}</p>
            </div>
          )}

          {errors.length > 0 && (
            <div>
              <div className="mb-1.5 font-mono text-[11px] uppercase tracking-wider text-text-faint">
                Errors
              </div>
              <ul className="flex flex-col gap-1">
                {errors.map((e) => (
                  <li key={e} className="font-mono text-[13px] text-error">
                    {e}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="flex flex-col gap-4 lg:sticky lg:top-24 lg:self-start">
          {curl && <CodeBlock title="cURL">{curl}</CodeBlock>}
          {response && <CodeBlock title="Response">{response}</CodeBlock>}
        </div>
      </div>
    </section>
  )
}
