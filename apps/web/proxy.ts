import { NextRequest, NextResponse } from "next/server";
export function proxy(request: NextRequest) {
  const headers = new Headers(request.headers);
  headers.set(
    "x-databrix-locale",
    request.nextUrl.pathname.split("/")[1] === "en" ? "en" : "de",
  );
  return NextResponse.next({ request: { headers } });
}
export const config = { matcher: ["/((?!api|auth|_next|favicon.ico).*)"] };
