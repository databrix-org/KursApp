import { LessonView } from "@/modules/learning/lesson";
export default async function Page({
  params,
}: {
  params: Promise<{ course: string; lesson: string }>;
}) {
  const p = await params;
  return <LessonView course={Number(p.course)} id={Number(p.lesson)} />;
}
