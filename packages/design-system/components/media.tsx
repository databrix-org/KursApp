"use client";
import { useEffect, useRef, useState } from "react";
import { Button } from "./ui/button";
import { Alert, AlertDescription } from "./ui/alert";
export function PrivateVideo({
  resolve,
  title,
  retryLabel,
}: {
  resolve: () => Promise<string>;
  title: string;
  retryLabel: string;
}) {
  const ref = useRef<HTMLVideoElement>(null),
    [url, setUrl] = useState(""),
    [failed, setFailed] = useState(false);
  async function refresh() {
    const time = ref.current?.currentTime || 0;
    try {
      setUrl(await resolve());
      setFailed(false);
      if (ref.current)
        ref.current.onloadedmetadata = () => {
          if (ref.current) ref.current.currentTime = time;
        };
    } catch {
      setFailed(true);
    }
  }
  useEffect(() => {
    void refresh();
  }, [resolve]); // Signed URL renewal retains the playback position.
  return (
    <div className="overflow-hidden rounded-xl border bg-black">
      <video
        ref={ref}
        src={url || undefined}
        controls
        playsInline
        preload="metadata"
        aria-label={title}
        className="aspect-video w-full"
        onError={() => setFailed(true)}
      />
      {failed && (
        <Alert>
          <AlertDescription>
            <Button onClick={refresh} variant="outline">
              {retryLabel}
            </Button>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
