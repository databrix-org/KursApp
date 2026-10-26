"use client";
import { Button } from "@repo/design-system/components/ui/button";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <main className="mx-auto max-w-xl p-12">
      <h1 className="text-2xl font-semibold">
        Dienst vorübergehend nicht verfügbar / Service temporarily unavailable
      </h1>
      <p className="my-5">
        Your saved records are unchanged. Please try again.
      </p>
      <Button onClick={reset}>Erneut versuchen / Try again</Button>
    </main>
  );
}
