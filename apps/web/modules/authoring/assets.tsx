"use client";
import { displayValue } from "@repo/i18n";
import { useState } from "react";
import { useLocale } from "next-intl";
import { api, mutate, putFile, type Asset } from "@repo/api-client";
import { Button } from "@repo/design-system/components/ui/button";
import { Input } from "@repo/design-system/components/ui/input";
import { Label } from "@repo/design-system/components/ui/label";
import { useText, useResource } from "@/lib/hooks";
import { Notice } from "@/components/common";
export function AssetUpload({
  course,
  lesson,
  ticket,
  category = "course",
}: {
  course?: number;
  lesson?: number;
  ticket?: number;
  category?: "course" | "assessment" | "support";
}) {
  const t = useText(),
    locale = useLocale(),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  const path = lesson
      ? `assets/?lesson=${lesson}`
      : ticket
        ? `assets/?ticket=${ticket}`
        : `assets/?course=${course}`,
    r = useResource<Asset[]>(path);
  async function upload(file: File) {
    setBusy(true);
    try {
      const x = await mutate<{
        asset: Asset;
        url: string;
        content_type: string;
      }>("assets/initiate/", {
        category,
        course,
        lesson,
        ticket,
        name: file.name,
        size: file.size,
      });
      await putFile(
        { asset_id: x.asset.id, url: x.url, content_type: x.content_type },
        file,
      );
      await mutate(`assets/${x.asset.id}/finalize/`);
      setMessage(
        locale === "de"
          ? "Hochgeladen. Prüfung läuft."
          : "Uploaded. Verification is pending.",
      );
      await r.reload();
    } catch (e) {
      setMessage(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="space-y-3">
      <Label htmlFor={"asset-" + category}>
        {category === "assessment" ? t.reference : t.upload}
      </Label>
      <Input
        id={"asset-" + category}
        type="file"
        accept={
          category === "assessment"
            ? ".ipynb"
            : category === "support"
              ? ".png,.jpg,.jpeg"
              : undefined
        }
        disabled={busy}
        onChange={(e) => {
          if (e.target.files?.[0]) void upload(e.target.files[0]);
        }}
      />
      <Notice message={message || r.error} />
      <Button variant="ghost" size="sm" onClick={r.reload}>
        {t.retry}
      </Button>
      {r.data
        ?.filter((a) => a.category === category)
        .map((a) => (
          <div
            className="flex flex-wrap items-center justify-between gap-2 border-b py-2 text-sm"
            key={a.id}
          >
            <span>
              {a.name} · {displayValue(a.status, locale)}
            </span>
            {a.status === "accepted" && category !== "support" && (
              <Button
                variant="ghost"
                size="sm"
                onClick={async () => {
                  try {
                    await mutate(`assets/${a.id}/retire/`);
                    await r.reload();
                  } catch (e) {
                    setMessage(String(e));
                  }
                }}
              >
                {t.delete}
              </Button>
            )}
          </div>
        ))}
    </div>
  );
}

export async function uploadInlineImage(
  course: number,
  lesson: number,
  file: File,
) {
  if (
    !["image/png", "image/jpeg"].includes(file.type) ||
    file.size > 32 * 1024 * 1024
  )
    throw new Error("Choose a PNG/JPEG image up to 32 MiB");
  const result = await mutate<{
    asset: Asset;
    url: string;
    content_type: string;
  }>("assets/initiate/", {
    category: "course",
    course,
    lesson,
    name: file.name,
    size: file.size,
  });
  await putFile(
    {
      asset_id: result.asset.id,
      url: result.url,
      content_type: result.content_type,
    },
    file,
  );
  await mutate(`assets/${result.asset.id}/finalize/`);
  for (let i = 0; i < 60; i++) {
    const asset = await api<Asset>(`assets/${result.asset.id}/`);
    if (asset.status === "accepted")
      return `/api/v1/assets/${asset.id}/inline/`;
    if (asset.status === "rejected") throw new Error("Image validation failed");
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  throw new Error(
    "Image verification is delayed; retry after checking your course assets",
  );
}
