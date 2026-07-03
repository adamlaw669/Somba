import DocsPage from '../../components/DocsPage'
import CodeBlock from '../../components/CodeBlock'

const errorShape = `{
  "error": {
    "code":    "not_found",
    "message": "Subscription not found"
  }
}`

const errors = [
  ['unauthorized', '401', 'Missing bearer token'],
  ['invalid_api_key', '401', "Token doesn't match any merchant"],
  ['missing_idempotency_key', '400', 'POST/PATCH/DELETE missing the header'],
  ['idempotency_key_reuse', '409', 'Same key, different request body'],
  ['not_found', '404', 'Plan, customer, subscription, invoice, or event not found'],
  ['plan_archived', '400', "Can't subscribe or switch to an archived plan"],
  ['already_archived', '400', 'Plan is already archived'],
  ['invalid_status', '400', "Can't change plan on a subscription in this state"],
  ['no_change', '400', 'Subscription is already on that plan'],
]

export default function Errors() {
  return (
    <DocsPage
      eyebrow="Getting started"
      title="Errors"
      path="/docs/errors"
      description="Every error uses the same shape, so your client can handle them with one code path."
      code={<CodeBlock title="Error shape">{errorShape}</CodeBlock>}
    >
      <p>
        <code>code</code> is machine-readable and safe to switch on. <code>message</code> is for
        logs and support tickets. Some errors also include a <code>param</code> naming the field
        they relate to.
      </p>

      <table>
        <thead>
          <tr>
            <th>Code</th>
            <th>HTTP</th>
            <th>Meaning</th>
          </tr>
        </thead>
        <tbody>
          {errors.map(([code, http, meaning]) => (
            <tr key={code}>
              <td>{code}</td>
              <td>{http}</td>
              <td>{meaning}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </DocsPage>
  )
}
