"use client";
import { useLocale } from "next-intl";
import { useState } from "react";
import { type Group, type Course, mutate } from "@repo/api-client";
import { Button } from "@repo/design-system/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@repo/design-system/components/ui/card";
import { PageTitle, Notice, Loading, Failure } from "@/components/common";
import { Field, Form, string } from "@/components/forms";
import { useUser } from "@/components/providers";
import { useResource, useText } from "@/lib/hooks";
export function Teams({ course }: { course: number }) {
  const t = useText(),
    locale = useLocale(),
    user = useUser(),
    r = useResource<Group[]>("groups/"),
    c = useResource<Course>(`courses/${course}/`),
    [message, setMessage] = useState("");
  async function act(id: number, action: string, user_id?: number) {
    try {
      await mutate(`groups/${id}/${action}/`, user_id ? { user_id } : {});
      await r.reload();
    } catch (e) {
      setMessage(String(e));
    }
  }
  return (
    <>
      <PageTitle title={t.teams} description={c.data?.title}>
        {c.data?.capabilities.manage && (
          <Button
            onClick={async () => {
              try {
                await mutate("groups/", { course });
                await r.reload();
              } catch (e) {
                setMessage(String(e));
              }
            }}
          >
            {t.create}
          </Button>
        )}
      </PageTitle>
      <Notice message={message} />
      {r.error ? (
        <Failure error={r.error} retry={r.reload} />
      ) : !r.data ? (
        <Loading />
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {r.data
            .filter((g) => g.course === course)
            .map((g) => (
              <Card key={g.id}>
                <CardHeader>
                  <CardTitle>
                    {t.teams} {g.group_number}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="mb-4 space-y-3">
                    {g.members.map((m) => (
                      <li
                        key={m.id}
                        className="flex items-center justify-between"
                      >
                        {m.first_name} {m.last_name}
                        {c.data?.capabilities.manage && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => act(g.id, "leave", m.id)}
                          >
                            ×
                          </Button>
                        )}
                      </li>
                    ))}
                  </ul>
                  {!g.members.length && (
                    <p className="text-muted-foreground">{t.noRecords}</p>
                  )}
                  {c.data?.capabilities.manage && (
                    <Form
                      key={g.members.length}
                      onSubmit={async (d) => {
                        await mutate(
                          `groups/${g.id}/`,
                          { lab_url: string(d, "lab_url") },
                          "PATCH",
                        );
                        if (string(d, "user_id"))
                          await mutate(`groups/${g.id}/join/`, {
                            user_id: Number(string(d, "user_id")),
                          });
                        await r.reload();
                      }}
                    >
                      <Field
                        label={t.lab + " URL"}
                        name="lab_url"
                        defaultValue={g.lab_url}
                      />
                      <Field
                        label={
                          locale === "de"
                            ? "Benutzer-ID hinzufügen"
                            : "Add user ID"
                        }
                        name="user_id"
                        type="number"
                      />
                    </Form>
                  )}
                </CardContent>
                <CardFooter className="gap-3">
                  <Button
                    variant="outline"
                    onClick={() =>
                      act(
                        g.id,
                        g.members.some((m) => m.id === user.id)
                          ? "leave"
                          : "join",
                      )
                    }
                  >
                    {g.members.some((m) => m.id === user.id) ? t.leave : t.join}
                  </Button>
                  {c.data?.capabilities.manage && (
                    <Button
                      variant="ghost"
                      onClick={async () => {
                        if (!confirm(t.delete + "?")) return;
                        try {
                          await mutate(`groups/${g.id}/`, {}, "DELETE");
                          await r.reload();
                        } catch (e) {
                          setMessage(String(e));
                        }
                      }}
                    >
                      {t.delete}
                    </Button>
                  )}
                </CardFooter>
              </Card>
            ))}
        </div>
      )}
    </>
  );
}
