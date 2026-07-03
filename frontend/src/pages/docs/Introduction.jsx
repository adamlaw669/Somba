import { Link } from 'react-router-dom'
import DocsPage from '../../components/DocsPage'

export default function Introduction() {
  return (
    <DocsPage
      eyebrow="Getting started"
      title="Introduction"
      path="/docs/introduction"
      description="Somba is managed recurring billing for Nomba merchants. It bills customers on a schedule, recovers failed payments, and keeps a ledger you can reconcile against."
    >
      <p>
        Somba sits between your product and Nomba&rsquo;s payment rails. You tell it what plan a
        customer is on and when the next bill should happen. Somba tracks the subscription
        lifecycle, creates invoices, schedules charges, retries or reroutes failed payments, and
        records what happened so it can be audited later.
      </p>

      <p>
        To use Somba you need a Nomba merchant account and a Somba API key. Every request is
        scoped to your merchant &mdash; you will never see another merchant&rsquo;s customers, plans,
        or invoices, and they will never see yours.
      </p>

      <p>
        In return you get a plans and subscriptions API, an invoice record for every billing
        period, webhooks for every state change, and a recovery engine that handles failed
        payments without you writing retry logic. Start with{' '}
        <Link to="/docs/authentication" className="text-settled hover:underline">
          authentication
        </Link>
        , then walk through{' '}
        <Link to="/docs/first-request" className="text-settled hover:underline">
          your first request
        </Link>
        .
      </p>
    </DocsPage>
  )
}
