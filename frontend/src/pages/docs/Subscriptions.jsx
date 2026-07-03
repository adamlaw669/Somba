import { Link } from 'react-router-dom'
import DocsPage from '../../components/DocsPage'
import CodeBlock from '../../components/CodeBlock'
import StatusPill from '../../components/StatusPill'

const subscription = `{
  "id": "sub_xxx",
  "status": "active",
  "customer_id": "cus_xxx",
  "plan_id": "plan_xxx",
  "current_period_start": "2026-07-01T00:00:00Z",
  "current_period_end": "2026-07-31T23:59:59Z",
  "next_bill_date": "2026-08-01T00:00:00Z",
  "created_at": "2026-07-01T09:00:00Z"
}`

const events = `subscription.active
subscription.past_due
subscription.paused
subscription.cancelled
payment.uncertain
payment.resolved`

export default function Subscriptions() {
  return (
    <DocsPage
      eyebrow="Core concepts"
      title="Subscriptions"
      path="/docs/subscriptions"
      description="The live billing relationship between a customer and a plan — and the thing Somba spends most of its effort protecting."
      code={
        <>
          <CodeBlock title="A subscription object">{subscription}</CodeBlock>
          <CodeBlock title="Events it can fire">{events}</CodeBlock>
        </>
      }
    >
      <p>
        A subscription is what you create when a customer commits to a plan. Somba tracks it
        through seven possible states, only allows the transitions that make sense, and fires a
        webhook every time the state changes.
      </p>

      <h2>A gym membership, in plain English</h2>
      <p>
        A customer signs up for a monthly gym plan and starts on <StatusPill kind="pending">trialing</StatusPill>.
        Their first payment succeeds, and the membership becomes <StatusPill kind="settled">active</StatusPill>. A
        month later, a renewal fails because the account is empty — the membership moves to{' '}
        <StatusPill kind="error">past_due</StatusPill> while Somba works on recovering it. Somba retries at a
        better time and it heals back to <StatusPill kind="settled">active</StatusPill>. Later, a renewal times
        out with no clear result, so the membership freezes at{' '}
        <StatusPill kind="pending">payment_uncertain</StatusPill> rather than guessing. A verification pass
        confirms the payment actually went through, and it heals back to{' '}
        <StatusPill kind="settled">active</StatusPill> again.
      </p>

      <p>
        The full state list and every legal transition between them are on{' '}
        <Link to="/docs/lifecycle" className="text-settled hover:underline">
          the subscription lifecycle
        </Link>{' '}
        page.
      </p>

      <h2>Grace period</h2>
      <p>
        A subscription in <code>past_due</code> is not immediately cut off. Somba gives it a grace
        window while recovery is attempted, so a customer who is genuinely going to pay doesn&rsquo;t
        lose access over a bad morning.
      </p>

      <h2>Heal-backward</h2>
      <p>
        Heal-backward means a subscription can move from a worse state back to a healthy one
        without you doing anything. If a payment that looked failed or uncertain turns out to
        have succeeded, the subscription heals back to <code>active</code> on its own — your
        customer never needs to re-subscribe.
      </p>

      <div className="flex flex-col gap-4">
        <h2>Subscribing a customer</h2>
        <p>
          Subscribing starts the billing relationship. Somba schedules the first charge and every
          renewal after it — you don&rsquo;t need a cron job or a scheduler of your own.
        </p>
        <CodeBlock title="Request">{`curl -X POST https://somba.ddns.net/v1/subscriptions \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>" \\
  -H "Idempotency-Key: sub-kemi-001" \\
  -H "Content-Type: application/json" \\
  -d '{
    "customer_id": "cus_xxx",
    "plan_id": "plan_xxx"
  }'`}</CodeBlock>
        <CodeBlock title="Response">{`{
  "id": "sub_xxx",
  "status": "active",
  "customer_id": "cus_xxx",
  "plan_id": "plan_xxx",
  "current_period_start": "2026-07-01T00:00:00Z",
  "current_period_end": "2026-07-31T23:59:59Z",
  "next_bill_date": "2026-08-01T00:00:00Z"
}`}</CodeBlock>
      </div>

      <div className="flex flex-col gap-4">
        <h2>Reading it back</h2>
        <CodeBlock title="Request">{`curl https://somba.ddns.net/v1/subscriptions/sub_xxx \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>"`}</CodeBlock>
        <CodeBlock title="Response">{`{
  "id": "sub_xxx",
  "status": "active",
  "next_bill_date": "2026-08-01T00:00:00Z"
}`}</CodeBlock>
      </div>
    </DocsPage>
  )
}
