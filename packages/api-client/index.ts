import createClient from "openapi-fetch";
import type { paths } from "./schema";
import type { components } from "./schema";
export type Course = Omit<
  Required<components["schemas"]["Course"]>,
  "capabilities" | "enrolled"
> & { capabilities: { teach: boolean; manage: boolean }; enrolled: boolean };
export type Module = Required<components["schemas"]["Module"]>;
export type Lesson = Omit<
  Required<components["schemas"]["Lesson"]>,
  "completed"
> & { completed: boolean };
export type Submission = Required<components["schemas"]["Submission"]>;
export type Asset = Required<components["schemas"]["Asset"]>;
export type Ticket = Required<components["schemas"]["Ticket"]>;
export type Group = Omit<
  Required<components["schemas"]["Group"]>,
  "members"
> & { members: { id: number; first_name: string; last_name: string }[] };
export type User = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_admin: boolean;
  is_instructor: boolean;
  is_active?: boolean;
};
export type Session = { user: User | null; sso_enabled: boolean };
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
function csrf() {
  if (typeof document === "undefined") return "";
  return decodeURIComponent(
    document.cookie
      .split("; ")
      .find((x) => x.startsWith("csrftoken="))
      ?.split("=")
      .slice(1)
      .join("=") || "",
  );
}
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  if (
    init.method &&
    !["GET", "HEAD"].includes(init.method.toUpperCase()) &&
    !csrf()
  )
    await fetch("/api/v1/session/", {
      credentials: "same-origin",
      cache: "no-store",
    });
  const response = await fetch(`/api/v1/${path.replace(/^\//, "")}`, {
    ...init,
    credentials: "same-origin",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrf(),
      ...init.headers,
    },
  });
  const data = await response
    .json()
    .catch(() => ({ detail: "Service unavailable" }));
  if (!response.ok)
    throw new ApiError(
      response.status,
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail || data),
    );
  return data;
}
export function mutate<T>(path: string, body: unknown = {}, method = "POST") {
  return api<T>(path, { method, body: JSON.stringify(body) });
}
export type UploadGrant = {
  asset_id: string;
  url: string;
  content_type: string;
};
export async function putFile(grant: UploadGrant, file: File) {
  const r = await fetch(grant.url, {
    method: "PUT",
    headers: { "Content-Type": grant.content_type },
    body: file,
  });
  if (!r.ok) throw new Error("Upload failed; your work was not accepted");
}

/** Generated route/method/body contracts for new integrations. Browser helpers above share its schemas. */
export const client = createClient<paths>({
  baseUrl: "",
  credentials: "same-origin",
  cache:"no-store",
});
client.use({
  async onRequest({ request }) {
    if (!["GET", "HEAD", "OPTIONS"].includes(request.method)) {
      if (!csrf()) await api("session/");
      request.headers.set("X-CSRFToken", csrf());
    }
    return request;
  },
});
export type { paths, components } from "./schema";
