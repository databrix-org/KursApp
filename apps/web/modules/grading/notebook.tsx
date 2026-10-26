"use client";
import { useEffect, useState } from "react";
import { assetURL } from "@/modules/learning/assets";
import { marked } from "marked";
import { sanitize } from "@/modules/learning/content";
import { Notice } from "@/components/common";
export type Cell = {
  cell_type: string;
  source: string | string[];
  outputs?: {
    text?: string | string[];
    data?: Record<string, string | string[]>;
    traceback?: string[];
  }[];
};
export type Notebook = { cells: Cell[] };
export function source(v: string | string[] | undefined) {
  return Array.isArray(v) ? v.join("") : v || "";
}
export async function readNotebook(id: string): Promise<Notebook> {
  const r = await fetch(await assetURL(id));
  if (!r.ok) throw new Error("Preview unavailable");
  if (Number(r.headers.get("Content-Length")) > 64 * 1024 * 1024)
    throw new Error("Notebook too large for preview");
  const data = await r.json();
  if (!Array.isArray(data.cells)) throw new Error("Invalid notebook");
  return data;
}
function MarkdownCell({ text }: { text: string }) {
  const [html, setHtml] = useState("");
  useEffect(
    () => setHtml(sanitize(marked.parse(text, { async: false }))),
    [text],
  );
  return (
    <div
      className="lesson-content p-4"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
export function NotebookPreview({
  id,
  compare,
}: {
  id: string;
  compare?: string;
}) {
  const [data, setData] = useState<Notebook>(),
    [ref, setRef] = useState<Notebook>(),
    [error, setError] = useState("");
  useEffect(() => {
    setError("");
    setData(undefined);
    setRef(undefined);
    void readNotebook(id)
      .then(setData)
      .catch((e) => setError(String(e)));
    if (compare)
      void readNotebook(compare)
        .then(setRef)
        .catch((e) => setError(String(e)));
  }, [id, compare]);
  return (
    <div className="my-5 space-y-4">
      <Notice message={error} />
      {data?.cells.map((cell, i) => {
        const original = ref?.cells[i];
        const differs =
          !!ref && source(original?.source) !== source(cell.source);
        return (
          <div
            key={i}
            className={
              "overflow-hidden rounded-md border " +
              (differs ? "border-amber-500" : "")
            }
          >
            <div className="border-b bg-muted px-4 py-2 font-mono text-xs">
              {i + 1} · {cell.cell_type}
              {differs ? " · Δ" : ""}
            </div>
            <div className={compare ? "grid md:grid-cols-2" : ""}>
              <div>
                {cell.cell_type === "markdown" ? (
                  <MarkdownCell text={source(cell.source)} />
                ) : (
                  <pre className="max-h-96 overflow-auto whitespace-pre-wrap p-4 text-sm">
                    {source(cell.source)}
                  </pre>
                )}
              </div>
              {compare && (
                <pre className="max-h-96 overflow-auto whitespace-pre-wrap border-l bg-muted/40 p-4 text-sm">
                  {source(original?.source)}
                </pre>
              )}
            </div>
            {cell.outputs?.map((o, j) => (
              <pre
                key={j}
                className="max-h-80 overflow-auto whitespace-pre-wrap border-t bg-muted/20 p-4 text-xs"
              >
                {source(o.text) ||
                  source(o.data?.["text/plain"]) ||
                  o.traceback?.join("\n") ||
                  "[Rich output omitted from safe preview]"}
              </pre>
            ))}
          </div>
        );
      })}
    </div>
  );
}
