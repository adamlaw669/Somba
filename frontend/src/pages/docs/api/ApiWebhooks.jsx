import ApiPage from '../../../components/ApiPage'
import Endpoint from '../../../components/Endpoint'

export default function ApiWebhooks() {
  return (
    <ApiPage
      eyebrow="API reference"
      title="Webhooks (inbound)"
      path="/docs/api/webhooks"
      description="The endpoint Nomba calls to notify Somba of payment and transfer results. You don't call this — Nomba does."
    >
      <Endpoint
        id="nomba"
        method="POST"
        path="/v1/webhooks/nomba"
        description="Receives Nomba events after HMAC verification. Any state change from this endpoint happens only after the signature checks out."
        headers={[{ name: 'X-Nomba-Signature', type: 'string' }]}
        returns="204 No Content."
        errors={['invalid_signature']}
        curl={`# Nomba sends this — you don't call it directly.
POST /v1/webhooks/nomba
X-Nomba-Signature: t=..., v1=...`}
        response={`HTTP/1.1 204 No Content`}
      />
    </ApiPage>
  )
}
