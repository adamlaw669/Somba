import { Link } from 'react-router-dom'
import { FaArrowRotateRight, FaCalendarDays, FaGithub, FaScaleBalanced } from 'react-icons/fa6'
import SiteNav from '../components/SiteNav'
import SiteFooter from '../components/SiteFooter'
import CodeBlock from '../components/CodeBlock'
import LedgerStrip from '../components/LedgerStrip'
import AmbientBackground from '../components/AmbientBackground'
import Eyebrow from '../components/Eyebrow'

const glass =
  'rounded-2xl border border-line/70 bg-panel/50 backdrop-blur-md shadow-[inset_0_1px_0_0_rgba(237,239,234,0.06),0_30px_60px_-20px_rgba(0,0,0,0.75)]'

const features = [
  {
    icon: FaCalendarDays,
    title: 'Bills on schedule',
    body: 'Define a plan. Subscribe a customer. Somba handles the rest automatically.',
  },
  {
    icon: FaArrowRotateRight,
    title: 'Recovers failures',
    body: 'Classifies every failed charge and routes it to the right recovery path automatically.',
  },
  {
    icon: FaScaleBalanced,
    title: 'Proves every naira',
    body: 'Full ledger of intents and settlements. Every charge accounted for.',
  },
]

const steps = [
  {
    n: '01',
    title: 'Get your API key',
    body: 'Create an account. Mint a key from your dashboard, shown once.',
  },
  {
    n: '02',
    title: 'Create a plan and subscribe a customer',
    body: 'POST /v1/plans then POST /v1/subscriptions. Somba starts billing on the cycle you set.',
  },
  {
    n: '03',
    title: 'Listen to webhooks',
    body: 'Somba signs every event with your webhook secret. React to charge.succeeded, charge.failed, subscription.past_due, and more.',
  },
]

const curlExample = `curl -X POST https://somba.ddns.net/v1/subscriptions \\
  -H "Authorization: Bearer sk-somba-<key_id>.<secret>" \\
  -H "Idempotency-Key: sub-kemi-001" \\
  -H "Content-Type: application/json" \\
  -d '{
    "customer_id": "cus_xxx",
    "plan_id": "plan_xxx"
  }'`

const webhookExample = `{
  "type": "charge.succeeded",
  "data": {
    "subscription_id": "sub_xxx",
    "amount": 1500000
  }
}`

const recoveredExample = `{
  "type": "charge.recovered",
  "data": {
    "subscription_id": "sub_xxx",
    "recovery_path": "timing"
  }
}`

const recoveryPaths = [
  ['empty_account', 'Retry later, when funds are more likely present'],
  ['broken_card', 'Stop pulling, switch to transfer fallback'],
  ['transient', 'Retry once, then decide'],
  ['risk', 'Stop — do not keep pushing'],
]

export default function Landing() {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteNav />

      <main className="flex-1">
        <section className="relative overflow-hidden">
          <AmbientBackground />

          <div className="relative mx-auto max-w-[900px] px-6 pb-16 pt-20 text-center lg:pt-28">
            <Eyebrow>Nomba × DevCareer Hackathon 2026</Eyebrow>

            <h1 className="mx-auto max-w-[20ch] bg-gradient-to-b from-text to-text-muted bg-clip-text font-mono text-[38px] font-medium leading-[1.15] tracking-tight text-transparent sm:text-[52px]">
              Recurring billing infrastructure for Nomba merchants.
            </h1>

            <p className="mx-auto mt-6 max-w-[46ch] text-[16px] leading-7 text-text-muted">
              Add subscriptions to your product in an afternoon. Somba handles the billing,
              recovery, and reconciliation. You handle your product.
            </p>

            <div className="mt-8 flex items-center justify-center gap-4">
              <Link
                to="/docs/introduction"
                className="rounded-full bg-settled px-5 py-2.5 font-mono text-[13px] font-medium text-ink transition-opacity hover:opacity-90"
              >
                Read the docs
              </Link>
              <a
                href="https://github.com/adamlaw669/Somba/"
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 rounded-full border border-line px-5 py-2.5 font-mono text-[13px] text-text transition-colors hover:border-settled hover:text-settled"
              >
                <FaGithub className="text-[14px]" />
                View on GitHub
              </a>
            </div>
          </div>

          <div className="relative mx-auto flex max-w-[1100px] flex-col items-center gap-6 px-6 pb-24 pt-6 lg:flex-row lg:items-start lg:justify-center lg:gap-0">
            <div
              className={`${glass} w-full max-w-[300px] rotate-0 p-4 lg:-mr-6 lg:mt-10 lg:w-[280px] lg:-rotate-3`}
            >
              <LedgerStrip />
            </div>
            <div className={`${glass} z-10 w-full max-w-[460px] p-4 lg:w-[460px] lg:scale-105`}>
              <CodeBlock title="Create a subscription">{curlExample}</CodeBlock>
            </div>
            <div
              className={`${glass} w-full max-w-[300px] rotate-0 p-4 lg:-ml-6 lg:mt-10 lg:w-[280px] lg:rotate-3`}
            >
              <CodeBlock title="Webhook received">{webhookExample}</CodeBlock>
            </div>
          </div>
        </section>

        <section className="border-t border-line py-20">
          <div className="mx-auto max-w-[1100px] px-6">
            <Eyebrow>What it does</Eyebrow>

            <div className="flex flex-col items-center gap-0 sm:flex-row sm:items-start sm:justify-center sm:gap-4">
              {features.map((feature, i) => (
                <div key={feature.title} className="flex items-center sm:items-start">
                  <div className="flex w-[220px] flex-col items-center text-center">
                    <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full border border-line bg-panel text-settled">
                      <feature.icon className="text-[20px]" />
                    </div>
                    <h2 className="mb-2 text-[15px] font-medium text-text">{feature.title}</h2>
                    <p className="text-[13px] leading-6 text-text-muted">{feature.body}</p>
                  </div>
                  {i < features.length - 1 && (
                    <span className="mt-7 hidden h-px w-12 shrink-0 bg-gradient-to-r from-line to-line sm:block" />
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="border-t border-line py-20">
          <div className="mx-auto max-w-[1100px] px-6">
            <Eyebrow>Integration</Eyebrow>
            <h2 className="mb-12 text-center text-[24px] font-medium tracking-tight text-text">
              Three steps to your first charge
            </h2>
            <div className="grid gap-10 sm:grid-cols-3">
              {steps.map((step) => (
                <div key={step.n}>
                  <div className="mb-3 font-mono text-[13px] text-settled">{step.n}</div>
                  <h3 className="mb-2 text-[15px] font-medium text-text">{step.title}</h3>
                  <p className="text-[14px] leading-6 text-text-muted">{step.body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="border-t border-line py-20">
          <div className="mx-auto max-w-[1100px] px-6">
            <Eyebrow>Recovery</Eyebrow>
            <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
              <div>
                <h2 className="mb-4 text-[24px] font-medium tracking-tight text-text">
                  A failed charge isn&rsquo;t a final answer.
                </h2>
                <p className="mb-6 text-[14px] leading-6 text-text-muted">
                  Somba classifies every failure and picks the next step itself &mdash; retry at a
                  better time, switch to transfer fallback, or stop if the payment looks unsafe.
                  You just listen for the webhook.
                </p>
                <div className="flex flex-col gap-2">
                  {recoveryPaths.map(([code, meaning]) => (
                    <div
                      key={code}
                      className="flex items-center gap-3 rounded-sm border border-line-soft bg-panel/40 px-3 py-2"
                    >
                      <code className="font-mono text-[12px] text-settled">{code}</code>
                      <span className="text-[12px] text-text-muted">{meaning}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className={`${glass} p-4`}>
                <CodeBlock title="charge.recovered webhook">{recoveredExample}</CodeBlock>
              </div>
            </div>
          </div>
        </section>

        <section className="border-t border-line py-20 text-center">
          <div className="mx-auto max-w-[640px] px-6">
            <Eyebrow>Get started</Eyebrow>
            <h2 className="mb-4 text-[24px] font-medium tracking-tight text-text">
              Add billing to your product this afternoon.
            </h2>
            <p className="mb-8 text-[14px] leading-6 text-text-muted">
              Create an account, mint a key, and make your first request. No sales call required.
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link
                to="/signup"
                className="rounded-full bg-settled px-5 py-2.5 font-mono text-[13px] font-medium text-ink transition-opacity hover:opacity-90"
              >
                Create an account
              </Link>
              <Link
                to="/docs/introduction"
                className="rounded-full border border-line px-5 py-2.5 font-mono text-[13px] text-text transition-colors hover:border-settled hover:text-settled"
              >
                Read the docs
              </Link>
            </div>
          </div>
        </section>

      </main>

      <SiteFooter />
    </div>
  )
}
