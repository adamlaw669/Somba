const styles = {
  GET: 'text-settled border-settled/40 bg-settled-dim/40',
  POST: 'text-pending border-pending/40 bg-pending-dim/40',
  PATCH: 'text-pending border-pending/40 bg-pending-dim/40',
  DELETE: 'text-error border-error/40 bg-error-dim/40',
}

export default function MethodBadge({ method }) {
  return (
    <span
      className={`inline-block rounded-sm border px-1.5 py-0.5 font-mono text-[11px] font-medium ${styles[method] ?? ''}`}
    >
      {method}
    </span>
  )
}
