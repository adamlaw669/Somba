import DocsPage from '../../components/DocsPage'

const entries = [
  {
    date: '2026-07-01',
    title: 'Reconciliation sweep + smoke tests',
    body: 'Added the periodic sweep job that resolves stuck payment_uncertain subscriptions and unmatched ledger intents. Added a golden-path smoke test covering plan/customer/subscription creation through a paid invoice.',
  },
  {
    date: '2026-06-18',
    title: 'Proration on plan changes',
    body: 'PATCH /v1/subscriptions/:id now calculates and returns a proration invoice for upgrades and downgrades.',
  },
  {
    date: '2026-06-02',
    title: 'Transfer fallback recovery',
    body: 'Failed charges classified as broken_card or risk now route to transfer fallback instead of continued retries. Added transfer.requested and transfer.reconciled events.',
  },
]

export default function Changelog() {
  return (
    <DocsPage eyebrow="Resources" title="Changelog" path="/docs/changelog">
      <div className="flex flex-col gap-8">
        {entries.map((e) => (
          <div key={e.date} className="border-l-2 border-line pl-4">
            <div className="mb-1 font-mono text-[12px] text-text-faint">{e.date}</div>
            <h2 className="mb-1">{e.title}</h2>
            <p>{e.body}</p>
          </div>
        ))}
      </div>
    </DocsPage>
  )
}
