/**
 * E2E tests for chat input handling
 * RED phase - Test-Driven Development
 *
 * Testing requirements from spec.md User Story 1:
 * - Shift+Enter creates new line (doesn't send)
 * - Enter sends message
 * - Textarea auto-resizes
 * - Keyboard navigation
 * - Real browser interaction
 */

import { test, expect } from "@playwright/test";

test.describe("Chat Input - Multiline Handling", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to chat interface
    await page.goto("/");

    // Wait for composer to load
    await page.waitForSelector("[data-testid='composer']");
  });

  test("should send message on Enter key", async ({ page }) => {
    const textarea = page.locator("textarea[placeholder*='Message']");

    // Type message
    await textarea.fill("Hello, Claude!");

    // Press Enter
    await textarea.press("Enter");

    // Message should appear in chat
    await expect(page.locator("text=Hello, Claude!")).toBeVisible();

    // Textarea should be cleared
    await expect(textarea).toHaveValue("");
  });

  test("should create new line on Shift+Enter", async ({ page }) => {
    const textarea = page.locator("textarea[placeholder*='Message']");

    // Type first line
    await textarea.fill("Line 1");

    // Press Shift+Enter
    await textarea.press("Shift+Enter");

    // Textarea should have newline
    await expect(textarea).toHaveValue("Line 1\n");

    // Type second line
    await textarea.type("Line 2");

    await expect(textarea).toHaveValue("Line 1\nLine 2");

    // Message should NOT have been sent yet
    await expect(page.locator("text=Line 1")).not.toBeVisible();
  });

  test("should send multiline message on Enter", async ({ page }) => {
    const textarea = page.locator("textarea[placeholder*='Message']");

    // Create multiline message
    await textarea.fill("Line 1");
    await textarea.press("Shift+Enter");
    await textarea.type("Line 2");
    await textarea.press("Shift+Enter");
    await textarea.type("Line 3");

    // Verify multiline content
    await expect(textarea).toHaveValue("Line 1\nLine 2\nLine 3");

    // Send with Enter
    await textarea.press("Enter");

    // All lines should appear in message
    const message = page.locator("[data-role='user']").first();
    await expect(message).toContainText("Line 1");
    await expect(message).toContainText("Line 2");
    await expect(message).toContainText("Line 3");
  });

  test("should auto-resize textarea as content grows", async ({ page }) => {
    const textarea = page.locator("textarea[placeholder*='Message']");

    // Get initial height
    const initialHeight = await textarea.evaluate(
      (el) => el.getBoundingClientRect().height
    );

    // Add multiple lines
    await textarea.fill("Line 1\nLine 2\nLine 3\nLine 4\nLine 5");

    // Get new height
    const newHeight = await textarea.evaluate(
      (el) => el.getBoundingClientRect().height
    );

    // Height should have increased
    expect(newHeight).toBeGreaterThan(initialHeight);
  });

  test("should respect max height and scroll when exceeded", async ({
    page,
  }) => {
    const textarea = page.locator("textarea[placeholder*='Message']");

    // Fill with many lines
    const manyLines = Array.from({ length: 20 }, (_, i) => `Line ${i + 1}`).join(
      "\n"
    );
    await textarea.fill(manyLines);

    // Should have overflow scroll
    const hasScroll = await textarea.evaluate((el) => {
      return el.scrollHeight > el.clientHeight;
    });

    expect(hasScroll).toBe(true);
  });

  test("should maintain cursor position after Shift+Enter", async ({
    page,
  }) => {
    const textarea = page.locator("textarea[placeholder*='Message']");

    // Type and add newline
    await textarea.fill("Line 1");
    await textarea.press("Shift+Enter");

    // Cursor should be on new line
    const cursorPosition = await textarea.evaluate((el: HTMLTextAreaElement) => {
      return el.selectionStart;
    });

    expect(cursorPosition).toBe(7); // "Line 1\n".length
  });

  test("should show keyboard hint for Shift+Enter", async ({ page }) => {
    // Hint should be visible
    await expect(
      page.locator("text=/Shift.*Enter.*new line/i")
    ).toBeVisible();
  });
});

test.describe("Chat Input - Send Button", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForSelector("[data-testid='composer']");
  });

  test("should disable send button when textarea is empty", async ({
    page,
  }) => {
    const sendButton = page.locator("button[aria-label*='Send']");

    // Should be disabled initially
    await expect(sendButton).toBeDisabled();
  });

  test("should enable send button when textarea has text", async ({ page }) => {
    const textarea = page.locator("textarea[placeholder*='Message']");
    const sendButton = page.locator("button[aria-label*='Send']");

    // Type text
    await textarea.fill("Test");

    // Should be enabled
    await expect(sendButton).toBeEnabled();
  });

  test("should disable send button after clearing textarea", async ({
    page,
  }) => {
    const textarea = page.locator("textarea[placeholder*='Message']");
    const sendButton = page.locator("button[aria-label*='Send']");

    // Type and clear
    await textarea.fill("Test");
    await textarea.clear();

    // Should be disabled again
    await expect(sendButton).toBeDisabled();
  });

  test("should send message when send button is clicked", async ({ page }) => {
    const textarea = page.locator("textarea[placeholder*='Message']");
    const sendButton = page.locator("button[aria-label*='Send']");

    // Type message
    await textarea.fill("Click to send");

    // Click send button
    await sendButton.click();

    // Message should appear
    await expect(page.locator("text=Click to send")).toBeVisible();

    // Textarea should be cleared
    await expect(textarea).toHaveValue("");
  });
});

test.describe("Chat Input - Loading State", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForSelector("[data-testid='composer']");
  });

  test("should disable input during response streaming", async ({ page }) => {
    const textarea = page.locator("textarea[placeholder*='Message']");
    const sendButton = page.locator("button[aria-label*='Send']");

    // Send message
    await textarea.fill("Test");
    await sendButton.click();

    // Should be disabled during streaming
    await expect(textarea).toBeDisabled();
    await expect(sendButton).toBeDisabled();

    // Wait for response to complete
    await page.waitForSelector("[data-testid='streaming-indicator']", {
      state: "detached",
      timeout: 10000,
    });

    // Should re-enable after streaming
    await expect(textarea).toBeEnabled();
    await expect(sendButton).toBeEnabled();
  });

  test("should show loading indicator during streaming", async ({ page }) => {
    const textarea = page.locator("textarea[placeholder*='Message']");

    // Send message
    await textarea.fill("Test");
    await textarea.press("Enter");

    // Loading indicator should appear
    await expect(page.locator("[data-testid='composer-loading']")).toBeVisible();
  });
});

test.describe("Chat Input - Draft Persistence", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForSelector("[data-testid='composer']");
  });

  test("should persist draft in localStorage", async ({ page }) => {
    const textarea = page.locator("textarea[placeholder*='Message']");

    // Type draft
    await textarea.fill("Draft message");

    // Wait for debounce
    await page.waitForTimeout(500);

    // Reload page
    await page.reload();
    await page.waitForSelector("[data-testid='composer']");

    // Draft should be restored
    await expect(textarea).toHaveValue("Draft message");
  });

  test("should clear draft after sending", async ({ page }) => {
    const textarea = page.locator("textarea[placeholder*='Message']");

    // Type and send
    await textarea.fill("Draft message");
    await textarea.press("Enter");

    // Reload page
    await page.reload();
    await page.waitForSelector("[data-testid='composer']");

    // Draft should be cleared
    await expect(textarea).toHaveValue("");
  });

  test("should maintain separate drafts per session", async ({ page }) => {
    // Session 1
    await page.goto("/?session=session-1");
    await page.waitForSelector("[data-testid='composer']");

    const textarea1 = page.locator("textarea[placeholder*='Message']");
    await textarea1.fill("Draft for session 1");

    // Session 2
    await page.goto("/?session=session-2");
    await page.waitForSelector("[data-testid='composer']");

    const textarea2 = page.locator("textarea[placeholder*='Message']");
    await textarea2.fill("Draft for session 2");

    // Back to session 1
    await page.goto("/?session=session-1");
    await page.waitForSelector("[data-testid='composer']");

    // Should restore session 1 draft
    await expect(textarea1).toHaveValue("Draft for session 1");
  });
});

test.describe("Chat Input - Accessibility", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForSelector("[data-testid='composer']");
  });

  test("should have proper ARIA labels", async ({ page }) => {
    const textarea = page.locator("textarea[placeholder*='Message']");
    const sendButton = page.locator("button[aria-label*='Send']");

    // Check ARIA attributes
    await expect(textarea).toHaveAttribute("aria-label", "Message input");
    await expect(sendButton).toHaveAttribute("aria-label");
  });

  test("should be keyboard navigable", async ({ page }) => {
    // Tab to textarea
    await page.keyboard.press("Tab");

    const textarea = page.locator("textarea[placeholder*='Message']");
    await expect(textarea).toBeFocused();

    // Tab to send button
    await page.keyboard.press("Tab");

    const sendButton = page.locator("button[aria-label*='Send']");
    await expect(sendButton).toBeFocused();
  });

  test("should announce disabled state to screen readers", async ({ page }) => {
    const textarea = page.locator("textarea[placeholder*='Message']");

    // Send message to trigger loading
    await textarea.fill("Test");
    await textarea.press("Enter");

    // Should have aria-disabled
    await expect(textarea).toHaveAttribute("aria-disabled", "true");
  });
});
