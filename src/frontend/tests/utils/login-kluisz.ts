import type { Page } from "@playwright/test";

export const loginKluisz = async (page: Page) => {
  await page.goto("/");
  await page.getByPlaceholder("Username").fill("kluisz");
  await page.getByPlaceholder("Password").fill("kluisz");
  await page.getByRole("button", { name: "Sign In" }).click();
};
