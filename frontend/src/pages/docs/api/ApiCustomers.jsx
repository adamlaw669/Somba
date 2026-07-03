import ApiPage from '../../../components/ApiPage'
import Endpoint from '../../../components/Endpoint'

const auth = { name: 'Authorization', type: 'Bearer sk-somba-<key_id>.<secret>' }
const idem = { name: 'Idempotency-Key', type: 'string', required: true }

export default function ApiCustomers() {
  return (
    <ApiPage
      eyebrow="API reference"
      title="Customers"
      path="/docs/api/customers"
      description="Create and read the identities being billed."
    >
      <Endpoint
        id="create"
        method="POST"
        path="/v1/customers"
        description="Creates a customer record."
        headers={[auth, idem]}
        body={[
          { name: 'external_id', type: 'string', required: true, note: 'your own user ID' },
          { name: 'email', type: 'string', required: true },
          { name: 'name', type: 'string' },
        ]}
        returns="The customer object."
        errors={['unauthorized', 'idempotency_key_required']}
        curl={`curl -X POST https://somba.ddns.net/v1/customers \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>" \\
  -H "Idempotency-Key: cus-kemi-001" \\
  -H "Content-Type: application/json" \\
  -d '{
    "external_id": "user_8823",
    "email": "kemi@example.com",
    "name": "Kemi Adegoke"
  }'`}
        response={`{
  "id": "cus_xxx",
  "external_id": "user_8823",
  "email": "kemi@example.com",
  "name": "Kemi Adegoke",
  "credit_balance": 0
}`}
      />

      <Endpoint
        id="read"
        method="GET"
        path="/v1/customers/:id"
        description="Reads one customer."
        headers={[auth]}
        returns="The customer object."
        errors={['unauthorized', 'customer_not_found']}
        curl={`curl https://somba.ddns.net/v1/customers/cus_xxx \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>"`}
        response={`{
  "id": "cus_xxx",
  "external_id": "user_8823",
  "email": "kemi@example.com"
}`}
      />

      <Endpoint
        id="update"
        method="PATCH"
        path="/v1/customers/:id"
        description="Updates customer details."
        headers={[auth, idem]}
        body={[
          { name: 'email', type: 'string' },
          { name: 'name', type: 'string' },
        ]}
        returns="The updated customer object."
        errors={['unauthorized', 'customer_not_found']}
        curl={`curl -X PATCH https://somba.ddns.net/v1/customers/cus_xxx \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>" \\
  -H "Idempotency-Key: cus-update-001" \\
  -d '{ "email": "kemi.new@example.com" }'`}
        response={`{
  "id": "cus_xxx",
  "email": "kemi.new@example.com"
}`}
      />
    </ApiPage>
  )
}
