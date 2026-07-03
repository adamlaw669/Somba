import DocsPage from '../../../components/DocsPage'
import CodeBlock from '../../../components/CodeBlock'

const python = `import hmac, hashlib

def verify(payload: bytes, sig: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, sig)`

const node = `const crypto = require("crypto");

function verify(payload, sig, secret) {
  const expected = crypto
    .createHmac("sha256", secret)
    .update(payload)
    .digest("hex");
  return crypto.timingSafeEqual(
    Buffer.from(expected),
    Buffer.from(sig)
  );
}`

const curl = `# Recompute locally and diff against the
# X-Somba-Signature header — never trust an
# unsigned or unverified payload.
echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET"`

export default function VerifyWebhooks() {
  return (
    <DocsPage
      eyebrow="Guides"
      title="Verify webhooks"
      path="/docs/guides/verify-webhooks"
      code={
        <>
          <CodeBlock title="verify.py">{python}</CodeBlock>
          <CodeBlock title="verify.js">{node}</CodeBlock>
          <CodeBlock title="curl / openssl">{curl}</CodeBlock>
        </>
      }
    >
      <p>
        Recompute the HMAC-SHA256 of the raw request body using your webhook secret, and compare
        it against the <code>X-Somba-Signature</code> header with a constant-time comparison.
        Never process a payload whose signature doesn&rsquo;t match.
      </p>

      <div className="flex flex-col gap-4">
        <CodeBlock title="verify.py">{python}</CodeBlock>
      </div>
    </DocsPage>
  )
}
