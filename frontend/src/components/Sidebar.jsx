import { NavLink } from 'react-router-dom'
import { docsNav } from '../data/docsNav'

export default function Sidebar({ open = false, onClose }) {
  return (
    <>
      {open && (
        <div className="fixed inset-0 z-40 bg-ink/70 md:hidden" onClick={onClose} />
      )}

      <aside
        className={`fixed left-0 top-14 z-50 h-[calc(100vh-3.5rem)] w-72 -translate-x-full bg-ink transition-transform duration-200 ease-out md:sticky md:top-20 md:z-0 md:h-[calc(100vh-5.5rem)] md:w-60 md:shrink-0 md:translate-x-0 md:bg-transparent md:py-6 md:transition-none ${
          open ? 'translate-x-0' : ''
        }`}
      >
        <nav className="h-full overflow-y-auto border-r border-line bg-panel/95 p-4 md:rounded-sm md:border md:bg-panel/40">
          {docsNav.map((group) => (
            <div key={group.heading} className="mb-6 last:mb-0">
              <div className="mb-2 font-mono text-[11px] uppercase tracking-wider text-text-faint">
                {group.heading}
              </div>
              <ul className="flex flex-col gap-0.5">
                {group.items.map((item) => (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      onClick={onClose}
                      className={({ isActive }) =>
                        `block rounded-sm px-2 py-1 text-[13px] transition-colors ${
                          isActive ? 'bg-panel text-settled' : 'text-text-muted hover:text-text'
                        }`
                      }
                    >
                      {item.title}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
      </aside>
    </>
  )
}
