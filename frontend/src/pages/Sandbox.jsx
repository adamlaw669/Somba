import { useState } from 'react'
import SiteNav from '../components/SiteNav'
import CodeBlock from '../components/CodeBlock'
import StatusPill from '../components/StatusPill'
import { sandboxCheckAuth, sandboxCreateVirtualAccount } from '../lib/api'

function ResultBlock({ result, error }) {
  if (error) {
    return (
      <p className="rounded-sm border border-error/40 bg-error-dim/30 px-3 py-2 text-[13px] text-error">
        {error}
      </p>
    )
  }
  if (result) {
    return <CodeBlock title="Response">{JSON.stringify(result, null, 2)}</CodeBlock>
  }
  return null
}

async function hmacSha256Hex(secret, payload) {
  const enc = new TextEncoder()
  const key = await crypto.subtle.importKey(
    'raw',
    enc.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  )
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(payload))
  return Array.from(new Uint8Array(sig))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

export default function Sandbox() {
  const [apiKey, setApiKey] = useState('')
  const [customerName, setCustomerName] = useState('Sandbox Test Customer')

  const [authStatus, setAuthStatus] = useState('idle')
  const [authResult, setAuthResult] = useState(null)
  const [authError, setAuthError] = useState(null)

  const [vaStatus, setVaStatus] = useState('idle')
  const [vaResult, setVaResult] = useState(null)
  const [vaError, setVaError] = useState(null)

  const [whPayload, setWhPayload] = useState('{"type":"charge.succeeded","data":{"subscription_id":"sub_xxx"}}')
  const [whSecret, setWhSecret] = useState('')
  const [whSignature, setWhSignature] = useState('')
  const [whResult, setWhResult] = useState(null)

  async function onCheckAuth() {
    setAuthStatus('loading')
    setAuthError(null)
    setAuthResult(null)
    try {
      const data = await sandboxCheckAuth(apiKey.trim())
      setAuthResult(data)
    } catch (err) {
      setAuthError(err.message)
    } finally {
      setAuthStatus('idle')
    }
  }

  async function onCreateVa() {
    setVaStatus('loading')
    setVaError(null)
    setVaResult(null)
    try {
      const data = await sandboxCreateVirtualAccount(apiKey.trim(), customerName.trim())
      setVaResult(data)
    } catch (err) {
      setVaError(err.message)
    } finally {
      setVaStatus('idle')
    }
  }

  async function onVerifyWebhook() {
    const expected = await hmacSha256Hex(whSecret, whPayload)
    const matches = expected === whSignature.trim().toLowerCase()
    setWhResult({ expected, matches })
  }

  return (
    <div className="flex min-h-screen flex-col">
      <SiteNav />

      <main className="flex flex-1 justify-center px-6 py-16">
        <div className="w-full max-w-[640px]">
          <div className="mb-2 font-mono text-[12px] uppercase tracking-wider text-text-faint">
            Sandbox
          </div>
          <h1 className="mb-2 font-mono text-[26px] font-medium tracking-tight text-text">
            Test the Nomba integration
          </h1>
          <p className="mb-8 text-[14px] leading-6 text-text-muted">
            These calls always use dedicated sandbox credentials against{' '}
            <code className="font-mono text-settled">sandbox.nomba.com</code>, regardless of
            whether your account is holding live keys. Nothing here ever touches real money.
          </p>

          <label className="mb-10 flex flex-col gap-1.5">
            <span className="font-mono text-[12px] text-text-muted">Your API key</span>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-somba-..."
              className="rounded-sm border border-line bg-panel px-3 py-2 font-mono text-[13px] text-text outline-none focus-visible:border-settled"
            />
          </label>

          <div className="mb-6 flex flex-col gap-4 rounded-sm border border-line bg-panel/40 p-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-[15px] font-medium text-text">Auth check</h2>
                <p className="text-[13px] text-text-muted">
                  Confirms the sandbox credentials can issue a token.
                </p>
              </div>
              <StatusPill kind={authResult ? 'settled' : authError ? 'error' : 'neutral'}>
                {authResult ? 'ok' : authError ? 'failed' : 'untested'}
              </StatusPill>
            </div>
            <button
              type="button"
              onClick={onCheckAuth}
              disabled={!apiKey || authStatus === 'loading'}
              className="w-fit rounded-full bg-settled px-4 py-2 font-mono text-[13px] font-medium text-ink transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {authStatus === 'loading' ? 'Checking…' : 'Test auth'}
            </button>
            <ResultBlock result={authResult} error={authError} />
          </div>

          <div className="mb-6 flex flex-col gap-4 rounded-sm border border-line bg-panel/40 p-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-[15px] font-medium text-text">Virtual account</h2>
                <p className="text-[13px] text-text-muted">
                  Creates a throwaway sandbox virtual account end-to-end.
                </p>
              </div>
              <StatusPill kind={vaResult ? 'settled' : vaError ? 'error' : 'neutral'}>
                {vaResult ? 'ok' : vaError ? 'failed' : 'untested'}
              </StatusPill>
            </div>

            <p className="rounded-sm border border-pending/40 bg-pending-dim/20 px-3 py-2 text-[12px] leading-5 text-text-muted">
              Nomba caps sandbox accounts at 2 virtual accounts total per account holder — once
              that&rsquo;s used up, this will fail with a real Nomba error even though nothing is
              broken. That&rsquo;s expected, not a bug.
            </p>

            <label className="flex flex-col gap-1.5">
              <span className="font-mono text-[12px] text-text-muted">Customer name</span>
              <input
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                className="rounded-sm border border-line bg-panel px-3 py-2 text-[14px] text-text outline-none focus-visible:border-settled"
              />
            </label>

            <button
              type="button"
              onClick={onCreateVa}
              disabled={!apiKey || !customerName || vaStatus === 'loading'}
              className="w-fit rounded-full bg-settled px-4 py-2 font-mono text-[13px] font-medium text-ink transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {vaStatus === 'loading' ? 'Creating…' : 'Create test virtual account'}
            </button>
            <ResultBlock result={vaResult} error={vaError} />
          </div>

          <div className="flex flex-col gap-4 rounded-sm border border-line bg-panel/40 p-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-[15px] font-medium text-text">Webhook signature</h2>
                <p className="text-[13px] text-text-muted">
                  Checks a payload + secret against a signature entirely in your browser — no
                  Nomba call, no quota.
                </p>
              </div>
              {whResult && (
                <StatusPill kind={whResult.matches ? 'settled' : 'error'}>
                  {whResult.matches ? 'matches' : "doesn't match"}
                </StatusPill>
              )}
            </div>

            <label className="flex flex-col gap-1.5">
              <span className="font-mono text-[12px] text-text-muted">Payload (raw body)</span>
              <textarea
                value={whPayload}
                onChange={(e) => setWhPayload(e.target.value)}
                rows={3}
                className="rounded-sm border border-line bg-panel px-3 py-2 font-mono text-[12px] text-text outline-none focus-visible:border-settled"
              />
            </label>
            <label className="flex flex-col gap-1.5">
              <span className="font-mono text-[12px] text-text-muted">Webhook secret</span>
              <input
                type="password"
                value={whSecret}
                onChange={(e) => setWhSecret(e.target.value)}
                className="rounded-sm border border-line bg-panel px-3 py-2 font-mono text-[13px] text-text outline-none focus-visible:border-settled"
              />
            </label>
            <label className="flex flex-col gap-1.5">
              <span className="font-mono text-[12px] text-text-muted">Signature to check</span>
              <input
                value={whSignature}
                onChange={(e) => setWhSignature(e.target.value)}
                placeholder="hex digest from X-Somba-Signature"
                className="rounded-sm border border-line bg-panel px-3 py-2 font-mono text-[13px] text-text outline-none focus-visible:border-settled"
              />
            </label>

            <button
              type="button"
              onClick={onVerifyWebhook}
              disabled={!whPayload || !whSecret}
              className="w-fit rounded-full bg-settled px-4 py-2 font-mono text-[13px] font-medium text-ink transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              Verify signature
            </button>

            {whResult && (
              <CodeBlock title="Computed HMAC-SHA256">{whResult.expected}</CodeBlock>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
