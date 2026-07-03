import ApiPage from '../../../components/ApiPage'
import Endpoint from '../../../components/Endpoint'

const auth = { name: 'Authorization', type: 'Bearer sk-somba-<key_id>.<secret>' }
const idem = { name: 'Idempotency-Key', type: 'string', required: true }

export default function ApiPlans() {
  return (
    <ApiPage
      eyebrow="API reference"
      title="Plans"
      path="/docs/api/plans"
      description="Create and manage the billing templates subscriptions point to."
    >
      <Endpoint
        id="create"
        method="POST"
        path="/v1/plans"
        description="Creates a plan."
        headers={[auth, idem]}
        body={[
          { name: 'name', type: 'string', required: true },
          { name: 'amount', type: 'integer (kobo)', required: true },
          { name: 'currency', type: 'string', required: true, note: 'e.g. "NGN"' },
          { name: 'interval', type: 'string', required: true, note: '"day" | "week" | "month" | "year"' },
          { name: 'interval_count', type: 'integer', note: 'default 1' },
          { name: 'trial_days', type: 'integer' },
        ]}
        returns="The plan object."
        errors={['unauthorized', 'idempotency_key_required']}
        curl={`curl -X POST https://somba.ddns.net/v1/plans \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>" \\
  -H "Idempotency-Key: plan-gym-monthly-001" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Gym — Monthly",
    "amount": 1500000,
    "currency": "NGN",
    "interval": "month",
    "interval_count": 1
  }'`}
        response={`{
  "id": "plan_xxx",
  "name": "Gym — Monthly",
  "amount": 1500000,
  "currency": "NGN",
  "interval": "month",
  "interval_count": 1,
  "trial_days": 0,
  "status": "active"
}`}
      />

      <Endpoint
        id="list"
        method="GET"
        path="/v1/plans"
        description="Lists plans for your merchant."
        headers={[auth]}
        returns="An array of plan objects."
        errors={['unauthorized']}
        curl={`curl https://somba.ddns.net/v1/plans \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>"`}
        response={`{
  "data": [
    { "id": "plan_xxx", "name": "Gym — Monthly", "status": "active" }
  ]
}`}
      />

      <Endpoint
        id="read"
        method="GET"
        path="/v1/plans/:id"
        description="Reads one plan."
        headers={[auth]}
        returns="The plan object."
        errors={['unauthorized', 'plan_not_found']}
        curl={`curl https://somba.ddns.net/v1/plans/plan_xxx \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>"`}
        response={`{
  "id": "plan_xxx",
  "name": "Gym — Monthly",
  "status": "active"
}`}
      />

      <Endpoint
        id="update"
        method="PATCH"
        path="/v1/plans/:id"
        description="Updates a plan's name or metadata. Amount and interval are immutable once subscriptions exist."
        headers={[auth, idem]}
        body={[{ name: 'name', type: 'string', note: 'optional' }]}
        returns="The updated plan object."
        errors={['unauthorized', 'plan_not_found']}
        curl={`curl -X PATCH https://somba.ddns.net/v1/plans/plan_xxx \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>" \\
  -H "Idempotency-Key: plan-rename-001" \\
  -d '{ "name": "Gym — Monthly (2026)" }'`}
        response={`{
  "id": "plan_xxx",
  "name": "Gym — Monthly (2026)",
  "status": "active"
}`}
      />

      <Endpoint
        id="archive"
        method="DELETE"
        path="/v1/plans/:id"
        description="Archives a plan. Existing subscriptions keep billing; no new subscriptions can be created against it."
        headers={[auth, idem]}
        returns="The archived plan object."
        errors={['unauthorized', 'plan_not_found']}
        curl={`curl -X DELETE https://somba.ddns.net/v1/plans/plan_xxx \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>" \\
  -H "Idempotency-Key: plan-archive-001"`}
        response={`{
  "id": "plan_xxx",
  "status": "archived"
}`}
      />
    </ApiPage>
  )
}
