import Link from "next/link";
import type { ComponentProps, ReactNode } from "react";

type Variant = "primary" | "dark" | "outline" | "ghost" | "danger";

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-volt text-ink border-ink hover:bg-ink hover:text-volt",
  dark: "bg-ink text-paper border-ink hover:bg-ink-2",
  outline:
    "bg-transparent text-ink border-ink hover:bg-ink hover:text-paper",
  ghost:
    "bg-transparent text-ink border-transparent hover:border-concrete-2 hover:bg-paper",
  danger:
    "bg-transparent text-danger border-danger/40 hover:bg-danger hover:text-paper",
};

const base =
  "inline-flex items-center justify-center gap-2 border-2 rounded-full font-semibold uppercase tracking-wide text-sm px-5 py-2.5 transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer";

export function Button({
  variant = "primary",
  className = "",
  ...props
}: ComponentProps<"button"> & { variant?: Variant }) {
  return (
    <button className={`${base} ${VARIANTS[variant]} ${className}`} {...props} />
  );
}

export function ButtonLink({
  variant = "primary",
  className = "",
  href,
  children,
}: {
  variant?: Variant;
  className?: string;
  href: string;
  children: ReactNode;
}) {
  return (
    <Link href={href} className={`${base} ${VARIANTS[variant]} ${className}`}>
      {children}
    </Link>
  );
}

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`bg-paper border border-concrete-2 rounded-card ${className}`}
    >
      {children}
    </div>
  );
}

export function Kicker({ children }: { children: ReactNode }) {
  return <p className="kicker text-smoke">{children}</p>;
}

export function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: ReactNode;
  hint?: string;
}) {
  return (
    <label className="block">
      <span className="block text-xs font-semibold uppercase tracking-wide text-smoke mb-1.5">
        {label}
      </span>
      {children}
      {hint && <span className="block mt-1 text-xs text-smoke-2">{hint}</span>}
    </label>
  );
}

export const inputCls =
  "w-full bg-concrete border border-concrete-2 rounded-lg px-3.5 py-2.5 text-ink placeholder:text-smoke-2 focus:border-ink focus:bg-paper outline-none transition-colors";
