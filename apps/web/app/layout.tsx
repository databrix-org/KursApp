import { headers } from "next/headers";
import "@repo/design-system/styles/globals.css";
export const metadata = {
  title: { default: "Databrix", template: "%s · Databrix" },
  description: "Learn data science with courses and collaborative notebooks.",
};
export default async function RootLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale?: string }>;
}) {
  const { locale: hint } = await params;
  const locale = hint || (await headers()).get("x-databrix-locale");
  return (
    <html lang={locale === "en" ? "en" : "de"} suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
