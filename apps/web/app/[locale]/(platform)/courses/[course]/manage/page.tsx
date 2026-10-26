import { Authoring } from "@/modules/authoring/screen";
export default async function Page({
  params,
}: {
  params: Promise<{ course: string }>;
}) {
  return <Authoring id={Number((await params).course)} />;
}
