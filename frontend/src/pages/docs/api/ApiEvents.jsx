import ApiPage from '../../../components/ApiPage'
import Endpoint from '../../../components/Endpoint'

const auth = { name: 'Authorization', type: 'Bearer sk-somba-<key_id>.<secret>' }
const idem = { name: 'Idempotency-Key', type: 'string', required: true }

export default function ApiEvents() {
  return (
    <ApiPage
      eyebrow="API reference"
      title="Events"
      path="/docs/api/events"
      description="List published events and replay one you missed."
    >
      <Endpoint
        id="list"
        method="GET"
        path="/v1/events"
        description="Lists published events for your merchant, most recent first."
        headers={[auth]}
        body={[{ name: 'type', type: 'string', note: 'filter by event type' }]}
        returns="An array of event objects."
        errors={['unauthorized']}
        curl={`curl "https://somba.ddns.net/v1/events?type=charge.failed" \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>"`}
        response={`{
  "data": [
    { "id": "evt_xxx", "type": "charge.failed", "created_at": "2026-07-01T09:00:00Z" }
  ]
}`}
      />

      <Endpoint
        id="replay"
        method="POST"
        path="/v1/events/:id/replay"
        description="Replays a prior event to your webhook endpoint intentionally — useful if a delivery was missed."
        headers={[auth, idem]}
        returns="The event object."
        errors={['unauthorized', 'event_not_found']}
        curl={`curl -X POST https://somba.ddns.net/v1/events/evt_xxx/replay \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>" \\
  -H "Idempotency-Key: replay-evt-xxx-001"`}
        response={`{ "id": "evt_xxx", "type": "charge.failed", "replayed": true }`}
      />
    </ApiPage>
  )
}
