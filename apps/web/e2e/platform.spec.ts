import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
const password = process.env.DEMO_PASSWORD || "Local-Demo-Password-449!";
async function signIn(page: Page, role = "student", locale = "en") {
  await page.goto(`/${locale}/login`);
  await page
    .getByLabel(locale === "en" ? "Email" : "E-Mail", { exact: true })
    .fill(role + "@example.invalid");
  await page
    .getByLabel(locale === "en" ? "Password" : "Passwort", { exact: true })
    .fill(password);
  await page
    .getByRole("button", {
      name: locale === "en" ? "Sign in" : "Anmelden",
      exact: true,
    })
    .click();
  await expect(page).toHaveURL(new RegExp("/" + locale + "/courses$"));
}
test("public pages, invitation-only sign in, and legal content", async ({
  page,
}) => {
  await page.goto("/en");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(
    page.getByRole("heading", { name: "Learn. Apply. Collaborate." }),
  ).toBeVisible();
  await page.goto("/en/imprint");
  await expect(
    page.getByText("Votan Enterprise UG", { exact: false }),
  ).toBeVisible();
  await page.goto("/en/login");
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});
test("student learns, changes language, opens teams, and creates a support ticket", async ({
  page,
}) => {
  await signIn(page);
  await page.getByRole("link", { name: "Course overview" }).first().click();
  await page.getByRole("link", { name: "Introduction" }).click();
  await expect(
    page.getByRole("heading", { name: "Introduction", exact: true }),
  ).toBeVisible();
  if (
    await page
      .getByRole("button", { name: "Completed", exact: true })
      .isVisible()
  )
    await page.getByRole("button", { name: "Completed", exact: true }).click();
  await page.getByRole("button", { name: "Mark complete" }).click();
  await expect(
    page.getByRole("button", { name: "Completed", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("progressbar", { name: "Completed" }),
  ).toHaveAttribute("aria-valuenow", /^[1-9]/);
  await page.getByRole("button", { name: "Deutsch", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Introduction", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Abgeschlossen", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Support", exact: true })
    .first()
    .click();
  const subject = `Browser support test ${Date.now()}`;
  await page.getByLabel("Titel", { exact: true }).fill(subject);
  await page
    .getByLabel("Beschreibung", { exact: true })
    .fill("Please help with my course.");
  await page.getByRole("button", { name: "Speichern", exact: true }).click();
  await expect(
    page.getByRole("button", { name: new RegExp(subject) }),
  ).toBeVisible();
});
test("student uploads a notebook and receives an immutable accepted receipt", async ({
  page,
}) => {
  await signIn(page);
  await page.getByRole("link", { name: "Course overview" }).first().click();
  await page.getByRole("link", { name: "Notebook exercise" }).click();
  await page.getByLabel("Upload files", { exact: true }).setInputFiles({
    name: "browser.ipynb",
    mimeType: "application/json",
    buffer: Buffer.from(
      JSON.stringify({
        nbformat: 4,
        nbformat_minor: 5,
        metadata: {},
        cells: [
          {
            id: "code1",
            cell_type: "code",
            execution_count: 1,
            metadata: {},
            source: ["print(1)"],
            outputs: [{ output_type: "stream", name: "stdout", text: ["1\n"] }],
          },
        ],
      }),
    ),
  });
  await page.getByRole("button", { name: "Submit work", exact: true }).click();
  await expect(page.getByRole("link", { name: /#\d+ · / })).toBeVisible();
  await page.getByRole("link", { name: /#\d+ · / }).click();
  await expect(page.getByText("Accepted", { exact: true }).first()).toBeVisible(
    { timeout: 40000 },
  );
  await page.getByRole("button", { name: "Preview: browser.ipynb" }).click();
  await expect(page.getByText("print(1)", { exact: true })).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});
test("instructor authors reading content and records a grade with history", async ({
  page,
}) => {
  await signIn(page, "instructor");
  await page.getByRole("link", { name: "Course overview" }).first().click();
  await page.getByRole("link", { name: "Manage", exact: true }).click();
  await expect(page.getByRole("tab", { name: "Learning" })).toBeVisible();
  await page
    .getByRole("button", { name: "Manage", exact: true })
    .first()
    .click();
  await expect(
    page.getByRole("textbox", { name: "Instructions" }),
  ).toBeVisible();
  await page
    .getByRole("textbox", { name: "Instructions" })
    .fill("Updated course instructions from browser test.");
  const image = Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAEklEQVR4nGNkYPjPwMDAxAAGAAsfAQMU4wsAAAAAAElFTkSuQmCC",
    "base64",
  );
  const chooser = page.waitForEvent("filechooser");
  await page.getByRole("button", { name: "image", exact: true }).click();
  await (
    await chooser
  ).setFiles({
    name: "course-diagram.png",
    mimeType: "image/png",
    buffer: image,
  });
  await expect(page.locator(".ql-editor img")).toHaveAttribute(
    "src",
    /\/api\/v1\/assets\/.*\/inline\//,
    { timeout: 30000 },
  );
  await expect
    .poll(() =>
      page
        .locator(".ql-editor img")
        .evaluate((img) => (img as HTMLImageElement).naturalWidth),
    )
    .toBeGreaterThan(0);
  await page.getByRole("button", { name: "Save", exact: true }).first().click();
  await page
    .getByRole("link", { name: "Submissions", exact: true })
    .first()
    .click();
  await page.getByRole("link", { name: "Preview →" }).first().click();
  await page.getByLabel("Score", { exact: true }).fill("8");
  await page
    .getByLabel("Feedback", { exact: true })
    .fill("Reviewed exact accepted snapshot.");
  await page.getByRole("button", { name: "Grade", exact: true }).click();
  await expect(
    page
      .getByText("Reviewed exact accepted snapshot.", { exact: true })
      .first(),
  ).toBeVisible();
});
test("administrator has invitation and account controls", async ({ page }) => {
  await signIn(page, "admin");
  await page.getByRole("link", { name: "Administration", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Users", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Invite", exact: true }),
  ).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});
test("responsive sidebar works on a narrow screen", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await signIn(page);
  await page.getByRole("button", { name: "Toggle Sidebar" }).click();
  await expect(
    page.getByRole("link", { name: "Support", exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Support", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Support", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
});

test("private MP4 supports real browser playback", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Course overview" }).first().click();
  await page.getByRole("link", { name: /Video lesson/ }).click();
  const video = page.locator("video");
  await expect(video).toBeVisible();
  await expect
    .poll(() => video.evaluate((v) => (v as HTMLVideoElement).readyState))
    .toBeGreaterThanOrEqual(1);
  await video.evaluate(async (v) => {
    const media = v as HTMLVideoElement;
    media.muted = true;
    await media.play();
  });
  await expect
    .poll(() => video.evaluate((v) => (v as HTMLVideoElement).currentTime))
    .toBeGreaterThan(0.1);
});
