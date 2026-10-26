import { redirect } from "next/navigation";
import { getSession } from "@/lib/server";
import { Shell } from "@/components/shell";
export const dynamic = "force-dynamic";
export default async function Layout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const session = await getSession();
  if (!session.user) redirect(`/${locale}/login`);
  return <Shell user={session.user}>{children}</Shell>;
}
