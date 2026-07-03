import StatusPill from './StatusPill'

const rows = [
  { ref: 'evt_9f2a', event: 'charge.succeeded', amount: '₦4,500.00', kind: 'settled', label: 'settled' },
  { ref: 'evt_9f2b', event: 'charge.failed', amount: '₦12,000.00', kind: 'error', label: 'empty_account' },
  { ref: 'evt_9f2c', event: 'charge.recovered', amount: '₦12,000.00', kind: 'settled', label: 'timing' },
  { ref: 'evt_9f2d', event: 'payment.uncertain', amount: '₦2,300.00', kind: 'pending', label: 'verifying' },
]

export default function LedgerStrip() {
  return (
    <div className="overflow-hidden rounded-sm border border-line bg-panel">
      <div className="flex items-center justify-between border-b border-line px-4 py-2">
        <span className="font-mono text-[12px] text-text-muted">ledger — live</span>
        <span className="font-mono text-[11px] text-text-faint">every naira accounted for</span>
      </div>
      <div>
        {rows.map((row) => (
          <div
            key={row.ref}
            className="flex items-center gap-4 border-b border-line-soft px-4 py-2.5 font-mono text-[12px] last:border-b-0"
          >
            <span className="text-text-faint">{row.ref}</span>
            <span className="flex-1 text-text-muted">{row.event}</span>
            <StatusPill kind={row.kind}>{row.label}</StatusPill>
            <span className="w-24 text-right text-text">{row.amount}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
