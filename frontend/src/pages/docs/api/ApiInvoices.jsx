import ApiPage from '../../../components/ApiPage'
import Endpoint from '../../../components/Endpoint'

const auth = { name: 'Authorization', type: 'Bearer sk-somba-<key_id>.<secret>' }

export default function ApiInvoices() {
  return (
    <ApiPage
      eyebrow="API reference"
      title="Invoices"
      path="/docs/api/invoices"
      description="Read-only records of what was owed for each billing period."
    >
      <Endpoint
        id="list"
        method="GET"
        path="/v1/invoices"
        description="Lists invoices for your merchant."
        headers={[auth]}
        body={[
          { name: 'subscription_id', type: 'string', note: 'filter to one subscription' },
          { name: 'status', type: 'string', note: '"draft" | "open" | "paid" | "uncollectible"' },
        ]}
        returns="An array of invoice objects."
        errors={['unauthorized']}
        curl={`curl "https://somba.ddns.net/v1/invoices?subscription_id=sub_xxx" \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>"`}
        response={`{
  "data": [
    { "id": "inv_xxx", "status": "paid", "amount": 1500000 }
  ]
}`}
      />

      <Endpoint
        id="read"
        method="GET"
        path="/v1/invoices/:id"
        description="Reads one invoice, including line items."
        headers={[auth]}
        returns="The invoice object."
        errors={['unauthorized', 'invoice_not_found']}
        curl={`curl https://somba.ddns.net/v1/invoices/inv_xxx \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>"`}
        response={`{
  "id": "inv_xxx",
  "status": "paid",
  "amount": 1500000,
  "period_start": "2026-07-01T00:00:00Z",
  "period_end": "2026-07-31T23:59:59Z"
}`}
      />
    </ApiPage>
  )
}
