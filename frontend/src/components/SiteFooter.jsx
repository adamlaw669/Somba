import { Link } from 'react-router-dom'
import { FaGithub } from 'react-icons/fa6'

const columns = [
  {
    heading: 'Product',
    links: [
      { label: 'Introduction', to: '/docs/introduction' },
      { label: 'API reference', to: '/docs/api/plans' },
      { label: 'Guides', to: '/docs/guides/recurring-billing' },
    ],
  },
  {
    heading: 'Core concepts',
    links: [
      { label: 'Plans', to: '/docs/plans' },
      { label: 'Subscriptions', to: '/docs/subscriptions' },
      { label: 'Events & webhooks', to: '/docs/events-webhooks' },
    ],
  },
  {
    heading: 'Resources',
    links: [
      { label: 'Changelog', to: '/docs/changelog' },
      { label: 'Status', to: '/docs/status' },
      { label: 'Errors', to: '/docs/errors' },
    ],
  },
  {
    heading: 'Account',
    links: [
      { label: 'Get API key', to: '/signup' },
      { label: 'Log in', to: '/login' },
    ],
  },
]

export default function SiteFooter() {
  return (
    <footer className="border-t border-line">
      <div className="mx-auto max-w-[1400px] px-6 py-16">
        <div className="grid grid-cols-2 gap-x-8 gap-y-12 sm:grid-cols-[1.3fr_1fr_1fr_1fr_1fr]">
          <div className="col-span-2 flex flex-col gap-4 sm:col-span-1">
            <div className="flex items-center gap-2 font-mono text-[15px] text-text">
              <span className="inline-block h-2 w-2 rounded-full bg-settled" />
              somba
            </div>
            <p className="max-w-[26ch] text-[13px] leading-6 text-text-muted">
              Managed recurring billing for Nomba merchants — billing, recovery, and
              reconciliation, handled.
            </p>
            <a
              href="https://github.com/adamlaw669/Somba/"
              target="_blank"
              rel="noreferrer"
              className="mt-1 flex w-fit items-center gap-2 rounded-full border border-line px-3.5 py-1.5 font-mono text-[12px] text-text-muted transition-colors hover:border-settled hover:text-settled"
            >
              <FaGithub className="text-[13px]" />
              Watch on GitHub
            </a>
          </div>

          {columns.map((col) => (
            <div key={col.heading} className="flex flex-col gap-3">
              <div className="font-mono text-[11px] uppercase tracking-wider text-text-faint">
                {col.heading}
              </div>
              <ul className="flex flex-col gap-2 font-mono text-[13px] text-text-muted">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <Link to={link.to} className="transition-colors hover:text-text">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-14 flex flex-col gap-3 border-t border-line pt-6 font-mono text-[12px] text-text-faint sm:flex-row sm:items-center sm:justify-between">
          <span>Nomba × DevCareer Hackathon 2026.</span>
          <span>Built on Nomba&rsquo;s payment rails.</span>
        </div>
      </div>
    </footer>
  )
}
