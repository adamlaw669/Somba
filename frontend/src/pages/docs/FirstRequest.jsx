import DocsPage from '../../components/DocsPage'
import CodeBlock from '../../components/CodeBlock'

export default function FirstRequest() {
  return (
    <DocsPage
      eyebrow="Getting started"
      title="Your first request"
      path="/docs/first-request"
      description="Create a plan and see it come back exactly as you defined it."
    >
      <div className="flex flex-col gap-4">
        <p>
          A plan defines the amount and cadence. Create one for a gym membership billed monthly
          at ₦15,000.00 — amounts are always in kobo, so <code>1500000</code> kobo is ₦15,000.00.
        </p>
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
