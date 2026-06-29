import { AppShell } from "@/components/AppShell";

export default function MembershipLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}
