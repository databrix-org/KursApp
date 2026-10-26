"use client";
import { displayValue } from "@repo/i18n";
import Link from "next/link";
import { useLocale } from "next-intl";
import { useState } from "react";
import { type Lesson, type Course, mutate } from "@repo/api-client";
import { Button } from "@repo/design-system/components/ui/button";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@repo/design-system/components/ui/accordion";
import { Progress } from "@repo/design-system/components/ui/progress";
import { useText, useResource } from "@/lib/hooks";
import { Loading, Failure, Notice } from "@/components/common";
import { Content } from "./content";
import { AssetList } from "./assets";
import { SubmitWork } from "@/modules/submissions/upload";
import type { Outline } from "@/modules/courses/overview";
export function LessonView({ course, id }: { course: number; id: number }) {
  const t = useText(),
    locale = useLocale(),
    r = useResource<Lesson>(`lessons/${id}/`),
    c = useResource<Course>(`courses/${course}/`),
    outline = useResource<Outline>(`courses/${course}/outline/`);
  const [message, setMessage] = useState("");
  if (r.error) return <Failure error={r.error} retry={r.reload} />;
  if (outline.error)
    return <Failure error={outline.error} retry={outline.reload} />;
  if (!r.data || !outline.data) return <Loading />;
  const l = r.data,
    lessons = outline.data.lessons,
    next = lessons[lessons.findIndex((x) => x.id === id) + 1];
  return (
    <>
      <nav
        aria-label="Breadcrumb"
        className="mb-8 flex flex-wrap gap-2 text-sm text-muted-foreground"
      >
        <Link href={`/${locale}/courses`}>{t.courses}</Link>
        <span>/</span>
        <Link href={`/${locale}/courses/${course}`}>{c.data?.title}</Link>
        <span>/</span>
        <span aria-current="page">{l.title}</span>
      </nav>
      <div className="grid items-start gap-10 lg:grid-cols-[220px_minmax(0,1fr)]">
        <aside className="rounded-lg border bg-card p-5 lg:sticky lg:top-24">
          <p className="mb-3 font-semibold">{t.learning}</p>
          <Progress
            aria-label={t.completed}
            value={
              lessons.length
                ? (100 * lessons.filter((x) => x.completed).length) /
                  lessons.length
                : 0
            }
          />
          <Accordion
            type="multiple"
            defaultValue={outline.data.modules
              .filter((m) => m.id === l.module)
              .map((m) => String(m.id))}
            className="mt-5"
          >
            {outline.data.modules.map((m) => (
              <AccordionItem key={m.id} value={String(m.id)}>
                <AccordionTrigger>{m.title}</AccordionTrigger>
                <AccordionContent>
                  <ul className="space-y-3 border-l pl-3">
                    {lessons
                      .filter((x) => x.module === m.id)
                      .map((x) => (
                        <li key={x.id}>
                          <Link
                            href={`/${locale}/courses/${course}/lessons/${x.id}`}
                            aria-current={id === x.id ? "page" : undefined}
                            className="text-sm text-muted-foreground aria-[current=page]:font-semibold aria-[current=page]:text-primary"
                          >
                            {x.completed ? "✓ " : ""}
                            {x.title}
                          </Link>
                        </li>
                      ))}
                  </ul>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </aside>
        <article className="min-w-0">
          <p className="mb-3 text-sm uppercase tracking-widest text-primary">
            {displayValue(l.lesson_type, locale)}
          </p>
          <h1 className="mb-8 text-4xl font-semibold tracking-tight">
            {l.title}
          </h1>
          {l.lesson_type === "video" && (
            <div className="mb-10">
              <AssetList path={`assets/?lesson=${id}`} video />
            </div>
          )}
          <Content html={l.lesson_content || ""} />
          <section className="my-10 space-y-5">
            <h2 className="text-xl font-semibold">{t.materials}</h2>
            {l.lesson_type !== "video" && (
              <AssetList path={`assets/?lesson=${id}`} />
            )}
          </section>
          {l.exercise && <SubmitWork exercise={l.exercise.id} />}
          <Notice message={message} />
          <div className="mt-12 flex flex-wrap justify-between gap-4 border-t pt-6">
            <Button
              variant={l.completed ? "secondary" : "default"}
              onClick={async () => {
                try {
                  await mutate(
                    `lessons/${id}/completion/`,
                    { completed: !l.completed },
                    "PUT",
                  );
                  await Promise.all([r.reload(), outline.reload()]);
                } catch (e) {
                  setMessage(String(e));
                }
              }}
            >
              {l.completed ? t.completed : t.complete}
            </Button>
            {next && (
              <Button variant="outline" asChild>
                <Link href={`/${locale}/courses/${course}/lessons/${next.id}`}>
                  {t.next} →
                </Link>
              </Button>
            )}
          </div>
        </article>
      </div>
    </>
  );
}
