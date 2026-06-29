import { AppShell } from "@/components/AppShell";

export default function EventsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}
