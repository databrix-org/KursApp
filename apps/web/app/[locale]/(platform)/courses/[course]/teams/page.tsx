import { Teams } from "@/modules/teams/screen";
export default async function Page({
  params,
}: {
  params: Promise<{ course: string }>;
}) {
  return <Teams course={Number((await params).course)} />;
}
