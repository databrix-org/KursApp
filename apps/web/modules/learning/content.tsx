"use client";
import { useEffect, useRef, useState } from "react";
import DOMPurify from "dompurify";
import { useText } from "@/lib/hooks";
export function sanitize(html: string) {
  return DOMPurify.sanitize(html, {
    USE_PROFILES: { html: true },
    FORBID_TAGS: ["iframe", "style", "form", "input", "video", "audio"],
    FORBID_ATTR: ["style"],
  });
}
export function Content({ html }: { html: string }) {
  const root = useRef<HTMLDivElement>(null);
  const [headings, setHeadings] = useState<
      { id: string; text: string; level: string }[]
    >([]),
    [safe, setSafe] = useState(""),
    [active, setActive] = useState("");
  const t = useText();
  useEffect(() => {
    setSafe(sanitize(html));
  }, [html]);
  useEffect(() => {
    if (!root.current) return;
    const list = Array.from(root.current.querySelectorAll("h2,h3"));
    list.forEach((h, i) => {
      h.id = "section-" + i;
    });
    setHeadings(
      list.map((h) => ({
        id: h.id,
        text: h.textContent || "",
        level: h.tagName,
      })),
    );
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) setActive(e.target.id);
        });
      },
      { rootMargin: "-80px 0px -60% 0px" },
    );
    list.forEach((h) => observer.observe(h));
    return () => observer.disconnect();
  }, [safe]);
  return (
    <div className="grid gap-10 xl:grid-cols-[minmax(0,1fr)_180px]">
      <div
        ref={root}
        className="lesson-content min-w-0"
        dangerouslySetInnerHTML={{ __html: safe }}
      />
      <aside className="hidden xl:block">
        <nav aria-label={t.onThisPage} className="sticky top-24">
          <h2 className="mb-4 text-sm font-semibold">{t.onThisPage}</h2>
          <ul className="space-y-3 border-l text-sm text-muted-foreground">
            {headings.map((h) => (
              <li key={h.id} className={h.level === "H3" ? "pl-7" : "pl-4"}>
                <a
                  className="aria-[current=location]:font-semibold aria-[current=location]:text-primary"
                  href={"#" + h.id}
                  aria-current={active === h.id ? "location" : undefined}
                >
                  {h.text}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </aside>
    </div>
  );
}
