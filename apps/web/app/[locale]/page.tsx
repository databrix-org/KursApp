import Link from "next/link";
import { dictionary } from "@repo/i18n";
import { Button } from "@repo/design-system/components/ui/button";
export default async function Home({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params,
    t = dictionary(locale);
  return (
    <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-6">
      <header className="flex items-center justify-between py-8">
        <span className="text-2xl font-bold tracking-tight">
          databrix<span className="text-primary">.</span>
        </span>
        <Button asChild variant="outline">
          <Link href={`/${locale}/login`}>{t.login}</Link>
        </Button>
      </header>
      <main className="flex flex-1 flex-col justify-center py-20">
        <p className="mb-6 text-sm font-medium uppercase tracking-[.25em] text-primary">
          Data Science · DHBW
        </p>
        <h1 className="max-w-4xl text-5xl font-semibold leading-[1.1] tracking-tighter sm:text-7xl">
          {t.welcome}
        </h1>
        <p className="mt-8 max-w-xl text-xl leading-relaxed text-muted-foreground">
          {t.tagline}
        </p>
        <Button asChild size="lg" className="mt-10 w-fit">
          <Link href={`/${locale}/courses`}>{t.start} →</Link>
        </Button>
        <div className="mt-20 grid gap-6 border-t pt-8 sm:grid-cols-3">
          {(locale === "de"
            ? [
                "01 · Videos & Lesen",
                "02 · Notebook-Projekte",
                "03 · Feedback & Fortschritt",
              ]
            : [
                "01 · Video & reading",
                "02 · Notebook projects",
                "03 · Feedback & progress",
              ]
          ).map((x) => (
            <div key={x} className="font-mono text-sm text-muted-foreground">
              {x}
            </div>
          ))}
        </div>
      </main>
      <footer className="flex gap-6 border-t py-8 text-sm text-muted-foreground">
        <Link href={`/${locale}/imprint`}>{t.imprint}</Link>
        <Link href={`/${locale}/privacy`}>{t.privacy}</Link>
        <Link href={locale === "de" ? "/en" : "/de"}>
          {locale === "de" ? "English" : "Deutsch"}
        </Link>
      </footer>
    </div>
  );
}
