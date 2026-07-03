import DocsPage from '../../components/DocsPage'
import CodeBlock from '../../components/CodeBlock'

const customer = `{
  "id": "cus_xxx",
  "external_id": "user_8823",
  "email": "kemi@example.com",
  "name": "Kemi Adegoke",
  "va_id": "va_xxx",
  "va_account_no": "9012345678",
  "credit_balance": 0
}`

export default function Customers() {
  return (
    <DocsPage
      eyebrow="Core concepts"
      title="Customers"
      path="/docs/customers"
      description="A customer is the identity being billed, plus whatever Somba needs to charge or recover from them."
      code={<CodeBlock title="A customer object">{customer}</CodeBlock>}
    >
      <p>
        A customer record ties a billing identity to your own user. It also holds the payment
        token reference and, once assigned, a dedicated virtual account for transfer recovery.
      </p>

      <h2>external_id</h2>
      <p>
        Set <code>external_id</code> to your own user ID at creation time. Every lookup — from a
        webhook payload, from a support ticket, from your own dashboard — can then resolve back
        to a customer by the identity your system already uses, without keeping a second mapping
        table.
      </p>

      <h2>The token key</h2>
      <p>
        Somba stores a reference to the customer&rsquo;s payment method, never the raw card number.
        Charges are made by asking Nomba to use the stored token — the card details themselves
        never pass through or live in Somba.
      </p>

      <h2>The virtual account</h2>
      <p>
        <code>va_id</code> and <code>va_account_no</code> are assigned automatically the first time
        transfer fallback recovery fires for this customer. Before that happens, both fields are
        empty.
      </p>

      <div className="flex flex-col gap-4">
        <h2>Creating a customer</h2>
        <p>
          Use <code>external_id</code> to store your own user ID, so you can always look a
          customer up by the identity your system already knows.
        </p>
        <CodeBlock title="Request">{`curl -X POST https://somba.ddns.net/v1/customers \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>" \\
  -H "Idempotency-Key: cus-kemi-001" \\
  -H "Content-Type: application/json" \\
  -d '{
    "external_id": "user_8823",
    "email": "kemi@example.com",
    "name": "Kemi Adegoke"
  }'`}</CodeBlock>
        <CodeBlock title="Response">{`{
  "id": "cus_xxx",
  "external_id": "user_8823",
  "email": "kemi@example.com",
  "name": "Kemi Adegoke",
  "credit_balance": 0
}`}</CodeBlock>
      </div>
    </DocsPage>
  )
}
