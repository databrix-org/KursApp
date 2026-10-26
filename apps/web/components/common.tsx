"use client";
import {
  Alert,
  AlertDescription,
} from "@repo/design-system/components/ui/alert";
import { Button } from "@repo/design-system/components/ui/button";
import { Skeleton } from "@repo/design-system/components/ui/skeleton";
import { useText } from "@/lib/hooks";
export function Notice({ message }: { message: string }) {
  return message ? (
    <Alert role="status" className="my-4">
      <AlertDescription>{message}</AlertDescription>
    </Alert>
  ) : null;
}
export function Loading() {
  return (
    <div role="status" aria-label="Loading" className="space-y-4">
      <Skeleton className="h-10 w-64" />
      <Skeleton className="h-48 w-full" />
    </div>
  );
}
export function Failure({
  error,
  retry,
}: {
  error: string;
  retry: () => void;
}) {
  const t = useText();
  return (
    <div>
      <Notice message={error} />
      <Button onClick={retry}>{t.retry}</Button>
    </div>
  );
}
export function PageTitle({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="mb-10 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          {title}
        </h1>
        {description && (
          <p className="mt-3 max-w-2xl text-muted-foreground">{description}</p>
        )}
      </div>
      {children}
    </div>
  );
}
