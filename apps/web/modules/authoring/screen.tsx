"use client";
import { displayValue } from "@repo/i18n";
import { useState } from "react";
import Link from "next/link";
import { useLocale } from "next-intl";
import { mutate, type Course, type Lesson } from "@repo/api-client";
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@repo/design-system/components/ui/tabs";
import { Button } from "@repo/design-system/components/ui/button";
import { Textarea } from "@repo/design-system/components/ui/textarea";
import { Label } from "@repo/design-system/components/ui/label";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@repo/design-system/components/ui/card";
import { PageTitle, Loading, Failure, Notice } from "@/components/common";
import { Form, Field, string } from "@/components/forms";
import { useText, useResource } from "@/lib/hooks";
import { useUser } from "@/components/providers";
import { RichEditor } from "./editor";
import { AssetUpload, uploadInlineImage } from "./assets";
import type { Outline } from "@/modules/courses/overview";
function LessonEditor({
  lesson,
  course,
  reload,
}: {
  lesson: Lesson;
  course: number;
  reload: () => Promise<void>;
}) {
  const t = useText(),
    locale = useLocale(),
    [html, setHtml] = useState(lesson.lesson_content || "");
  return (
    <div className="space-y-8 rounded-lg border bg-card p-6">
      <h3 className="text-xl font-semibold">{lesson.title}</h3>
      <Form
        onSubmit={async (d) => {
          await mutate(
            `lessons/${lesson.id}/`,
            {
              title: string(d, "title"),
              lesson_type: string(d, "lesson_type"),
              duration: string(d, "duration"),
              order: Number(string(d, "order")),
              lesson_content: html,
            },
            "PATCH",
          );
          await reload();
        }}
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <Field
            label={t.title}
            name="title"
            defaultValue={lesson.title}
            required
          />
          <Field
            label={locale === "de" ? "Reihenfolge" : "Order"}
            name="order"
            type="number"
            min="0"
            defaultValue={lesson.order}
          />
          <div className="space-y-2">
            <Label htmlFor={"type-" + lesson.id}>
              {locale === "de" ? "Typ" : "Type"}
            </Label>
            <select
              className="w-full rounded-md border bg-background p-2"
              id={"type-" + lesson.id}
              name="lesson_type"
              defaultValue={lesson.lesson_type}
            >
              {["reading", "video", "exercise"].map((v) => (
                <option key={v} value={v}>
                  {displayValue(v, locale)}
                </option>
              ))}
            </select>
          </div>
          <Field
            label={locale === "de" ? "Dauer (HH:MM:SS)" : "Duration (HH:MM:SS)"}
            name="duration"
            defaultValue={lesson.duration}
          />
        </div>
        <Label>{t.instructions}</Label>
        <RichEditor
          initial={lesson.lesson_content || ""}
          onChange={setHtml}
          label={t.instructions}
          uploadImage={(file) => uploadInlineImage(course, lesson.id, file)}
        />
      </Form>
      {lesson.lesson_type === "exercise" && (
        <Form
          label={t.save + " · " + t.grade}
          onSubmit={async (d) => {
            await mutate(
              `lessons/${lesson.id}/exercise/`,
              {
                exercise_type: string(d, "exercise_type"),
                maximum_points: Number(string(d, "maximum_points")),
                pass_points: Number(string(d, "pass_points")),
              },
              "PUT",
            );
            await reload();
          }}
        >
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <Label htmlFor={"ex-" + lesson.id}>
                {locale === "de" ? "Aufgabentyp" : "Exercise type"}
              </Label>
              <select
                name="exercise_type"
                id={"ex-" + lesson.id}
                className="mt-2 w-full rounded-md border bg-background p-2"
                defaultValue={lesson.exercise?.exercise_type || "jupyter"}
              >
                <option value="jupyter">Jupyter</option>
                <option value="traditional">
                  {locale === "de" ? "Dateiaufgabe" : "File exercise"}
                </option>
              </select>
            </div>
            <Field
              label={locale === "de" ? "Maximale Punkte" : "Maximum points"}
              name="maximum_points"
              type="number"
              min="0"
              defaultValue={lesson.exercise?.maximum_points ?? 10}
            />
            <Field
              label={locale === "de" ? "Bestehensgrenze" : "Pass points"}
              name="pass_points"
              type="number"
              min="0"
              defaultValue={lesson.exercise?.pass_points ?? 5}
            />
          </div>
        </Form>
      )}
      <AssetUpload course={course} lesson={lesson.id} />
      {lesson.exercise && (
        <AssetUpload course={course} lesson={lesson.id} category="assessment" />
      )}
      <Button
        variant="destructive"
        onClick={async () => {
          if (confirm(t.delete + "?")) {
            try {
              await mutate(`lessons/${lesson.id}/`, {}, "DELETE");
              await reload();
            } catch (e) {
              alert(String(e));
            }
          }
        }}
      >
        {t.delete}
      </Button>
    </div>
  );
}
export function Authoring({ id }: { id: number }) {
  const t = useText(),
    locale = useLocale(),
    user = useUser(),
    c = useResource<Course>(`courses/${id}/`),
    o = useResource<Outline>(`courses/${id}/outline/`),
    [editing, setEditing] = useState<number>(),
    [message, setMessage] = useState("");
  const students = useResource<
      {
        student_id: number;
        student__first_name: string;
        student__last_name: string;
        student__email: string;
        notebook_access__confirmed: boolean | null;
      }[]
    >(c.data?.capabilities.teach ? `courses/${id}/students/` : null),
    staff = useResource<
      { id: number; first_name: string; last_name: string; role: string }[]
    >(c.data?.capabilities.teach ? `courses/${id}/staff/` : null);
  if (c.error) return <Failure error={c.error} retry={c.reload} />;
  if (!c.data || !o.data) return <Loading />;
  if (!c.data.capabilities.teach) return <Notice message="403" />;
  const course = c.data,
    selected = o.data.lessons.find((l) => l.id === editing);
  return (
    <>
      <PageTitle title={t.manage} description={course.title}>
        <Button variant="outline" asChild>
          <Link href={`/${locale}/courses/${id}`}>{t.courseHome}</Link>
        </Button>
      </PageTitle>
      <Notice message={message} />
      <Tabs defaultValue="content">
        <TabsList className="mb-8 flex h-auto flex-wrap">
          <TabsTrigger value="content">{t.learning}</TabsTrigger>
          <TabsTrigger value="settings">{t.manage}</TabsTrigger>
          <TabsTrigger value="students">{t.users}</TabsTrigger>
          <TabsTrigger value="announcements">{t.announcements}</TabsTrigger>
          <TabsTrigger value="statistics">{t.statistics}</TabsTrigger>
        </TabsList>
        <TabsContent value="content">
          {selected ? (
            <>
              <Button
                variant="ghost"
                className="mb-5"
                onClick={() => setEditing(undefined)}
              >
                ← {t.back}
              </Button>
              <LessonEditor
                key={selected.id}
                lesson={selected}
                course={id}
                reload={o.reload}
              />
            </>
          ) : (
            <div className="space-y-6">
              {o.data.modules.map((m) => (
                <Card key={m.id}>
                  <CardHeader>
                    <CardTitle>{m.title}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-5">
                    {(course.capabilities.manage ||
                      m.instructor === user.id) && (
                      <>
                        <Form
                          onSubmit={async (d) => {
                            await mutate(
                              `modules/${m.id}/`,
                              {
                                title: string(d, "title"),
                                description: string(d, "description"),
                                order: Number(string(d, "order")),
                                difficulty_level: Number(
                                  string(d, "difficulty_level"),
                                ),
                                instructor: Number(string(d, "instructor")),
                              },
                              "PATCH",
                            );
                            await o.reload();
                          }}
                        >
                          <div className="grid gap-4 sm:grid-cols-3">
                            <Field
                              label={t.title}
                              name="title"
                              defaultValue={m.title}
                              required
                            />
                            <Field
                              label={locale === "de" ? "Reihenfolge" : "Order"}
                              name="order"
                              type="number"
                              min="0"
                              defaultValue={m.order}
                            />
                            <Field
                              label={
                                locale === "de"
                                  ? "Schwierigkeit (1–5)"
                                  : "Difficulty (1–5)"
                              }
                              name="difficulty_level"
                              type="number"
                              min="1"
                              max="5"
                              defaultValue={m.difficulty_level}
                            />
                          </div>
                          <Field
                            label={t.description}
                            name="description"
                            defaultValue={m.description || ""}
                          />
                          <Label htmlFor={"teacher-" + m.id}>
                            {locale === "de" ? "Lehrperson" : "Instructor"}
                          </Label>
                          <select
                            id={"teacher-" + m.id}
                            name="instructor"
                            defaultValue={m.instructor}
                            disabled={!course.capabilities.manage}
                            className="rounded-md border bg-background p-2"
                          >
                            {staff.data?.map((s) => (
                              <option key={s.id} value={s.id}>
                                {s.first_name} {s.last_name}
                              </option>
                            ))}
                          </select>
                          {!course.capabilities.manage && (
                            <input
                              type="hidden"
                              name="instructor"
                              value={m.instructor}
                            />
                          )}
                        </Form>
                        <Button
                          variant="ghost"
                          onClick={async () => {
                            if (!confirm(t.delete + "?")) return;
                            try {
                              await mutate(`modules/${m.id}/`, {}, "DELETE");
                              await o.reload();
                            } catch (e) {
                              setMessage(String(e));
                            }
                          }}
                        >
                          {t.delete}
                        </Button>
                      </>
                    )}
                    <ul className="divide-y">
                      {o
                        .data!.lessons.filter((l) => l.module === m.id)
                        .map((l) => (
                          <li
                            key={l.id}
                            className="flex items-center justify-between py-3"
                          >
                            <span>
                              {l.order}. {l.title}
                            </span>
                            {(course.capabilities.manage ||
                              m.instructor === user.id) && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setEditing(l.id)}
                              >
                                {t.manage}
                              </Button>
                            )}
                          </li>
                        ))}
                    </ul>
                    {(course.capabilities.manage ||
                      m.instructor === user.id) && (
                      <Form
                        label={t.create}
                        onSubmit={async (d) => {
                          const l = await mutate<Lesson>("lessons/", {
                            module: m.id,
                            title: string(d, "title"),
                            order: o.data!.lessons.filter(
                              (l) => l.module === m.id,
                            ).length,
                            lesson_type: "reading",
                          });
                          await o.reload();
                          setEditing(l.id);
                        }}
                      >
                        <Field label={t.title} name="title" required />
                      </Form>
                    )}
                  </CardContent>
                </Card>
              ))}
              {course.capabilities.manage && (
                <Card>
                  <CardHeader>
                    <CardTitle>
                      {locale === "de" ? "Modul hinzufügen" : "Add module"}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Form
                      label={t.create}
                      onSubmit={async (d) => {
                        await mutate("modules/", {
                          course: id,
                          instructor: user.id,
                          title: string(d, "title"),
                          order: o.data!.modules.length,
                        });
                        await o.reload();
                      }}
                    >
                      <Field name="title" label={t.title} required />
                    </Form>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </TabsContent>
        <TabsContent value="settings">
          <div className="max-w-2xl">
            {course.capabilities.manage && (
              <Form
                key={course.id}
                onSubmit={async (d) => {
                  const result = await mutate<Course>(
                    `courses/${id}/`,
                    {
                      title: string(d, "title"),
                      description: string(d, "description"),
                      start_date: string(d, "start_date") || null,
                      end_date: string(d, "end_date") || null,
                      difficulty_level: Number(string(d, "difficulty_level")),
                      max_members: Number(string(d, "max_members")),
                      is_published: d.has("published"),
                      frontend_enabled: d.has("frontend"),
                      lab_url: string(d, "lab_url"),
                      ...(string(d, "key")
                        ? { enrollment_key: string(d, "key") }
                        : {}),
                    },
                    "PATCH",
                  );
                  c.setData(result);
                  setMessage(t.save + " ✓");
                }}
              >
                <Field
                  label={t.title}
                  name="title"
                  defaultValue={course.title}
                />
                <Label htmlFor="description">{t.description}</Label>
                <Textarea
                  id="description"
                  name="description"
                  defaultValue={course.description}
                />
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field
                    label={locale === "de" ? "Beginn" : "Start"}
                    name="start_date"
                    type="date"
                    defaultValue={course.start_date || ""}
                  />
                  <Field
                    label={t.deadline}
                    name="end_date"
                    type="date"
                    defaultValue={course.end_date || ""}
                  />
                  <Field
                    label={locale === "de" ? "Teamgröße" : "Team capacity"}
                    name="max_members"
                    type="number"
                    min="1"
                    max="100"
                    defaultValue={course.max_members}
                  />
                  <Field
                    label={
                      locale === "de"
                        ? "Schwierigkeit (1–5)"
                        : "Difficulty (1–5)"
                    }
                    name="difficulty_level"
                    type="number"
                    min="1"
                    max="5"
                    defaultValue={course.difficulty_level}
                  />
                </div>
                <Field
                  label={t.enrollmentKey}
                  name="key"
                  type="password"
                  placeholder={
                    locale === "de"
                      ? "Leer lassen zum Beibehalten"
                      : "Leave empty to retain current key"
                  }
                />
                <Field
                  label={t.lab + " URL"}
                  name="lab_url"
                  type="url"
                  defaultValue={course.lab_url}
                />
                <label className="flex gap-3 text-sm">
                  <input
                    type="checkbox"
                    name="published"
                    defaultChecked={course.is_published}
                  />
                  {t.published}
                </label>
                <label className="flex gap-3 text-sm">
                  <input
                    type="checkbox"
                    name="frontend"
                    defaultChecked={course.frontend_enabled}
                  />
                  {locale === "de"
                    ? "Neue Oberfläche für diesen Kurs aktivieren"
                    : "Enable new interface for this course"}
                </label>
              </Form>
            )}
          </div>
        </TabsContent>
        <TabsContent value="students">
          <div className="space-y-4">
            {students.data?.map((s) => (
              <div
                key={s.student_id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-4"
              >
                <div>
                  {s.student__first_name} {s.student__last_name}
                  <p className="text-sm text-muted-foreground">
                    #{s.student_id} · {s.student__email}
                  </p>
                </div>
                {course.capabilities.manage && (
                  <Button
                    variant="outline"
                    onClick={async () => {
                      try {
                        await mutate(`courses/${id}/notebook-access/`, {
                          user_id: s.student_id,
                          confirmed: !s.notebook_access__confirmed,
                        });
                        await students.reload();
                      } catch (e) {
                        setMessage(String(e));
                      }
                    }}
                  >
                    {t.lab}: {s.notebook_access__confirmed ? "✓" : "—"}
                  </Button>
                )}
              </div>
            ))}
            {course.capabilities.manage && (
              <Form
                label={t.create}
                onSubmit={async (d) => {
                  await mutate(`courses/${id}/staff/`, {
                    user_id: Number(string(d, "user_id")),
                    role: "instructor",
                  });
                  await staff.reload();
                }}
              >
                <Field
                  label={
                    locale === "de"
                      ? "Lehrperson: Benutzer-ID"
                      : "Instructor: user ID"
                  }
                  name="user_id"
                  type="number"
                  required
                />
              </Form>
            )}
            {staff.data?.map((s) => (
              <p key={s.id} className="text-sm">
                #{s.id} · {s.first_name} {s.last_name} · {s.role}
                {course.capabilities.manage && s.id !== course.instructor && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={async () => {
                      await mutate(
                        `courses/${id}/staff/`,
                        { user_id: s.id },
                        "DELETE",
                      );
                      await staff.reload();
                    }}
                  >
                    {t.delete}
                  </Button>
                )}
              </p>
            ))}
          </div>
        </TabsContent>
        <TabsContent value="announcements">
          <div className="max-w-xl">
            <Form
              label={t.announcements}
              onSubmit={async (d) => {
                await mutate(`courses/${id}/announcements/`, {
                  subject: string(d, "subject"),
                  body: string(d, "body"),
                });
                setMessage(
                  locale === "de"
                    ? "Nachricht wird versendet."
                    : "Message queued.",
                );
              }}
            >
              <Field label={t.title} name="subject" required />
              <Label htmlFor="announcement">{t.description}</Label>
              <Textarea id="announcement" name="body" required />
            </Form>
          </div>
        </TabsContent>
        <TabsContent value="statistics">
          <Statistics id={id} />
        </TabsContent>
      </Tabs>
    </>
  );
}
function Statistics({ id }: { id: number }) {
  const t = useText(),
    r = useResource<
      {
        group_id: number | null;
        submissions: number;
        average: number | null;
        maximum: number | null;
        members: string[];
      }[]
    >(`courses/${id}/statistics/`);
  return (
    <div className="space-y-3">
      <Notice message={r.error} />
      {r.data?.map((s, i) => (
        <Card key={i}>
          <CardContent>
            {t.teams} #{s.group_id ?? "—"} · {t.submissions}: {s.submissions} ·
            Ø {t.score}: {s.average?.toFixed(1) ?? "—"} · Max:{" "}
            {s.maximum ?? "—"}
            <p className="mt-2 text-sm text-muted-foreground">
              {s.members.join(", ")}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
