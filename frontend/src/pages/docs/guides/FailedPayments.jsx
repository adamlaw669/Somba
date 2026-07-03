import DocsPage from '../../../components/DocsPage'
import CodeBlock from '../../../components/CodeBlock'

const classes = `empty_account   → retry later, better funding window
broken_card     → stop pulling, switch to transfer fallback
transient       → retry once, then decide
risk            → stop, do not keep pushing
unknown         → bounded retry, then fall back safely`

export default function FailedPayments() {
  return (
    <DocsPage
      eyebrow="Guides"
      title="Handle failed payments"
      path="/docs/guides/failed-payments"
      description="You don't need to build retry logic. Listen to webhooks and update your UI — Somba does the rest."
      code={<CodeBlock title="Failure classes">{classes}</CodeBlock>}
    >
      <p>
        When a charge fails, Somba classifies the reason and picks the next step itself: retry
        at a better time, switch to transfer fallback, or stop entirely if the payment looks
        unsafe. Your job is to react to the webhooks, not to reimplement this logic.
      </p>

      <h2>Timing recovery</h2>
      <p>
        The account was probably just empty. Somba schedules a retry for a more likely funding
        window and sends <code>charge.retrying</code>. If it later succeeds, you get{' '}
        <code>charge.recovered</code> with <code>recovery_path: "timing"</code> — update the
        subscription status in your UI and move on.
      </p>

      <h2>Transfer fallback</h2>
      <p>
        The card is dead or pulling no longer makes sense. Somba sends{' '}
        <code>transfer.requested</code> with a dedicated virtual account number — show that to the
        customer. Once the transfer is reconciled, you get <code>charge.recovered</code> with{' '}
        <code>recovery_path: "transfer"</code>.
      </p>

      <h2>Fraud block</h2>
      <p>
        The payment looked unsafe. Somba does not retry. You&rsquo;ll see the subscription move to{' '}
        <code>past_due</code> without a scheduled recovery — treat this as a case for manual
        review, not an automatic retry candidate.
      </p>

      <div className="flex flex-col gap-4">
        <h2>Asking for an immediate retry</h2>
        <p>
          If a customer tells you they&rsquo;ve topped up, you can ask Somba to retry right away
          instead of waiting for the scheduled window.
        </p>
        <CodeBlock title="Request">{`curl -X POST https://somba.ddns.net/v1/subscriptions/sub_xxx/retry \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>" \\
  -H "Idempotency-Key: retry-sub-xxx-001"`}</CodeBlock>
        <CodeBlock title="Response">{`{ "id": "sub_xxx", "status": "past_due" }`}</CodeBlock>
      </div>
    </DocsPage>
  )
}
