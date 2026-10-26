"use client";
import { displayValue } from "@repo/i18n";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useLocale } from "next-intl";
import {
  api,
  mutate,
  putFile,
  type Submission,
  type UploadGrant,
} from "@repo/api-client";
import { Button } from "@repo/design-system/components/ui/button";
import { Input } from "@repo/design-system/components/ui/input";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@repo/design-system/components/ui/card";
import { Label } from "@repo/design-system/components/ui/label";
import { Notice } from "@/components/common";
import { useText } from "@/lib/hooks";
import { useUser } from "@/components/providers";
export function SubmitWork({ exercise }: { exercise: number }) {
  const user = useUser(),
    storageKey = `submission-${user.id}-${exercise}`;
  const t = useText(),
    locale = useLocale(),
    [files, setFiles] = useState<File[]>([]),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [receipt, setReceipt] = useState<Submission>(),
    key = useRef("");
  useEffect(() => {
    const stored = localStorage.getItem(storageKey);
    if (stored) {
      const data = JSON.parse(stored);
      key.current = data.key;
      if (data.id)
        void api<Submission>(`submissions/${data.id}/`)
          .then(setReceipt)
          .catch(() => {});
    }
  }, [storageKey]);
  async function send() {
    setBusy(true);
    setMessage("");
    try {
      if (receipt && receipt.status !== "pending") {
        setReceipt(
          await mutate<Submission>(`submissions/${receipt.id}/finalize/`),
        );
        return;
      }
      if (!files.length)
        throw new Error(
          locale === "de" ? "Bitte Dateien auswählen." : "Please choose files.",
        );
      if (!key.current) key.current = crypto.randomUUID();
      localStorage.setItem(storageKey, JSON.stringify({ key: key.current }));
      const result = await mutate<{
        submission: Submission;
        uploads: UploadGrant[];
      }>("submissions/initiate/", {
        exercise_id: exercise,
        idempotency_key: key.current,
        files: files.map((f) => ({ name: f.name, size: f.size })),
      });
      setReceipt(result.submission);
      localStorage.setItem(
        storageKey,
        JSON.stringify({ key: key.current, id: result.submission.id }),
      );
      if (result.uploads.length !== files.length)
        throw new Error("Upload manifest differs. Start a new submission.");
      for (let i = 0; i < files.length; i++)
        await putFile(result.uploads[i], files[i]);
      const sub = await mutate<Submission>(
        `submissions/${result.submission.id}/finalize/`,
      );
      setReceipt(sub);
      setMessage(
        locale === "de"
          ? "Dateien hochgeladen. Die Annahme erfolgt nach Prüfung."
          : "Files uploaded. Acceptance follows verification.",
      );
    } catch (e) {
      setMessage(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <Card className="my-8">
      <CardHeader>
        <CardTitle>{t.submit}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          {locale === "de"
            ? "Speichere und exportiere deine Arbeit im Notebook-Labor. Lade anschließend die Dateien hier hoch. Spätere Änderungen im Labor verändern eine angenommene Einreichung nicht."
            : "Save and export your work from the notebook lab, then upload the files here. Later lab edits do not change an accepted submission."}
        </p>
        <Label htmlFor={"files-" + exercise}>{t.upload}</Label>
        <Input
          id={"files-" + exercise}
          type="file"
          multiple
          disabled={busy || (!!receipt && receipt.status !== "pending")}
          onChange={(e) => setFiles(Array.from(e.target.files || []))}
        />
        <div className="flex flex-wrap gap-3">
          <Button disabled={busy} onClick={send}>
            {busy
              ? t.loading
              : receipt?.status === "validating"
                ? t.retry
                : t.submit}
          </Button>
          {receipt && (
            <Button variant="outline" asChild>
              <Link href={`/${locale}/submissions/${receipt.id}`}>
                #{receipt.id} · {displayValue(receipt.status, locale)}
              </Link>
            </Button>
          )}
          {receipt && (
            <Button
              variant="ghost"
              onClick={() => {
                key.current = "";
                setReceipt(undefined);
                setFiles([]);
                localStorage.removeItem(storageKey);
              }}
            >
              {locale === "de" ? "Neue Einreichung" : "New submission"}
            </Button>
          )}
        </div>
        <Notice message={message} />
      </CardContent>
    </Card>
  );
}
