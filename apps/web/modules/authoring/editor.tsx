"use client";
import { useEffect, useRef, useState } from "react";
import type Quill from "quill";
import "quill/dist/quill.snow.css";
import { Notice } from "@/components/common";
import { sanitize } from "@/modules/learning/content";
export function RichEditor({
  initial,
  onChange,
  label,
  uploadImage,
}: {
  initial: string;
  onChange: (value: string) => void;
  label: string;
  uploadImage: (file: File) => Promise<string>;
}) {
  const root = useRef<HTMLDivElement>(null),
    editor = useRef<Quill | null>(null),
    change = useRef(onChange);
  const [message, setMessage] = useState(""),
    imageUpload = useRef(uploadImage);
  imageUpload.current = uploadImage;
  change.current = onChange;
  useEffect(() => {
    const host = root.current;
    let disposed = false;
    let container: HTMLDivElement | undefined;
    import("quill").then(({ default: Quill }) => {
      if (disposed || !root.current) return;
      container = document.createElement("div");
      root.current.append(container);
      const q = new Quill(container, {
        theme: "snow",
        modules: {
          toolbar: {
            container: [
              [{ header: [1, 2, 3, false] }],
              ["bold", "italic", "underline", "strike"],
              [{ list: "ordered" }, { list: "bullet" }],
              ["blockquote", "code-block", "link", "image"],
              [{ script: "sub" }, { script: "super" }],
              [{ indent: "-1" }, { indent: "+1" }],
              ["clean"],
            ],
            handlers: {
              image: () => {
                const picker = document.createElement("input");
                picker.type = "file";
                picker.accept = "image/png,image/jpeg";
                const position =
                  q.getSelection(true)?.index ?? q.getLength() - 1;
                picker.onchange = async () => {
                  const file = picker.files?.[0];
                  if (!file) return;
                  setMessage("Uploading / Wird hochgeladen…");
                  try {
                    const url = await imageUpload.current(file);
                    q.insertEmbed(position, "image", url, "user");
                    q.formatText(position, 1, "alt", file.name, "user");
                    setMessage("");
                  } catch (e) {
                    setMessage(
                      e instanceof Error ? e.message : "Image upload failed",
                    );
                  }
                };
                picker.click();
              },
            },
          },
        },
      });
      editor.current = q;
      q.root.setAttribute("aria-label", label);
      q.root.setAttribute("role", "textbox");
      q.root.setAttribute("aria-multiline", "true");
      host
        ?.querySelectorAll<HTMLButtonElement>(".ql-toolbar button")
        .forEach((button) =>
          button.setAttribute(
            "aria-label",
            button.className.replace("ql-", ""),
          ),
        );
      q.clipboard.dangerouslyPasteHTML(sanitize(initial));
      q.on("text-change", () => change.current(q.getSemanticHTML()));
    });
    return () => {
      disposed = true;
      editor.current = null;
      if (host) host.innerHTML = "";
    };
  }, [initial, label]);
  return (
    <div>
      <div className="rounded-md border bg-background" ref={root} />
      <Notice message={message} />
    </div>
  );
}
