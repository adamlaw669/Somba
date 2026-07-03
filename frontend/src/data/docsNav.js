export const docsNav = [
  {
    heading: 'Getting started',
    items: [
      { title: 'Introduction', path: '/docs/introduction' },
      { title: 'Authentication', path: '/docs/authentication' },
      { title: 'Your first request', path: '/docs/first-request' },
      { title: 'Idempotency', path: '/docs/idempotency' },
      { title: 'Errors', path: '/docs/errors' },
    ],
  },
  {
    heading: 'Core concepts',
    items: [
      { title: 'Plans', path: '/docs/plans' },
      { title: 'Customers', path: '/docs/customers' },
      { title: 'Subscriptions', path: '/docs/subscriptions' },
      { title: 'The subscription lifecycle', path: '/docs/lifecycle' },
      { title: 'Invoices', path: '/docs/invoices' },
      { title: 'Events & webhooks', path: '/docs/events-webhooks' },
    ],
  },
  {
    heading: 'Guides',
    items: [
      { title: 'Set up recurring billing', path: '/docs/guides/recurring-billing' },
      { title: 'Handle failed payments', path: '/docs/guides/failed-payments' },
      { title: 'Understand recovery', path: '/docs/guides/recovery' },
      { title: 'Plan changes & proration', path: '/docs/guides/proration' },
      { title: 'Verify webhooks', path: '/docs/guides/verify-webhooks' },
    ],
  },
  {
    heading: 'API reference',
    items: [
      { title: 'Plans', path: '/docs/api/plans' },
      { title: 'Customers', path: '/docs/api/customers' },
      { title: 'Subscriptions', path: '/docs/api/subscriptions' },
      { title: 'Invoices', path: '/docs/api/invoices' },
      { title: 'Events', path: '/docs/api/events' },
      { title: 'Webhooks (inbound)', path: '/docs/api/webhooks' },
    ],
  },
  {
    heading: 'Resources',
    items: [
      { title: 'Changelog', path: '/docs/changelog' },
      { title: 'Status', path: '/docs/status' },
    ],
  },
]

export const flatDocsNav = docsNav.flatMap((group) => group.items)

export function adjacentDocs(path) {
  const idx = flatDocsNav.findIndex((item) => item.path === path)
  return {
    prev: idx > 0 ? flatDocsNav[idx - 1] : null,
    next: idx >= 0 && idx < flatDocsNav.length - 1 ? flatDocsNav[idx + 1] : null,
  }
}
