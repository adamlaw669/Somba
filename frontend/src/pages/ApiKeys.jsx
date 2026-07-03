import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import SiteNav from '../components/SiteNav'
import CodeBlock from '../components/CodeBlock'
import {
  listApiKeys,
  createApiKey,
  revokeApiKey,
  getSessionToken,
  clearSessionToken,
} from '../lib/api'

export default function ApiKeys() {
  const navigate = useNavigate()
  const [keys, setKeys] = useState(null)
  const [name, setName] = useState('')
  const [creating, setCreating] = useState(false)
  const [revealedKey, setRevealedKey] = useState(null)
  const [error, setError] = useState(null)

  function load() {
    const token = getSessionToken()
    if (!token) {
      navigate('/login')
      return
    }
    listApiKeys(token)
      .then((data) => setKeys(data.api_keys))
      .catch(() => {
        clearSessionToken()
        navigate('/login')
      })
  }

  useEffect(load, [navigate])

  async function onCreate(e) {
    e.preventDefault()
    setError(null)
    setCreating(true)
    try {
      const data = await createApiKey(getSessionToken(), name)
      setRevealedKey(data.api_key)
      setName('')
      load()
    } catch (err) {
      setError(err.message)
    } finally {
      setCreating(false)
    }
  }

  async function onRevoke(id) {
    setError(null)
    try {
      await revokeApiKey(getSessionToken(), id)
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <SiteNav />

      <main className="flex flex-1 justify-center px-6 py-16">
        <div className="w-full max-w-[760px]">
          <div className="mb-2 font-mono text-[12px] uppercase tracking-wider text-text-faint">
            Account
          </div>
          <h1 className="mb-2 font-mono text-[26px] font-medium tracking-tight text-text">
            API keys
          </h1>
          <p className="mb-8 text-[14px] leading-6 text-text-muted">
            Keys you mint here are what your own code uses to call the Somba API. Name them by
            what they&rsquo;re for &mdash; production, local development, a specific integration &mdash;
            so revoking one is never a guess.
          </p>

          {revealedKey && (
            <div className="mb-8 flex flex-col gap-4">
              <p className="rounded-sm border border-pending/40 bg-pending-dim/30 px-3 py-2 text-[13px] text-pending">
                Copy your API key now — it will never be shown again.
              </p>
              <CodeBlock title="Your API key">{revealedKey}</CodeBlock>
            </div>
          )}

          <form onSubmit={onCreate} className="mb-10 flex items-end gap-3">
            <label className="flex flex-1 flex-col gap-1.5">
              <span className="font-mono text-[12px] text-text-muted">New key name</span>
              <input
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Production"
                className="rounded-sm border border-line bg-panel px-3 py-2 text-[14px] text-text outline-none focus-visible:border-settled"
              />
            </label>
            <button
              type="submit"
              disabled={creating}
              className="rounded-sm bg-settled px-4 py-2 font-mono text-[13px] font-medium text-ink transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {creating ? 'Creating…' : 'Create key'}
            </button>
          </form>

          {error && (
            <p className="mb-6 rounded-sm border border-error/40 bg-error-dim/30 px-3 py-2 text-[13px] text-error">
              {error}
            </p>
          )}

          {keys === null && (
            <p className="text-[13px] text-text-muted">Loading your keys…</p>
          )}

          {keys?.length === 0 && (
            <p className="rounded-sm border border-line bg-panel px-4 py-6 text-center text-[13px] text-text-muted">
              No keys yet. Create one above to use in your code.
            </p>
          )}

          {keys?.length > 0 && (
            <div className="overflow-hidden rounded-sm border border-line">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-line bg-panel">
                    <th className="px-4 py-2.5 font-mono text-[11px] uppercase tracking-wider text-text-faint">
                      Name
                    </th>
                    <th className="px-4 py-2.5 font-mono text-[11px] uppercase tracking-wider text-text-faint">
                      Key
                    </th>
                    <th className="px-4 py-2.5 font-mono text-[11px] uppercase tracking-wider text-text-faint">
                      Created
                    </th>
                    <th className="px-4 py-2.5 font-mono text-[11px] uppercase tracking-wider text-text-faint">
                      Last used
                    </th>
                    <th className="px-4 py-2.5" />
                  </tr>
                </thead>
                <tbody>
                  {keys.map((k) => (
                    <tr key={k.id} className="border-b border-line-soft last:border-b-0">
                      <td className="px-4 py-3 text-[13px] text-text">{k.name}</td>
                      <td className="px-4 py-3 font-mono text-[12px] text-text-muted">
                        sk-somba-{k.key_id}…
                      </td>
                      <td className="px-4 py-3 font-mono text-[12px] text-text-muted">
                        {new Date(k.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 font-mono text-[12px] text-text-muted">
                        {k.last_used_at
                          ? new Date(k.last_used_at).toLocaleDateString()
                          : 'never'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          type="button"
                          onClick={() => onRevoke(k.id)}
                          className="font-mono text-[12px] text-text-faint transition-colors hover:text-error"
                        >
                          revoke
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
