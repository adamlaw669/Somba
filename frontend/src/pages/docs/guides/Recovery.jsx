import DocsPage from '../../../components/DocsPage'
import CodeBlock from '../../../components/CodeBlock'

const why = `# Why not just retry on a second rail?
# If the account was empty on rail A, it's usually
# still empty on rail B — same customer, same balance.
# Somba prefers: wait for a better window, or ask for
# a transfer, over blind rerouting between pull rails.`

export default function Recovery() {
  return (
    <DocsPage
      eyebrow="Guides"
      title="Understand recovery"
      path="/docs/guides/recovery"
      description="Why Somba treats a failed charge as a different problem to solve, not a final answer."
      code={<CodeBlock title="A design decision, not an oversight">{why}</CodeBlock>}
    >
      <p>
        Most payment tools stop at &ldquo;charge failed.&rdquo; Somba treats that as the start of a
        second decision: is this worth retrying, and if so, when and how?
      </p>

      <h2>Timing-based recovery</h2>
      <p>
        If a customer&rsquo;s account was empty at 8 a.m., that&rsquo;s not proof they&rsquo;ll still be empty by
        evening. Somba uses signals like expected payday and recent incoming transfers to retry
        at a moment when the charge is actually likely to succeed, instead of hammering the same
        card on a fixed interval.
      </p>

      <h2>Transfer fallback</h2>
      <p>
        When pulling stops making sense — a dead card, a pattern of hard declines — Somba asks
        the customer to push money to a dedicated virtual account instead. Transfers are
        familiar and visible in Nigeria, and easy to reconcile automatically once they land.
      </p>

      <h2>Why not just try a second pull rail</h2>
      <p>
        It sounds like an obvious next step, but it usually just reaches the same empty account
        through a different door — more noise, more failed attempts, no better outcome. Somba&rsquo;s
        position is that timing plus transfer fallback solves the real problem more honestly than
        rerouting between rails does.
      </p>

      <div className="flex flex-col gap-4">
        <h2>What a transfer request looks like</h2>
        <CodeBlock title="transfer.requested webhook">{`{
  "type": "transfer.requested",
  "data": {
    "subscription_id": "sub_xxx",
    "va_account_no": "9012345678",
    "amount": 1500000
  }
}`}</CodeBlock>
      </div>
    </DocsPage>
  )
}
