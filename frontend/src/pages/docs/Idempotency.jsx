import DocsPage from '../../components/DocsPage'
import CodeBlock from '../../components/CodeBlock'

const header = `Idempotency-Key: sub-kemi-2026-07-01`

const missingKey = `{
  "error": {
    "code": "missing_idempotency_key",
    "message": "Mutating requests require an Idempotency-Key header",
    "param": "Idempotency-Key"
  }
}`

const reuseKey = `{
  "error": {
    "code": "idempotency_key_reuse",
    "message": "Idempotency-Key was reused with a different request body",
    "param": "Idempotency-Key"
  }
}`

export default function Idempotency() {
  return (
    <DocsPage
      eyebrow="Getting started"
      title="Idempotency"
      path="/docs/idempotency"
      description="Send the same request twice with the same key — Somba returns the original response without creating a duplicate."
      code={
        <>
          <CodeBlock title="Header">{header}</CodeBlock>
          <CodeBlock title="Missing → 400">{missingKey}</CodeBlock>
          <CodeBlock title="Reused with a different body → 409">{reuseKey}</CodeBlock>
        </>
      }
    >
      <p>
        Every mutating request &mdash; <code>POST</code>, <code>PATCH</code>, or{' '}
        <code>DELETE</code> &mdash; requires an <code>Idempotency-Key</code> header. If your
        client retries a request because of a timeout or a dropped connection, Somba recognizes
        the key and returns the original response instead of creating a second subscription,
        invoice, or charge attempt.
      </p>

      <p>In plain English: doing the same action twice should have the same effect as doing it once.</p>

      <p>
        Somba stores the request fingerprint tied to your merchant, so retries stay safe even
        across process restarts on your side.
      </p>

      <h2>Constructing a good key</h2>
      <p>
        A key should be unique per logical action, not per HTTP attempt. A pattern like{' '}
        <code>sub-{'{customer}'}-{'{date}'}</code> works well &mdash; it&rsquo;s stable across retries of
        the same intent, but distinct from a genuinely new one you make later.
      </p>
    </DocsPage>
  )
}
