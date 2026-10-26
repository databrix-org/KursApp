"use client";
import Link from "next/link";
import { useLocale } from "next-intl";
import { useState } from "react";
import { BookOpen, ArrowUpRight } from "lucide-react";
import { type Course, mutate } from "@repo/api-client";
import { Button } from "@repo/design-system/components/ui/button";
import { Badge } from "@repo/design-system/components/ui/badge";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@repo/design-system/components/ui/card";
import { Input } from "@repo/design-system/components/ui/input";
import { useResource, useText } from "@/lib/hooks";
import { useUser } from "@/components/providers";
import { PageTitle, Loading, Failure, Notice } from "@/components/common";
import { Form, Field, string } from "@/components/forms";
export function Catalog() {
  const t = useText(),
    locale = useLocale(),
    user = useUser(),
    r = useResource<Course[]>("courses/");
  const [search, setSearch] = useState(""),
    [create, setCreate] = useState(false);
  return (
    <>
      <PageTitle title={t.courses} description={t.tagline}>
        {(user.is_instructor || user.is_admin) && (
          <Button onClick={() => setCreate(!create)}>{t.create}</Button>
        )}
      </PageTitle>
      {create && (
        <Card className="mb-8 max-w-lg">
          <CardContent>
            <Form
              onSubmit={async (d) => {
                await mutate("courses/", {
                  title: string(d, "title"),
                  description: string(d, "description"),
                });
                setCreate(false);
                await r.reload();
              }}
            >
              <Field name="title" label={t.title} required />
              <Field name="description" label={t.description} />
            </Form>
          </CardContent>
        </Card>
      )}
      <Input
        aria-label={t.courses}
        placeholder={locale === "de" ? "Kurse durchsuchen…" : "Search courses…"}
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="mb-8 max-w-sm"
      />
      {r.error ? (
        <Failure error={r.error} retry={r.reload} />
      ) : !r.data ? (
        <Loading />
      ) : (
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {r.data
            .filter((c) => c.title.toLowerCase().includes(search.toLowerCase()))
            .map((c) => (
              <Card key={c.id} className="overflow-hidden">
                <div className="flex h-28 items-end justify-between bg-primary/5 p-6">
                  <BookOpen className="size-8 text-primary" />
                  <Badge variant="secondary">
                    {c.is_published ? t.published : t.draft}
                  </Badge>
                </div>
                <CardHeader>
                  <CardTitle className="text-xl">{c.title}</CardTitle>
                  <CardDescription className="line-clamp-3">
                    {c.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground">
                  {c.start_date} {c.end_date && `— ${c.end_date}`}
                </CardContent>
                <CardFooter className="mt-auto">
                  <Button
                    asChild
                    variant="outline"
                    className="w-full justify-between"
                  >
                    <Link href={`/${locale}/courses/${c.id}`}>
                      {t.courseHome}
                      <ArrowUpRight />
                    </Link>
                  </Button>
                </CardFooter>
              </Card>
            ))}
        </div>
      )}
    </>
  );
}
export function Enroll({
  course,
  onDone,
}: {
  course: Course;
  onDone: () => void;
}) {
  const t = useText();
  return (
    <div className="my-8 max-w-md">
      <Notice message={t.enroll} />
      <Form
        label={t.enroll}
        onSubmit={async (d) => {
          await mutate(`courses/${course.id}/enroll/`, {
            key: string(d, "key"),
          });
          onDone();
        }}
      >
        <Field name="key" label={t.enrollmentKey} type="password" />
      </Form>
    </div>
  );
}
