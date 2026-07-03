import DocsPage from '../../../components/DocsPage'
import CodeBlock from '../../../components/CodeBlock'

const patchCall = `curl -X PATCH https://somba.ddns.net/v1/subscriptions/sub_xxx \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>" \\
  -H "Idempotency-Key: upgrade-sub-xxx-001" \\
  -H "Content-Type: application/json" \\
  -d '{
    "plan_id": "plan_pro"
  }'`

const patchResponse = `{
  "id": "sub_xxx",
  "status": "active",
  "plan_id": "plan_pro",
  "latest_invoice": {
    "id": "inv_yyy",
    "type": "proration",
    "amount": 560000,
    "line_items": [
      { "type": "credit", "description": "Unused time on Basic", "amount": -420000 },
      { "type": "charge",  "description": "Remaining time on Pro", "amount": 980000 }
    ]
  }
}`

export default function Proration() {
  return (
    <DocsPage
      eyebrow="Guides"
      title="Plan changes & proration"
      path="/docs/guides/proration"
      description="Upgrading or downgrading mid-cycle produces a fair, explainable charge — never a full second month."
      code={
        <>
          <CodeBlock title="Upgrade">{patchCall}</CodeBlock>
          <CodeBlock title="Response">{patchResponse}</CodeBlock>
        </>
      }
    >
      <p>
        Change a customer&rsquo;s plan with a single <code>PATCH</code> call. Somba works out how much
        value is left on the old plan, how much the new plan costs for the remaining days, and
        charges only the difference.
      </p>

      <div className="flex flex-col gap-4">
        <CodeBlock title="Request">{patchCall}</CodeBlock>
        <CodeBlock title="Response">{patchResponse}</CodeBlock>
      </div>

      <p>
        In the example, the customer had unused time on Basic worth ₦4,200.00. The remaining
        days on Pro cost ₦9,800.00. Somba charges the net ₦5,600.00 immediately, and returns the
        proration invoice with both line items so the amount is never a mystery to you or the
        customer.
      </p>

      <h2>Downgrades work in reverse</h2>
      <p>
        Downgrading stores the unused value as <code>credit_balance</code> on the customer instead
        of refunding it. The next renewal checks that balance before charging — if it fully
        covers the renewal, Somba doesn&rsquo;t call Nomba for that cycle at all.
      </p>
    </DocsPage>
  )
}
