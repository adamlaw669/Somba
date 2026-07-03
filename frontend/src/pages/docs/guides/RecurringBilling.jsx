import DocsPage from '../../../components/DocsPage'
import CodeBlock from '../../../components/CodeBlock'

const steps = `# 1. Create the plan
POST /v1/plans        { name, amount, currency, interval, interval_count }

# 2. Create the customer
POST /v1/customers    { external_id, email, name }

# 3. Subscribe them
POST /v1/subscriptions { customer_id, plan_id }

# 4. Somba bills automatically on the cycle you set
# 5. You receive charge.succeeded on the first payment`

export default function RecurringBilling() {
  return (
    <DocsPage
      eyebrow="Guides"
      title="Set up recurring billing"
      path="/docs/guides/recurring-billing"
      description="A walkthrough from zero to a subscription that bills itself."
      code={<CodeBlock title="The whole flow">{steps}</CodeBlock>}
    >
      <p>
        Start by deciding your pricing shape and creating a plan for it. A plan is just an
        amount and a cadence — you can create as many as you have pricing tiers.
      </p>

      <p>
        Next, create a customer record the moment someone signs up in your product. Set{' '}
        <code>external_id</code> to the user ID you already have, so this record is always
        reachable from your own system without a second lookup table.
      </p>

      <p>
        Subscribe the customer to the plan. This is the point where billing actually starts —
        Somba calculates the first <code>current_period_start</code> and{' '}
        <code>current_period_end</code>, and schedules the first charge.
      </p>

      <div className="flex flex-col gap-4">
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
  "next_bill_date": "2026-08-01T00:00:00Z"
}`}</CodeBlock>
      </div>

      <p>
        From here you do nothing. Somba&rsquo;s scheduler finds subscriptions due for billing, attempts
        the charge, creates the invoice, and fires <code>charge.succeeded</code> or{' '}
        <code>charge.failed</code>. Listen for the success event to grant access, and you have a
        working recurring billing flow.
      </p>
    </DocsPage>
  )
}
