import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import SiteNav from '../components/SiteNav'
import { login, setSessionToken } from '../lib/api'

export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState(null)

  async function onSubmit(e) {
    e.preventDefault()
    setStatus('loading')
    setError(null)
    try {
      const data = await login({ email, password })
      setSessionToken(data.session_token)
      navigate('/docs/introduction')
    } catch (err) {
      setError(err.message)
      setStatus('idle')
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <SiteNav />

      <main className="flex flex-1 items-start justify-center px-6 py-16">
        <div className="w-full max-w-[440px]">
          <div className="mb-2 font-mono text-[12px] uppercase tracking-wider text-text-faint">
            Getting started
          </div>
          <h1 className="mb-3 font-mono text-[26px] font-medium tracking-tight text-text">
            Log in
          </h1>
          <p className="mb-8 text-[14px] leading-6 text-text-muted">
            Get back into your dashboard to view or mint your API key.
          </p>

          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <label className="flex flex-col gap-1.5">
              <span className="font-mono text-[12px] text-text-muted">Email</span>
              <input
                required
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="kemi@example.com"
                className="rounded-sm border border-line bg-panel px-3 py-2 text-[14px] text-text outline-none focus-visible:border-settled"
              />
            </label>

            <label className="flex flex-col gap-1.5">
              <span className="font-mono text-[12px] text-text-muted">Password</span>
              <input
                required
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="rounded-sm border border-line bg-panel px-3 py-2 text-[14px] text-text outline-none focus-visible:border-settled"
              />
            </label>

            {error && (
              <p className="rounded-sm border border-error/40 bg-error-dim/30 px-3 py-2 text-[13px] text-error">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={status === 'loading'}
              className="mt-2 rounded-sm bg-settled px-4 py-2 font-mono text-[13px] font-medium text-ink transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {status === 'loading' ? 'Logging in…' : 'Log in'}
            </button>

            <p className="text-[13px] text-text-muted">
              Don&rsquo;t have an account?{' '}
              <Link to="/signup" className="text-settled hover:underline">
                Create one
              </Link>
            </p>
          </form>
        </div>
      </main>
    </div>
  )
}
