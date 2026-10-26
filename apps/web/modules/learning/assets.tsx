"use client";
import { useCallback, useState } from "react";
import { api, type Asset } from "@repo/api-client";
import { Button } from "@repo/design-system/components/ui/button";
import { PrivateVideo } from "@repo/design-system/components/media";
import { useText, useResource } from "@/lib/hooks";
import { Notice } from "@/components/common";
export async function assetURL(id: string) {
  return (await api<{ url: string }>(`assets/${id}/download/`)).url;
}
function Video({ asset }: { asset: Asset }) {
  const resolve = useCallback(() => assetURL(asset.id), [asset.id]),
    t = useText();
  return (
    <PrivateVideo resolve={resolve} title={asset.name} retryLabel={t.retry} />
  );
}
export function AssetList({
  path,
  video = false,
}: {
  path: string;
  video?: boolean;
}) {
  const r = useResource<Asset[]>(path),
    t = useText(),
    [message, setMessage] = useState("");
  return (
    <div className="space-y-4">
      <Notice message={r.error || message} />
      {r.data
        ?.filter((a) => a.status === "accepted")
        .map((a) =>
          video && a.content_type.startsWith("video/") ? (
            <Video key={a.id} asset={a} />
          ) : (
            <div
              className="flex items-center justify-between gap-3 rounded-md border p-4"
              key={a.id}
            >
              <span className="truncate">{a.name}</span>
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  try {
                    window.location.assign(await assetURL(a.id));
                  } catch (e) {
                    setMessage(String(e));
                  }
                }}
              >
                {t.download}
              </Button>
            </div>
          ),
        )}
    </div>
  );
}
