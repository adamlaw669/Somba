import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { FaBars } from 'react-icons/fa6'
import SiteNav from '../components/SiteNav'
import Sidebar from '../components/Sidebar'

export default function DocsLayout() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  return (
    <div className="flex min-h-screen flex-col">
      <SiteNav />

      <button
        type="button"
        onClick={() => setMobileNavOpen(true)}
        className="flex items-center gap-2 border-b border-line px-6 py-3 font-mono text-[13px] text-text-muted md:hidden"
      >
        <FaBars className="text-[12px]" />
        Menu
      </button>

      <div className="mx-auto flex w-full max-w-[1400px] flex-1 items-start px-6">
        <Sidebar open={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />
        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
