"use client";
import { displayValue } from "@repo/i18n";
import { useState } from "react";
import { useLocale } from "next-intl";
import { type Ticket, type Course, mutate } from "@repo/api-client";
import { Button } from "@repo/design-system/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@repo/design-system/components/ui/card";
import { Textarea } from "@repo/design-system/components/ui/textarea";
import { Label } from "@repo/design-system/components/ui/label";
import { PageTitle, Notice } from "@/components/common";
import { Field, Form, string } from "@/components/forms";
import { AssetUpload } from "@/modules/authoring/assets";
import { AssetList } from "@/modules/learning/assets";
import { useText, useResource } from "@/lib/hooks";
import { useUser } from "@/components/providers";
export function Support() {
  const t = useText(),
    locale = useLocale(),
    user = useUser(),
    r = useResource<Ticket[]>("tickets/"),
    courses = useResource<Course[]>("courses/"),
    [selected, setSelected] = useState<number>(),
    [message, setMessage] = useState("");
  return (
    <>
      <PageTitle title={t.support} />
      <Notice message={message || r.error} />
      <Card className="mb-10 max-w-2xl">
        <CardHeader>
          <CardTitle>{t.create}</CardTitle>
        </CardHeader>
        <CardContent>
          <Form
            onSubmit={async (d) => {
              const ticket = await mutate<Ticket>("tickets/", {
                subject: string(d, "subject"),
                description: string(d, "description"),
                course: string(d, "course")
                  ? Number(string(d, "course"))
                  : null,
              });
              setSelected(ticket.id);
              await r.reload();
            }}
          >
            <Field label={t.title} name="subject" required />
            <Label htmlFor="ticket-description">{t.description}</Label>
            <Textarea id="ticket-description" name="description" required />
            <label className="block text-sm">
              {t.courses}
              <select
                name="course"
                className="mt-2 w-full rounded-md border bg-background p-2"
              >
                <option value="">—</option>
                {courses.data
                  ?.filter((c) => c.enrolled || c.capabilities.teach)
                  .map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.title}
                    </option>
                  ))}
              </select>
            </label>
          </Form>
        </CardContent>
      </Card>
      <div className="space-y-5">
        {r.data?.map((ticket) => (
          <Card key={ticket.id}>
            <CardHeader>
              <CardTitle>
                <Button
                  variant="link"
                  className="p-0 text-lg"
                  onClick={() =>
                    setSelected(selected === ticket.id ? undefined : ticket.id)
                  }
                >
                  #{ticket.id} · {ticket.subject}
                </Button>
                <span className="ml-4 text-sm font-normal text-muted-foreground">
                  {displayValue(ticket.status, locale)}
                </span>
              </CardTitle>
            </CardHeader>
            {selected === ticket.id && (
              <CardContent className="space-y-5">
                <p className="whitespace-pre-wrap">{ticket.description}</p>
                <p className="whitespace-pre-wrap text-muted-foreground">
                  {ticket.resolution_notes}
                </p>
                <AssetList path={`assets/?ticket=${ticket.id}`} />
                {ticket.user === user.id && (
                  <AssetUpload ticket={ticket.id} category="support" />
                )}
                {(user.is_admin || user.is_instructor) && (
                  <Form
                    onSubmit={async (d) => {
                      await mutate(
                        `tickets/${ticket.id}/`,
                        {
                          status: string(d, "status"),
                          resolution_notes: string(d, "notes"),
                          assigned_to: string(d, "assigned_to")
                            ? Number(string(d, "assigned_to"))
                            : null,
                        },
                        "PATCH",
                      );
                      await r.reload();
                    }}
                  >
                    <label className="block text-sm">
                      {t.status}
                      <select
                        name="status"
                        defaultValue={ticket.status}
                        className="mt-2 w-full rounded-md border bg-background p-2"
                      >
                        {["open", "in_progress", "closed"].map((s) => (
                          <option key={s} value={s}>
                            {displayValue(s, locale)}
                          </option>
                        ))}
                      </select>
                    </label>
                    <Field
                      label={
                        locale === "de"
                          ? "Zuständig: Benutzer-ID"
                          : "Assigned user ID"
                      }
                      name="assigned_to"
                      type="number"
                      defaultValue={ticket.assigned_to || ""}
                    />
                    <Label htmlFor={"notes-" + ticket.id}>{t.feedback}</Label>
                    <Textarea
                      id={"notes-" + ticket.id}
                      name="notes"
                      defaultValue={ticket.resolution_notes || ""}
                    />
                  </Form>
                )}
                {user.is_admin && (
                  <Button
                    variant="destructive"
                    onClick={async () => {
                      if (confirm(t.delete + "?")) {
                        try {
                          await mutate(`tickets/${ticket.id}/`, {}, "DELETE");
                          await r.reload();
                        } catch (e) {
                          setMessage(String(e));
                        }
                      }
                    }}
                  >
                    {t.delete}
                  </Button>
                )}
              </CardContent>
            )}
          </Card>
        ))}
      </div>
    </>
  );
}
