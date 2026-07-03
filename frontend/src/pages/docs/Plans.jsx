import DocsPage from '../../components/DocsPage'
import CodeBlock from '../../components/CodeBlock'

const plan = `{
  "id": "plan_xxx",
  "name": "Gym — Bimonthly",
  "amount": 2500000,
  "currency": "NGN",
  "interval": "month",
  "interval_count": 2,
  "trial_days": 7,
  "status": "active"
}`

export default function Plans() {
  return (
    <DocsPage
      eyebrow="Core concepts"
      title="Plans"
      path="/docs/plans"
      description="A plan is the billing template — amount, currency, and how often it's charged."
      code={<CodeBlock title="A plan object">{plan}</CodeBlock>}
    >
      <p>
        A plan defines what a customer pays and how often. Subscriptions point to a plan; the
        plan is where the amount and cadence actually live.
      </p>

      <h2>interval and interval_count</h2>
      <p>
        Cadence is two fields, not a string to parse. &ldquo;Every 2 months&rdquo; is{' '}
        <code>interval: month</code> with <code>interval_count: 2</code>. &ldquo;Every year&rdquo; is{' '}
        <code>interval: year</code> with <code>interval_count: 1</code>.
      </p>

      <h2>Active vs. archived</h2>
      <p>
        Archiving a plan does not touch existing subscriptions &mdash; they keep billing exactly
        as before. It only blocks new subscriptions from being created against it. This is how
        you retire a pricing tier without disrupting customers already on it.
      </p>

      <div className="flex flex-col gap-4">
        <h2>Creating a plan</h2>
        <CodeBlock title="Request">{`curl -X POST https://somba.ddns.net/v1/plans \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>" \\
  -H "Idempotency-Key: plan-gym-monthly-001" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Gym — Monthly",
    "amount": 1500000,
    "currency": "NGN",
    "interval": "month",
    "interval_count": 1
  }'`}</CodeBlock>
        <CodeBlock title="Response">{`{
  "id": "plan_xxx",
  "name": "Gym — Monthly",
  "amount": 1500000,
  "currency": "NGN",
  "interval": "month",
  "interval_count": 1,
  "status": "active"
}`}</CodeBlock>
      </div>
    </DocsPage>
  )
}
