import DocsPage from '../../components/DocsPage'
import CodeBlock from '../../components/CodeBlock'

const invoice = `{
  "id": "inv_xxx",
  "subscription_id": "sub_xxx",
  "customer_id": "cus_xxx",
  "amount": 1500000,
  "status": "paid",
  "type": "recurring",
  "period_start": "2026-07-01T00:00:00Z",
  "period_end": "2026-07-31T23:59:59Z",
  "due_date": "2026-07-01T00:00:00Z",
  "paid_at": "2026-07-01T09:03:12Z"
}`

const lineItems = `{
  "id": "inv_yyy",
  "type": "proration",
  "line_items": [
    { "type": "credit", "description": "Unused time on Basic", "amount": -420000 },
    { "type": "charge",  "description": "Remaining time on Pro", "amount": 980000 }
  ],
  "amount": 560000
}`

export default function Invoices() {
  return (
    <DocsPage
      eyebrow="Core concepts"
      title="Invoices"
      path="/docs/invoices"
      description="One invoice per subscription per billing period — the financial record of what was owed."
      code={
        <>
          <CodeBlock title="A recurring invoice">{invoice}</CodeBlock>
          <CodeBlock title="A proration invoice">{lineItems}</CodeBlock>
        </>
      }
    >
      <p>
        Every billing period produces exactly one invoice for a subscription. Somba enforces
        this with a uniqueness constraint on the subscription and period together, so a retried
        billing run can never double-invoice the same period.
      </p>

      <h2>Status flow</h2>
      <p>
        An invoice moves from <code>draft</code> to <code>open</code> once it&rsquo;s finalized and ready to
        be charged, then to <code>paid</code> once a charge settles against it — or to{' '}
        <code>uncollectible</code> if recovery is exhausted without success.
      </p>

      <h2>Line items</h2>
      <p>
        Regular recurring invoices don&rsquo;t need a breakdown — the amount is the plan price. A
        proration invoice does: it carries line items showing the credit from the old plan and
        the charge for the new one, so the net amount is explainable rather than a single
        opaque number.
      </p>

      <div className="flex flex-col gap-4">
        <h2>Fetching an invoice</h2>
        <CodeBlock title="Request">{`curl https://somba.ddns.net/v1/invoices/inv_xxx \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>"`}</CodeBlock>
        <CodeBlock title="Response">{`{
  "id": "inv_xxx",
  "status": "paid",
  "amount": 1500000,
  "period_start": "2026-07-01T00:00:00Z",
  "period_end": "2026-07-31T23:59:59Z"
}`}</CodeBlock>
      </div>
    </DocsPage>
  )
}
