import "server-only";
import { cookies } from "next/headers";
import type { Session } from "@repo/api-client";
export async function getSession(): Promise<Session> {
  const jar = await cookies();
  const origin = new URL(process.env.PUBLIC_ORIGIN || "http://localhost:8080");
  const response = await fetch(
    `${process.env.BACKEND_URL || "http://127.0.0.1:8000"}/api/v1/session/`,
    {
      headers: {
        Cookie: jar.toString(),
        Host: origin.host,
        "X-Forwarded-Proto": origin.protocol === "https:" ? "https" : "http",
      },
      cache: "no-store",
    },
  );
  if (!response.ok) throw new Error("Learning service unavailable");
  return response.json();
}
