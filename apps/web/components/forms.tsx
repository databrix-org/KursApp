"use client";
import { useId, useState } from "react";
import { Input } from "@repo/design-system/components/ui/input";
import { Label } from "@repo/design-system/components/ui/label";
import { Button } from "@repo/design-system/components/ui/button";
import { Notice } from "./common";
import { useText } from "@/lib/hooks";
export function Field({
  label,
  ...props
}: { label: string } & React.ComponentProps<typeof Input>) {
  const id = useId();
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <Input id={id} {...props} />
    </div>
  );
}
export function Form({
  onSubmit,
  children,
  label,
}: {
  onSubmit: (data: FormData) => Promise<void>;
  children: React.ReactNode;
  label?: string;
}) {
  const [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  const t = useText();
  return (
    <form
      className="space-y-5"
      onSubmit={async (e) => {
        e.preventDefault();
        const data = new FormData(e.currentTarget);
        setBusy(true);
        setMessage("");
        try {
          await onSubmit(data);
        } catch (e) {
          setMessage(e instanceof Error ? e.message : "Error");
        } finally {
          setBusy(false);
        }
      }}
    >
      {children}
      <Notice message={message} />
      <Button disabled={busy} type="submit">
        {busy ? t.loading : label || t.save}
      </Button>
    </form>
  );
}
export function string(data: FormData, key: string) {
  return String(data.get(key) || "");
}
