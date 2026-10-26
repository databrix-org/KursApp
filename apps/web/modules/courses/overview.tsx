"use client";
import { displayValue } from "@repo/i18n";
import Link from "next/link";
import { useLocale } from "next-intl";
import { useState } from "react";
import { type Course, type Module, type Lesson, api } from "@repo/api-client";
import { Button } from "@repo/design-system/components/ui/button";
import { Progress } from "@repo/design-system/components/ui/progress";
import { Badge } from "@repo/design-system/components/ui/badge";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@repo/design-system/components/ui/accordion";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@repo/design-system/components/ui/card";
import { PageTitle, Loading, Failure, Notice } from "@/components/common";
import { useResource, useText } from "@/lib/hooks";
import { Enroll } from "./catalog";
export type Outline = { modules: Module[]; lessons: Lesson[] };
export function Overview({ id }: { id: number }) {
  const t = useText(),
    locale = useLocale(),
    r = useResource<Course>(`courses/${id}/`),
    c = r.data,
    allowed = c && (c.enrolled || c.capabilities.teach),
    o = useResource<Outline>(allowed ? `courses/${id}/outline/` : null);
  const [message, setMessage] = useState("");
  if (r.error) return <Failure error={r.error} retry={r.reload} />;
  if (!c) return <Loading />;
  return (
    <>
      <Link
        href={`/${locale}/courses`}
        className="mb-6 inline-block text-sm text-muted-foreground"
      >
        ← {t.courses}
      </Link>
      <PageTitle title={c.title} description={c.description}>
        {c.capabilities.teach && (
          <Button variant="outline" asChild>
            <Link href={`/${locale}/courses/${id}/manage`}>{t.manage}</Link>
          </Button>
        )}
      </PageTitle>
      {!allowed ? (
        <Enroll course={c} onDone={r.reload} />
      ) : (
        <>
          <div className="mb-10 grid gap-5 sm:grid-cols-3">
            <Card className="sm:col-span-2">
              <CardHeader>
                <CardTitle>{t.learning}</CardTitle>
              </CardHeader>
              <CardContent>
                <Progress
                  aria-label={t.completed}
                  value={
                    o.data?.lessons.length
                      ? (100 *
                          o.data.lessons.filter((l) => l.completed).length) /
                        o.data.lessons.length
                      : 0
                  }
                />
                <p className="mt-3 text-sm text-muted-foreground">
                  {o.data?.lessons.filter((l) => l.completed).length || 0} /{" "}
                  {o.data?.lessons.length || 0} {t.completed.toLowerCase()}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="flex flex-col gap-3">
                <Button
                  onClick={async () => {
                    try {
                      const n = await api<{ status: string; url?: string }>(
                        `courses/${id}/notebook/`,
                      );
                      if (n.url)
                        window.open(n.url, "_blank", "noopener,noreferrer");
                      else setMessage(t.pendingLab);
                    } catch (e) {
                      setMessage(String(e));
                    }
                  }}
                >
                  {t.lab}
                </Button>
                <Button variant="outline" asChild>
                  <Link href={`/${locale}/courses/${id}/teams`}>{t.teams}</Link>
                </Button>
              </CardContent>
            </Card>
          </div>
          <Notice message={message} />
          {o.error ? (
            <Failure error={o.error} retry={o.reload} />
          ) : !o.data ? (
            <Loading />
          ) : (
            <Accordion
              type="multiple"
              defaultValue={o.data.modules.map((m) => String(m.id))}
            >
              {o.data.modules.map((m) => (
                <AccordionItem key={m.id} value={String(m.id)}>
                  <AccordionTrigger className="text-lg">
                    {m.title}
                  </AccordionTrigger>
                  <AccordionContent>
                    <p className="mb-4 text-muted-foreground">
                      {m.description}
                    </p>
                    <div className="divide-y">
                      {o
                        .data!.lessons.filter((l) => l.module === m.id)
                        .map((l) => (
                          <Link
                            className="flex items-center justify-between gap-4 py-4 hover:text-primary"
                            key={l.id}
                            href={`/${locale}/courses/${id}/lessons/${l.id}`}
                          >
                            <span>
                              {l.completed ? "✓ " : ""}
                              {l.title}
                            </span>
                            <Badge variant="secondary">
                              {displayValue(l.lesson_type, locale)}
                            </Badge>
                          </Link>
                        ))}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          )}
        </>
      )}
    </>
  );
}
