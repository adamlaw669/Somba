import DocsPage from '../../components/DocsPage'
import StatusPill from '../../components/StatusPill'

const systems = [
  { name: 'API', status: 'Operational' },
  { name: 'Billing scheduler', status: 'Operational' },
  { name: 'Recovery engine', status: 'Operational' },
  { name: 'Webhook delivery', status: 'Operational' },
  { name: 'Reconciliation sweep', status: 'Operational' },
]

export default function Status() {
  return (
    <DocsPage eyebrow="Resources" title="Status" path="/docs/status">
      <div className="flex flex-col gap-3">
        {systems.map((s) => (
          <div
            key={s.name}
            className="flex items-center justify-between rounded-sm border border-line-soft bg-panel px-4 py-3"
          >
            <span className="font-mono text-[13px] text-text">{s.name}</span>
            <StatusPill kind="settled">{s.status}</StatusPill>
          </div>
        ))}
      </div>
    </DocsPage>
  )
}
