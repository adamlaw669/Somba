export default function Eyebrow({ children }) {
  return (
    <div className="mb-6 flex items-center justify-center gap-4">
      <span className="h-px w-10 bg-gradient-to-r from-transparent to-line sm:w-20" />
      <span className="whitespace-nowrap font-mono text-[11px] uppercase tracking-[0.2em] text-text-faint">
        {children}
      </span>
      <span className="h-px w-10 bg-gradient-to-l from-transparent to-line sm:w-20" />
    </div>
  )
}
