import { Overview } from "@/modules/courses/overview";
export default async function Page({
  params,
}: {
  params: Promise<{ course: string }>;
}) {
  return <Overview id={Number((await params).course)} />;
}
