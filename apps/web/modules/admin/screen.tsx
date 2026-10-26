"use client";
import { displayValue } from "@repo/i18n";
import { useState } from "react";
import { useLocale } from "next-intl";
import { type User, type Course, mutate } from "@repo/api-client";
import { Button } from "@repo/design-system/components/ui/button";
import {
  Table,
  TableHeader,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
} from "@repo/design-system/components/ui/table";
import { PageTitle, Notice } from "@/components/common";
import { Field, Form, string } from "@/components/forms";
import { useText, useResource } from "@/lib/hooks";
import { useUser } from "@/components/providers";
export function Admin() {
  const t = useText(),
    locale = useLocale(),
    self = useUser(),
    r = useResource<User[]>(self.is_admin ? "users/" : null),
    courses = useResource<Course[]>("courses/"),
    [message, setMessage] = useState("");
  if (!self.is_admin) return <Notice message="403" />;
  return (
    <>
      <PageTitle title={t.admin} />
      <Notice message={message || r.error} />
      <section className="mb-12 max-w-xl rounded-lg border p-6">
        <h2 className="mb-6 text-xl font-semibold">{t.invite}</h2>
        <Form
          label={t.invite}
          onSubmit={async (d) => {
            await mutate("invitations/", {
              email: string(d, "email"),
              role: string(d, "role"),
              course: string(d, "course") ? Number(string(d, "course")) : null,
            });
            setMessage(
              locale === "de"
                ? "Einladung wird versendet."
                : "Invitation queued.",
            );
          }}
        >
          <Field label={t.email} name="email" type="email" required />
          <label className="block text-sm">
            {locale === "de" ? "Rolle" : "Role"}
            <select
              name="role"
              className="mt-2 block w-full rounded-md border bg-background p-2"
            >
              <option value="student">Student</option>
              <option value="instructor">
                {locale === "de" ? "Lehrperson" : "Instructor"}
              </option>
            </select>
          </label>
          <label className="block text-sm">
            {t.courses}
            <select
              name="course"
              className="mt-2 block w-full rounded-md border bg-background p-2"
            >
              <option value="">—</option>
              {courses.data?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title}
                </option>
              ))}
            </select>
          </label>
        </Form>
      </section>
      <section className="mb-12 max-w-xl rounded-lg border p-6">
        <h2 className="mb-6 text-xl font-semibold">{t.announcements}</h2>
        <Form
          label={t.announcements}
          onSubmit={async (d) => {
            await mutate("admin/announcements/", {
              subject: string(d, "subject"),
              body: string(d, "body"),
              recipients: string(d, "recipients"),
              selected_users: string(d, "selected_users")
                .split(",")
                .filter(Boolean)
                .map(Number),
            });
            setMessage(
              locale === "de"
                ? "Nachrichten werden versendet."
                : "Messages queued.",
            );
          }}
        >
          <Field label={t.title} name="subject" required />
          <Field label={t.description} name="body" required />
          <label className="block text-sm">
            {locale === "de" ? "Empfänger" : "Recipients"}
            <select
              className="mt-2 block w-full rounded-md border bg-background p-2"
              name="recipients"
            >
              {["all", "students", "instructors", "selected"].map((v) => (
                <option key={v} value={v}>
                  {displayValue(v, locale)}
                </option>
              ))}
            </select>
          </label>
          <Field
            label={
              locale === "de"
                ? "Ausgewählte Benutzer-IDs (Komma)"
                : "Selected user IDs (comma separated)"
            }
            name="selected_users"
          />
        </Form>
      </section>
      <h2 className="mb-6 text-xl font-semibold">{t.users}</h2>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>#</TableHead>
            <TableHead>{t.profile}</TableHead>
            <TableHead>{t.status}</TableHead>
            <TableHead>{t.manage}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {r.data?.map((u) => (
            <TableRow key={u.id}>
              <TableCell>{u.id}</TableCell>
              <TableCell>
                {u.first_name} {u.last_name}
                <p className="text-xs text-muted-foreground">{u.email}</p>
              </TableCell>
              <TableCell>{u.is_active ? "✓" : "—"}</TableCell>
              <TableCell>
                <div className="flex gap-2">
                  <select
                    aria-label={
                      locale === "de" ? "Rolle ändern" : "Change role"
                    }
                    disabled={u.id === self.id}
                    className="rounded-md border bg-background p-2"
                    value={
                      u.is_admin
                        ? "admin"
                        : u.is_instructor
                          ? "instructor"
                          : "student"
                    }
                    onChange={async (e) => {
                      try {
                        await mutate(
                          `users/${u.id}/`,
                          { role: e.target.value },
                          "PATCH",
                        );
                        await r.reload();
                      } catch (e) {
                        setMessage(String(e));
                      }
                    }}
                  >
                    {["student", "instructor", "admin"].map((v) => (
                      <option key={v} value={v}>
                        {displayValue(v, locale)}
                      </option>
                    ))}
                  </select>
                  <Button
                    disabled={u.id === self.id || !u.is_active}
                    variant="ghost"
                    onClick={async () => {
                      if (confirm(t.delete + "?")) {
                        try {
                          await mutate(`users/${u.id}/`, {}, "DELETE");
                          await r.reload();
                        } catch (e) {
                          setMessage(String(e));
                        }
                      }
                    }}
                  >
                    {locale === "de" ? "Deaktivieren" : "Deactivate"}
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  );
}
