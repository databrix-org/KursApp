"use client";
import { displayValue } from "@repo/i18n";
import Link from "next/link";
import { useLocale } from "next-intl";
import { useEffect, useState } from "react";
import {
  type Submission,
  type Lesson,
  type Asset,
  mutate,
} from "@repo/api-client";
import { Badge } from "@repo/design-system/components/ui/badge";
import { Button } from "@repo/design-system/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@repo/design-system/components/ui/table";
import { Textarea } from "@repo/design-system/components/ui/textarea";
import { Label } from "@repo/design-system/components/ui/label";
import { useText, useResource } from "@/lib/hooks";
import { PageTitle, Loading, Failure, Notice } from "@/components/common";
import { Form, Field, string } from "@/components/forms";
import { AssetList } from "@/modules/learning/assets";
import { NotebookPreview } from "@/modules/grading/notebook";
export function SubmissionList() {
  const t = useText(),
    locale = useLocale(),
    r = useResource<Submission[]>("submissions/");
  return (
    <>
      <PageTitle title={t.submissions} />
      {r.error ? (
        <Failure error={r.error} retry={r.reload} />
      ) : !r.data ? (
        <Loading />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              {["#", t.title, t.status, t.score, t.grade].map((s) => (
                <TableHead key={s}>{s}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {r.data.map((s) => (
              <TableRow key={s.id}>
                <TableCell>#{s.id}</TableCell>
                <TableCell>
                  <Link
                    className="font-medium underline"
                    href={`/${locale}/submissions/${s.id}`}
                  >
                    {s.exercise_title}
                  </Link>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {new Date(s.submitted_at).toLocaleString(locale)}
                  </p>
                </TableCell>
                <TableCell>
                  <Badge
                    variant={s.status === "accepted" ? "secondary" : "outline"}
                  >
                    {displayValue(s.status, locale)}
                  </Badge>
                </TableCell>
                <TableCell>{s.score ?? "—"}</TableCell>
                <TableCell>
                  <Button variant="ghost" asChild>
                    <Link href={`/${locale}/submissions/${s.id}`}>
                      {t.preview} →
                    </Link>
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </>
  );
}
export function SubmissionDetail({ id }: { id: number }) {
  const t = useText(),
    locale = useLocale(),
    r = useResource<Submission>(`submissions/${id}/`),
    lessons = useResource<Lesson[]>("lessons/"),
    [preview, setPreview] = useState(""),
    [compare, setCompare] = useState(""),
    [message, setMessage] = useState("");
  const reload = r.reload,
    s = r.data,
    lesson = lessons.data?.find((l) => l.exercise?.id === s?.exercise),
    refs = useResource<Asset[]>(lesson ? `assets/?lesson=${lesson.id}` : null);
  useEffect(() => {
    if (s?.status === "validating") {
      const timer = setInterval(() => void reload(), 5000);
      return () => clearInterval(timer);
    }
  }, [s?.status, reload]);
  if (r.error) return <Failure error={r.error} retry={r.reload} />;
  if (!s) return <Loading />;
  const canGrade = s.can_grade;
  return (
    <>
      <PageTitle
        title={`${t.submissions} #${s.id}`}
        description={s.exercise_title}
      />
      <div className="mb-8 flex flex-wrap gap-3">
        <Badge>{displayValue(s.status, locale)}</Badge>
        <Badge variant="outline">v{s.exercise_version}</Badge>
        <span className="text-sm text-muted-foreground">
          {s.accepted_at
            ? new Date(s.accepted_at).toLocaleString(locale)
            : new Date(s.submitted_at).toLocaleString(locale)}
        </span>
      </div>
      <Notice
        message={
          s.rejection_reason ||
          message ||
          (s.processing_delayed
            ? locale === "de"
              ? "Die Dateiprüfung verzögert sich. Die Einreichung ist noch nicht angenommen. Bitte kontaktiere den Support."
              : "File verification is delayed. This submission is not accepted yet. Please contact support."
            : "")
        }
      />
      {s.status === "pending" && (
        <Button
          onClick={async () => {
            try {
              await mutate(`submissions/${id}/finalize/`);
              await r.reload();
            } catch (e) {
              setMessage(String(e));
            }
          }}
        >
          {t.retry}
        </Button>
      )}
      <AssetList key={s.status} path={`assets/?submission=${id}`} />
      <div className="my-5 flex flex-wrap gap-2">
        {s.status === "accepted" &&
          s.assets
            .filter((a) => a.name.endsWith(".ipynb"))
            .map((a) => (
              <Button
                key={a.id}
                variant="outline"
                onClick={() => setPreview(a.id)}
              >
                {t.preview}: {a.name}
              </Button>
            ))}
      </div>
      {canGrade && (
        <div className="mb-5 max-w-sm">
          <Label htmlFor="compare">{t.reference}</Label>
          <select
            id="compare"
            className="mt-2 block w-full rounded-md border bg-background p-2"
            value={compare}
            onChange={(e) => setCompare(e.target.value)}
          >
            <option value="">—</option>
            {refs.data
              ?.filter(
                (a) => a.category === "assessment" && a.status === "accepted",
              )
              .map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
          </select>
        </div>
      )}
      {preview && (
        <NotebookPreview id={preview} compare={compare || undefined} />
      )}
      <section className="mt-10 max-w-2xl space-y-6 border-t pt-8">
        <h2 className="text-2xl font-semibold">
          {t.grade}: {s.score ?? "—"}
        </h2>
        <p className="whitespace-pre-wrap">{s.feedback}</p>
        {canGrade && s.status === "accepted" && (
          <Form
            key={s.grade_history.length}
            label={t.grade}
            onSubmit={async (d) => {
              await mutate(`submissions/${id}/grade/`, {
                score: Number(string(d, "score")),
                feedback: string(d, "feedback"),
              });
              await r.reload();
            }}
          >
            <Field
              label={t.score}
              name="score"
              type="number"
              min="0"
              max={s.maximum_points ?? lesson?.exercise?.maximum_points}
              step="0.1"
              defaultValue={s.score ?? ""}
              required
            />
            <Label htmlFor="feedback">{t.feedback}</Label>
            <Textarea
              id="feedback"
              name="feedback"
              defaultValue={s.feedback || ""}
            />
          </Form>
        )}
        <h3 className="font-semibold">
          {locale === "de" ? "Bewertungsverlauf" : "Grading history"}
        </h3>
        {s.grade_history.map((g) => (
          <div key={g.id} className="rounded-md border p-4">
            <p className="font-medium">
              {g.score} · {new Date(g.created_at).toLocaleString(locale)} · #
              {g.grader}
            </p>
            <p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">
              {g.feedback}
            </p>
          </div>
        ))}
      </section>
    </>
  );
}
