import { notFound } from "next/navigation";
import { Providers } from "@/components/providers";
export default async function Layout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (locale !== "de" && locale !== "en") notFound();
  return <Providers locale={locale}>{children}</Providers>;
}
