"use client";
import Link from "next/link";
import { useLocale } from "next-intl";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { mutate, type Session } from "@repo/api-client";
import { Button } from "@repo/design-system/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@repo/design-system/components/ui/card";
import { Field, Form, string } from "@/components/forms";
import { useText, useResource } from "@/lib/hooks";
import { Notice, PageTitle } from "@/components/common";
import { useUser } from "@/components/providers";
export function Login() {
  const t = useText(),
    locale = useLocale(),
    router = useRouter();
  const session = useResource<Session>("session/");
  return (
    <main className="mx-auto max-w-md px-6 py-20">
      <Link href={`/${locale}`} className="text-2xl font-bold">
        databrix.
      </Link>
      <Card className="mt-10">
        <CardHeader>
          <CardTitle>
            <h1>{t.login}</h1>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Form
            label={t.login}
            onSubmit={async (data) => {
              await mutate("session/change/", {
                email: string(data, "email"),
                password: string(data, "password"),
              });
              router.push(`/${locale}/courses`);
              router.refresh();
            }}
          >
            <Field
              name="email"
              type="email"
              label={t.email}
              required
              autoComplete="email"
            />
            <Field
              name="password"
              type="password"
              label={t.password}
              required
              autoComplete="current-password"
            />
          </Form>
          {session.data?.sso_enabled && (
            <Button asChild variant="outline" className="mt-5 w-full">
              <button
                type="button"
                onClick={() =>
                  window.location.assign(
                    new URL(
                      "/auth/institutional/login/",
                      window.location.origin,
                    ).href,
                  )
                }
              >
                {t.institutional}
              </button>
            </Button>
          )}
          <Link
            className="mt-6 block text-sm underline"
            href={`/${locale}/account/reset-password`}
          >
            {t.reset}
          </Link>
        </CardContent>
      </Card>
    </main>
  );
}
export function Account({ mode }: { mode: string }) {
  const t = useText(),
    locale = useLocale(),
    params = useSearchParams();
  const [done, setDone] = useState("");
  return (
    <main className="mx-auto max-w-md px-6 py-16">
      <Link href={`/${locale}/login`}>← {t.login}</Link>
      <h1 className="my-8 text-3xl font-semibold">
        {mode === "invitation"
          ? t.accept
          : mode === "verify-email"
            ? t.verify
            : t.reset}
      </h1>
      {done ? (
        <Notice message={done} />
      ) : (
        <Form
          onSubmit={async (data) => {
            if (mode === "invitation") {
              await mutate("invitations/accept/", {
                token: params.get("token"),
                first_name: string(data, "first_name"),
                last_name: string(data, "last_name"),
                password: string(data, "password"),
              });
              setDone(
                locale === "de"
                  ? "Einladung angenommen. Bitte bestätige deine E-Mail, bevor du dich anmeldest."
                  : "Invitation accepted. Please verify your email before signing in.",
              );
            } else if (mode === "verify-email") {
              await mutate("session/verify/", { key: params.get("key") });
              setDone(
                locale === "de"
                  ? "E-Mail bestätigt. Du kannst dich anmelden."
                  : "Email verified. You can sign in.",
              );
            } else {
              await mutate(
                params.has("key") ? "session/reset-confirm/" : "session/reset/",
                params.has("key")
                  ? {
                      key: params.get("key"),
                      password: string(data, "password"),
                    }
                  : { email: string(data, "email") },
              );
              setDone(
                locale === "de"
                  ? "Anfrage verarbeitet. Prüfe dein Postfach oder melde dich mit deinem neuen Passwort an."
                  : "Request processed. Check your inbox or sign in with your new password.",
              );
            }
          }}
        >
          {mode === "invitation" && (
            <>
              <Field name="first_name" label={t.firstName} />
              <Field name="last_name" label={t.lastName} />
            </>
          )}
          {mode !== "verify-email" &&
            (mode === "invitation" || params.has("key") ? (
              <Field
                name="password"
                label={t.password}
                type="password"
                minLength={12}
                autoComplete="new-password"
                required
              />
            ) : (
              <Field name="email" label={t.email} type="email" required />
            ))}
        </Form>
      )}
    </main>
  );
}
export function Profile() {
  const t = useText(),
    user = useUser(),
    [message, setMessage] = useState("");
  return (
    <div className="max-w-xl">
      <PageTitle title={t.profile} />
      <p className="mb-8 text-muted-foreground">{user.email}</p>
      <Form
        onSubmit={async (d) => {
          await mutate(
            "session/change/",
            {
              first_name: string(d, "first_name"),
              last_name: string(d, "last_name"),
            },
            "PATCH",
          );
          setMessage(t.save + " ✓");
        }}
      >
        <Field
          label={t.firstName}
          name="first_name"
          defaultValue={user.first_name}
          required
        />
        <Field
          label={t.lastName}
          name="last_name"
          defaultValue={user.last_name}
          required
        />
      </Form>
      <Notice message={message} />
      <Button variant="outline" className="mt-6" asChild>
        <button
          type="button"
          onClick={() =>
            window.location.assign(
              new URL("/auth/institutional/login/", window.location.origin)
                .href,
            )
          }
        >
          {t.institutional}
        </button>
      </Button>
    </div>
  );
}
