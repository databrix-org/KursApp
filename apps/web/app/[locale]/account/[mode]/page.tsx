import { Suspense } from "react";
import { Account } from "@/modules/auth/screens";
export default async function Page({
  params,
}: {
  params: Promise<{ mode: string }>;
}) {
  const { mode } = await params;
  return (
    <Suspense>
      <Account mode={mode} />
    </Suspense>
  );
}
