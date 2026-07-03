import DocsPage from '../../components/DocsPage'
import CodeBlock from '../../components/CodeBlock'

const verifyPython = `import hmac, hashlib

def verify(payload: bytes, sig: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, sig)`

const eventList = `invoice.created
charge.succeeded
charge.failed          # includes failure_reason and failure_class
charge.retrying
charge.recovered       # includes recovery_path: timing | transfer
transfer.requested     # VA number and amount included in payload
transfer.reconciled
subscription.past_due
subscription.active
subscription.paused
subscription.cancelled
payment.uncertain
payment.resolved
anomaly.detected`

export default function EventsWebhooks() {
  return (
    <DocsPage
      eyebrow="Core concepts"
      title="Events & webhooks"
      path="/docs/events-webhooks"
      description="Somba notifies you when anything about a subscription, charge, or transfer changes."
      code={
        <>
          <CodeBlock title="webhook.py">{verifyPython}</CodeBlock>
          <CodeBlock title="Outbound events">{eventList}</CodeBlock>
        </>
      }
    >
      <p>
        Every important state change fires a webhook to the URL you configured, signed with your
        webhook secret so you can confirm it actually came from Somba.
      </p>

      <div className="flex flex-col gap-4">
        <h2>What you receive</h2>
        <p>
          Once a charge succeeds, Somba posts a <code>charge.succeeded</code> event to your
          webhook URL. That&rsquo;s the moment to unlock access in your product.
        </p>
        <CodeBlock title="POST to your webhook URL">{`{
  "type": "charge.succeeded",
  "data": {
    "subscription_id": "sub_xxx",
    "amount": 1500000,
    "currency": "NGN"
  }
}`}</CodeBlock>
      </div>

      <h2>Verifying the signature</h2>
      <p>
        Compute an HMAC-SHA256 of the raw request body using your webhook secret, and compare it
        against the signature Somba sends — using a constant-time comparison, never a plain{' '}
        <code>==</code>.
      </p>

      <h2>Retries and dead letters</h2>
      <p>
        If your endpoint doesn&rsquo;t return a 2xx, Somba retries the delivery on a backoff schedule.
        After the retry schedule is exhausted, the delivery is marked dead-lettered rather than
        retried forever.
      </p>

      <h2>Replaying an event</h2>
      <p>
        If you missed a delivery — an endpoint was down, a deploy was mid-flight — you can ask
        Somba to replay any past event by ID rather than trying to reconstruct state yourself.
      </p>
    </DocsPage>
  )
}
