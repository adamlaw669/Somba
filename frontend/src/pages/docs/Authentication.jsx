import { Link } from 'react-router-dom'
import DocsPage from '../../components/DocsPage'
import CodeBlock from '../../components/CodeBlock'

export default function Authentication() {
  return (
    <DocsPage
      eyebrow="Getting started"
      title="Authentication"
      path="/docs/authentication"
      description="Every request is authenticated with a bearer token scoped to your merchant account."
    >
      <p className="rounded-sm border border-pending/40 bg-pending-dim/20 px-4 py-3 text-[14px] leading-6 text-text">
        You&rsquo;ll need an API key before any of these requests will work.{' '}
        <Link to="/signup" className="text-settled hover:underline">
          Click here
        </Link>{' '}
        to create an account and mint one.
      </p>

      <p>
        Your API key has two parts: a <code>key_id</code>, which Somba uses to look up your
        merchant, and a secret, which is checked against the bcrypt hash Somba stores. Only the
        hash is ever kept &mdash; Somba cannot show you the raw secret again after it&rsquo;s issued.
      </p>

      <p>
        Pass the key on every request as a bearer token. It&rsquo;s the only credential your code
        needs &mdash; there&rsquo;s no session to manage on the API side. The key itself is minted from
        your dashboard, which you get into with your email and password.
      </p>

      <div className="flex flex-col gap-4">
        <h2>A request with a valid key</h2>
        <CodeBlock title="Request">{`curl https://somba.ddns.net/v1/plans \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>"`}</CodeBlock>
        <CodeBlock title="Response">{`{
  "data": [
    { "id": "plan_xxx", "name": "Gym — Monthly", "status": "active" }
  ]
}`}</CodeBlock>
      </div>

      <p>
        Don&rsquo;t have a key yet?{' '}
        <Link to="/signup" className="text-settled hover:underline">
          Create an account
        </Link>{' '}
        to get into your dashboard, or{' '}
        <Link to="/login" className="text-settled hover:underline">
          log in
        </Link>{' '}
        if you already have one, then mint a key from there.
      </p>

      <p>
        Your key is shown to you exactly once, when you mint it. If you lose it, generate a new
        one from the dashboard &mdash; there is no recovery flow for a lost secret, by design.
      </p>

      <div className="flex flex-col gap-4">
        <h2>A missing or invalid key</h2>
        <p>
          A request with no bearer token is rejected with <code>unauthorized</code>. A request
          with a token that doesn&rsquo;t match any merchant is rejected with{' '}
          <code>invalid_api_key</code>. Both happen before anything else runs.
        </p>
        <CodeBlock title="Request">{`curl https://somba.ddns.net/v1/plans \\
  -H "Authorization: Bearer sk-somba-wrong"`}</CodeBlock>
        <CodeBlock title="Response → 401">{`{
  "error": {
    "code": "invalid_api_key",
    "message": "Invalid API key"
  }
}`}</CodeBlock>
      </div>
    </DocsPage>
  )
}
