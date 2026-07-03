import DocsPage from '../../components/DocsPage'
import CodeBlock from '../../components/CodeBlock'

function StateBox({ children, kind = 'neutral' }) {
  const tone = {
    settled: 'border-settled/50 text-settled',
    pending: 'border-pending/50 text-pending',
    error: 'border-error/50 text-error',
    neutral: 'border-line text-text-muted',
  }
  return (
    <span className={`inline-block rounded-sm border px-2.5 py-1 font-mono text-[12px] ${tone[kind]}`}>
      {children}
    </span>
  )
}

function FlowRow({ from, fromKind, label, to, toKind }) {
  return (
    <div className="flex flex-wrap items-center gap-2 py-1.5">
      <StateBox kind={fromKind}>{from}</StateBox>
      <span className="text-[12px] text-text-faint">— {label} →</span>
      <StateBox kind={toKind}>{to}</StateBox>
    </div>
  )
}

const transitions = [
  ['trialing', 'first successful charge', 'active', 'The trial converted into a paying subscription.'],
  ['trialing', 'trial ends with no payment', 'expired', 'The trial finished and nothing renewed.'],
  ['active', 'charge fails with recoverable reason', 'past_due', 'Somba gets a chance to recover the payment.'],
  ['active', 'charge times out', 'payment_uncertain', 'The system cannot guess, so it freezes.'],
  ['active', 'pause request', 'paused', 'The merchant or customer asked for a temporary stop.'],
  ['active', 'cancel request', 'cancelled', 'The subscription was deliberately ended.'],
  ['past_due', 'retry succeeds', 'active', 'The subscription has been healed.'],
  ['past_due', 'transfer arrives and matches open invoice', 'active', 'The customer recovered by pushing money in.'],
  ['payment_uncertain', 'verify confirms success', 'active', 'The missing result was actually successful.'],
  ['payment_uncertain', 'verify confirms failure', 'past_due', 'The system now knows it needs recovery.'],
  ['paused', 'resume request', 'active', 'Billing starts again.'],
  ['cancelled', 'recreate new plan', 'trialing or active', 'A new subscription must be created deliberately.'],
  ['expired', 'recreate new plan', 'trialing or active', 'A new subscription starts fresh.'],
]

const gymSweep = `# periodic sweep, simplified
for sub in subscriptions.where(status="payment_uncertain"):
    result = nomba.verify(sub.last_order_reference)
    if result.succeeded:
        sub.heal_to("active")
    elif result.failed:
        sub.transition_to("past_due")`

export default function Lifecycle() {
  return (
    <DocsPage
      eyebrow="Core concepts"
      title="The subscription lifecycle"
      path="/docs/lifecycle"
      description="Seven states, a fixed set of legal transitions, and two paths designed specifically to heal a subscription backward."
      code={<CodeBlock title="How payment_uncertain resolves">{gymSweep}</CodeBlock>}
    >
      <h2>The map</h2>
      <div className="rounded-sm border border-line bg-panel p-5">
        <div className="mb-1 font-mono text-[11px] uppercase tracking-wider text-text-faint">Happy path</div>
        <FlowRow from="trialing" fromKind="pending" label="charge succeeds" to="active" toKind="settled" />
        <FlowRow from="trialing" fromKind="pending" label="trial ends, no payment" to="expired" toKind="neutral" />

        <div className="mb-1 mt-4 font-mono text-[11px] uppercase tracking-wider text-text-faint">Recovery</div>
        <FlowRow from="active" fromKind="settled" label="charge fails" to="past_due" toKind="error" />
        <FlowRow from="past_due" fromKind="error" label="retry succeeds / transfer matches" to="active" toKind="settled" />
        <FlowRow from="active" fromKind="settled" label="charge times out" to="payment_uncertain" toKind="pending" />
        <FlowRow from="payment_uncertain" fromKind="pending" label="verify confirms success" to="active" toKind="settled" />
        <FlowRow from="payment_uncertain" fromKind="pending" label="verify confirms failure" to="past_due" toKind="error" />

        <div className="mb-1 mt-4 font-mono text-[11px] uppercase tracking-wider text-text-faint">Deliberate stops</div>
        <FlowRow from="active" fromKind="settled" label="pause request" to="paused" toKind="neutral" />
        <FlowRow from="paused" fromKind="neutral" label="resume request" to="active" toKind="settled" />
        <FlowRow from="active" fromKind="settled" label="cancel request" to="cancelled" toKind="neutral" />
      </div>

      <p>
        Any transition not listed here is rejected outright. That&rsquo;s deliberate — it prevents
        accidental state changes that could create double billing or phantom access.
      </p>

      <h2>Every legal transition</h2>
      <table>
        <thead>
          <tr>
            <th>Current</th>
            <th>Event</th>
            <th>Next</th>
            <th>Why</th>
          </tr>
        </thead>
        <tbody>
          {transitions.map((row, i) => (
            <tr key={i}>
              <td>{row[0]}</td>
              <td>{row[1]}</td>
              <td>{row[2]}</td>
              <td>{row[3]}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Three transitions worth understanding deeply</h2>

      <h3>How a past_due subscription heals</h3>
      <p>
        Recovery is not just retries. A <code>past_due</code> subscription heals to <code>active</code>{' '}
        either because a scheduled retry succeeded, or because a transfer arrived that matched
        the open invoice. Both are treated as a genuine recovery, not a special case.
      </p>

      <h3>What payment_uncertain means</h3>
      <p>
        It exists for one reason: a timeout is not the same thing as a failure. If Nomba hasn&rsquo;t
        confirmed the outcome yet, Somba doesn&rsquo;t know whether money moved. Rather than risk a
        double charge, the subscription freezes here until a verification pass settles the truth.
        It never auto-retries in this state, because retrying blind is exactly the mistake it
        exists to prevent.
      </p>

      <h3>How a pushed transfer restores an active subscription</h3>
      <p>
        When a customer pushes money to their dedicated virtual account, Somba matches the
        transfer against an open invoice by amount and reference. A good match heals the
        subscription backward to <code>active</code> — the customer never has to contact support to
        prove they paid.
      </p>
    </DocsPage>
  )
}
