import { describe, it, expect } from "vitest";
import { sanitize } from "../modules/learning/content";
import { source } from "../modules/grading/notebook";
import { messages } from "@repo/i18n";
describe("Untrusted learning content", () => {
  it("removes executable markup while keeping author headings and formatting", () => {
    const clean = sanitize(
      '<h2>Assignment</h2><p><strong>Start</strong></p><img src=x onerror=alert(1)><script>alert(2)</script><iframe src="https://evil.invalid"></iframe><a href="javascript:alert(3)">click</a>',
    );
    expect(clean).toContain("<h2>Assignment</h2>");
    expect(clean).toContain("<strong>Start</strong>");
    expect(clean).not.toMatch(/onerror|<script|<iframe|javascript:/);
  });
  it("normalizes notebook text without interpreting HTML or running code", () => {
    expect(source(["<script>", "print(1)"])).toBe("<script>print(1)");
    expect(source(undefined)).toBe("");
  });
  it("ships the same interface keys in German and English", () => {
    expect(Object.keys(messages.de).sort()).toEqual(
      Object.keys(messages.en).sort(),
    );
  });
});
