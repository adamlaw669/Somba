import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { fetchDashboardMe, getSessionToken, clearSessionToken } from '../lib/api'

export default function ProfileMenu() {
  const navigate = useNavigate()
  const [merchant, setMerchant] = useState(null)
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const token = getSessionToken()
    if (!token) return
    fetchDashboardMe(token)
      .then((data) => setMerchant(data.merchant))
      .catch(() => clearSessionToken())
  }, [])

  useEffect(() => {
    function onClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  if (!merchant) return null

  function onLogout() {
    clearSessionToken()
    setOpen(false)
    navigate('/')
  }

  const initial = merchant.name?.[0]?.toUpperCase() || '?'

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex h-8 w-8 items-center justify-center rounded-full border border-line bg-panel font-mono text-[13px] text-text transition-colors hover:border-settled"
      >
        {initial}
      </button>

      {open && (
        <div className="absolute right-0 top-11 w-56 overflow-hidden rounded-sm border border-line bg-panel">
          <div className="truncate border-b border-line px-4 py-3 font-mono text-[12px] text-text-muted">
            {merchant.email}
          </div>
          <Link
            to="/api-keys"
            onClick={() => setOpen(false)}
            className="block px-4 py-2.5 font-mono text-[13px] text-text transition-colors hover:bg-panel-2"
          >
            API keys
          </Link>
          <button
            type="button"
            onClick={onLogout}
            className="block w-full px-4 py-2.5 text-left font-mono text-[13px] text-text-muted transition-colors hover:bg-panel-2 hover:text-error"
          >
            Log out
          </button>
        </div>
      )}
    </div>
  )
}
