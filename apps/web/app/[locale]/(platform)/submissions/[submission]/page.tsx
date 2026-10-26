import { SubmissionDetail } from "@/modules/submissions/screens";
export default async function Page({
  params,
}: {
  params: Promise<{ submission: string }>;
}) {
  return <SubmissionDetail id={Number((await params).submission)} />;
}
