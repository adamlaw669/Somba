import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { FaBook, FaCode, FaGithub, FaKey } from 'react-icons/fa6'
import ProfileMenu from './ProfileMenu'
import { getSessionToken } from '../lib/api'

const navLinkClass = ({ isActive }) =>
  `flex items-center gap-1.5 text-sm transition-colors ${
    isActive ? 'text-text' : 'text-text-muted hover:text-text'
  }`

export default function SiteNav() {
  const [signedIn] = useState(() => Boolean(getSessionToken()))

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-ink/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-[1400px] items-center justify-between px-6">
        <Link
          to="/"
          className="flex items-center gap-2 font-mono text-[15px] font-medium tracking-tight text-text"
        >
          <span className="inline-block h-2 w-2 rounded-full bg-settled" />
          somba
        </Link>

        <nav className="hidden items-center gap-7 md:flex">
          <NavLink to="/docs/introduction" className={navLinkClass}>
            <FaBook className="text-[13px]" />
            Docs
          </NavLink>
          <NavLink to="/docs/api/plans" className={navLinkClass}>
            <FaCode className="text-[13px]" />
            API reference
          </NavLink>
          <a
            href="https://github.com/adamlaw669/Somba/"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 text-sm text-text-muted transition-colors hover:text-text"
          >
            <FaGithub className="text-[14px]" />
            GitHub
          </a>
        </nav>

        {signedIn ? (
          <ProfileMenu />
        ) : (
          <div className="flex items-center gap-4">
            <Link
              to="/login"
              className="hidden text-sm text-text-muted transition-colors hover:text-text sm:inline"
            >
              Log in
            </Link>
            <Link
              to="/signup"
              className="flex items-center gap-2 rounded-full border border-line bg-panel px-4 py-1.5 font-mono text-[13px] text-text transition-colors hover:border-settled hover:text-settled"
            >
              <FaKey className="text-[11px]" />
              Get API key
            </Link>
          </div>
        )}
      </div>
    </header>
  )
}
