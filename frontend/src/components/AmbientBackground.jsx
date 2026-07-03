export default function AmbientBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            'linear-gradient(to right, rgba(237,239,234,0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(237,239,234,0.05) 1px, transparent 1px)',
          backgroundSize: '64px 64px',
          maskImage: 'radial-gradient(ellipse 60% 55% at 50% 0%, black 40%, transparent 85%)',
          WebkitMaskImage:
            'radial-gradient(ellipse 60% 55% at 50% 0%, black 40%, transparent 85%)',
        }}
      />
      <div className="absolute left-1/2 top-0 h-[420px] w-[900px] -translate-x-1/2 -translate-y-1/4 rounded-full bg-settled/[0.08] blur-[120px]" />
    </div>
  )
}
