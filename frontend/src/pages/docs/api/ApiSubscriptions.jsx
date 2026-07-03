import ApiPage from '../../../components/ApiPage'
import Endpoint from '../../../components/Endpoint'

const auth = { name: 'Authorization', type: 'Bearer sk-somba-<key_id>.<secret>' }
const idem = { name: 'Idempotency-Key', type: 'string', required: true }

const sub = `{
  "id": "sub_xxx",
  "status": "active",
  "customer_id": "cus_xxx",
  "plan_id": "plan_xxx",
  "current_period_start": "2026-07-01T00:00:00Z",
  "current_period_end": "2026-07-31T23:59:59Z",
  "next_bill_date": "2026-08-01T00:00:00Z",
  "created_at": "2026-07-01T09:00:00Z"
}`

export default function ApiSubscriptions() {
  return (
    <ApiPage
      eyebrow="API reference"
      title="Subscriptions"
      path="/docs/api/subscriptions"
      description="Start, read, and manage the live billing relationship between a customer and a plan."
    >
      <Endpoint
        id="create"
        method="POST"
        path="/v1/subscriptions"
        description="Creates a subscription for a customer on a plan."
        headers={[auth, idem]}
        body={[
          { name: 'customer_id', type: 'string', required: true },
          { name: 'plan_id', type: 'string', required: true },
          { name: 'trial_days', type: 'integer', note: 'overrides plan default' },
        ]}
        returns="The subscription object."
        errors={['customer_not_found', 'plan_not_found', 'plan_archived']}
        curl={`curl -X POST https://somba.ddns.net/v1/subscriptions \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>" \\
  -H "Idempotency-Key: sub-kemi-001" \\
  -H "Content-Type: application/json" \\
  -d '{
    "customer_id": "cus_xxx",
    "plan_id": "plan_xxx"
  }'`}
        response={sub}
      />

      <Endpoint
        id="read"
        method="GET"
        path="/v1/subscriptions/:id"
        description="Reads one subscription."
        headers={[auth]}
        returns="The subscription object."
        errors={['unauthorized', 'subscription_not_found']}
        curl={`curl https://somba.ddns.net/v1/subscriptions/sub_xxx \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>"`}
        response={sub}
      />

      <Endpoint
        id="update"
        method="PATCH"
        path="/v1/subscriptions/:id"
        description="Changes the plan on a subscription and calculates proration for the change."
        headers={[auth, idem]}
        body={[{ name: 'plan_id', type: 'string', required: true }]}
        returns="The updated subscription, including the proration invoice if one was generated."
        errors={['unauthorized', 'subscription_not_found', 'plan_not_found', 'plan_archived']}
        curl={`curl -X PATCH https://somba.ddns.net/v1/subscriptions/sub_xxx \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>" \\
  -H "Idempotency-Key: upgrade-sub-xxx-001" \\
  -d '{ "plan_id": "plan_pro" }'`}
        response={`{
  "id": "sub_xxx",
  "status": "active",
  "plan_id": "plan_pro",
  "latest_invoice": { "id": "inv_yyy", "type": "proration", "amount": 560000 }
}`}
      />

      <Endpoint
        id="cancel"
        method="POST"
        path="/v1/subscriptions/:id/cancel"
        description="Cancels a subscription."
        headers={[auth, idem]}
        returns="The subscription object with status cancelled."
        errors={['unauthorized', 'subscription_not_found', 'invalid_transition']}
        curl={`curl -X POST https://somba.ddns.net/v1/subscriptions/sub_xxx/cancel \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>" \\
  -H "Idempotency-Key: cancel-sub-xxx-001"`}
        response={`{ "id": "sub_xxx", "status": "cancelled" }`}
      />

      <Endpoint
        id="pause"
        method="POST"
        path="/v1/subscriptions/:id/pause"
        description="Pauses a subscription. Billing stops until it's resumed."
        headers={[auth, idem]}
        returns="The subscription object with status paused."
        errors={['unauthorized', 'subscription_not_found', 'invalid_transition']}
        curl={`curl -X POST https://somba.ddns.net/v1/subscriptions/sub_xxx/pause \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>" \\
  -H "Idempotency-Key: pause-sub-xxx-001"`}
        response={`{ "id": "sub_xxx", "status": "paused" }`}
      />

      <Endpoint
        id="resume"
        method="POST"
        path="/v1/subscriptions/:id/resume"
        description="Resumes a paused subscription."
        headers={[auth, idem]}
        returns="The subscription object with status active."
        errors={['unauthorized', 'subscription_not_found', 'invalid_transition']}
        curl={`curl -X POST https://somba.ddns.net/v1/subscriptions/sub_xxx/resume \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>" \\
  -H "Idempotency-Key: resume-sub-xxx-001"`}
        response={`{ "id": "sub_xxx", "status": "active" }`}
      />

      <Endpoint
        id="retry"
        method="POST"
        path="/v1/subscriptions/:id/retry"
        description="Asks Somba to retry a failed payment immediately, ahead of its scheduled recovery time."
        headers={[auth, idem]}
        returns="The subscription object."
        errors={['unauthorized', 'subscription_not_found', 'invalid_transition']}
        curl={`curl -X POST https://somba.ddns.net/v1/subscriptions/sub_xxx/retry \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>" \\
  -H "Idempotency-Key: retry-sub-xxx-001"`}
        response={`{ "id": "sub_xxx", "status": "past_due" }`}
      />
    </ApiPage>
  )
}
