import { Routes, Route, Navigate } from 'react-router-dom'
import Landing from './pages/Landing'
import Signup from './pages/Signup'
import Login from './pages/Login'
import ApiKeys from './pages/ApiKeys'
import Sandbox from './pages/Sandbox'
import DocsLayout from './layouts/DocsLayout'

import Introduction from './pages/docs/Introduction'
import Authentication from './pages/docs/Authentication'
import FirstRequest from './pages/docs/FirstRequest'
import Idempotency from './pages/docs/Idempotency'
import Errors from './pages/docs/Errors'

import Plans from './pages/docs/Plans'
import Customers from './pages/docs/Customers'
import Subscriptions from './pages/docs/Subscriptions'
import Lifecycle from './pages/docs/Lifecycle'
import Invoices from './pages/docs/Invoices'
import EventsWebhooks from './pages/docs/EventsWebhooks'

import RecurringBilling from './pages/docs/guides/RecurringBilling'
import FailedPayments from './pages/docs/guides/FailedPayments'
import Recovery from './pages/docs/guides/Recovery'
import Proration from './pages/docs/guides/Proration'
import VerifyWebhooks from './pages/docs/guides/VerifyWebhooks'

import ApiPlans from './pages/docs/api/ApiPlans'
import ApiCustomers from './pages/docs/api/ApiCustomers'
import ApiSubscriptions from './pages/docs/api/ApiSubscriptions'
import ApiInvoices from './pages/docs/api/ApiInvoices'
import ApiEvents from './pages/docs/api/ApiEvents'
import ApiWebhooks from './pages/docs/api/ApiWebhooks'

import Changelog from './pages/docs/Changelog'
import Status from './pages/docs/Status'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/login" element={<Login />} />
      <Route path="/api-keys" element={<ApiKeys />} />
      <Route path="/sandbox" element={<Sandbox />} />

      <Route path="/docs" element={<DocsLayout />}>
        <Route index element={<Navigate to="/docs/introduction" replace />} />

        <Route path="introduction" element={<Introduction />} />
        <Route path="authentication" element={<Authentication />} />
        <Route path="first-request" element={<FirstRequest />} />
        <Route path="idempotency" element={<Idempotency />} />
        <Route path="errors" element={<Errors />} />

        <Route path="plans" element={<Plans />} />
        <Route path="customers" element={<Customers />} />
        <Route path="subscriptions" element={<Subscriptions />} />
        <Route path="lifecycle" element={<Lifecycle />} />
        <Route path="invoices" element={<Invoices />} />
        <Route path="events-webhooks" element={<EventsWebhooks />} />

        <Route path="guides/recurring-billing" element={<RecurringBilling />} />
        <Route path="guides/failed-payments" element={<FailedPayments />} />
        <Route path="guides/recovery" element={<Recovery />} />
        <Route path="guides/proration" element={<Proration />} />
        <Route path="guides/verify-webhooks" element={<VerifyWebhooks />} />

        <Route path="api/plans" element={<ApiPlans />} />
        <Route path="api/customers" element={<ApiCustomers />} />
        <Route path="api/subscriptions" element={<ApiSubscriptions />} />
        <Route path="api/invoices" element={<ApiInvoices />} />
        <Route path="api/events" element={<ApiEvents />} />
        <Route path="api/webhooks" element={<ApiWebhooks />} />

        <Route path="changelog" element={<Changelog />} />
        <Route path="status" element={<Status />} />

        <Route path="*" element={<Navigate to="/docs/introduction" replace />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
