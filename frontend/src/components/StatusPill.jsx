const tone = {
  settled: 'text-settled bg-settled-dim/50',
  pending: 'text-pending bg-pending-dim/50',
  error: 'text-error bg-error-dim/50',
  neutral: 'text-text-muted bg-panel-2',
}

export default function StatusPill({ children, kind = 'neutral' }) {
  return (
    <span
      className={`inline-flex items-center rounded-sm px-2 py-0.5 font-mono text-[11px] ${tone[kind]}`}
    >
      {children}
    </span>
  )
}
