import { test, expect } from '@playwright/test';
import { AuthHelper } from '../utils/auth.helper';
import { ApiHelper } from '../utils/api.helper';
import { TestRecipient, TestDonor, TestDonation } from '../utils/fixtures';

/**
 * Distribution Workflow E2E Tests
 * Tests: create recipient → create distribution → assign inventory → complete → verify inventory update
 */

test.describe('Distribution Workflow', () => {
  let recipientId: string;
  let inventoryItemIds: string[] = [];

  test.beforeEach(async ({ page }) => {
    const auth = new AuthHelper(page);
    await auth.loginAs('distributionManager');
  });

  test('complete distribution workflow: create recipient → assign inventory → complete distribution', async ({ page, request }) => {
    const api = new ApiHelper(page, request);

    // Step 1: Create a recipient
    await page.goto('/recipients');
    await page.click('button:has-text("Add Recipient")');

    const recipient = TestRecipient.create();
    await page.fill('input[name="firstName"]', recipient.firstName);
    await page.fill('input[name="lastName"]', recipient.lastName);
    await page.fill('input[name="contactPhone"]', recipient.contactPhone);
    await page.fill('input[name="email"]', recipient.email);
    await page.fill('input[name="address"]', recipient.address);
    await page.fill('input[name="city"]', recipient.city);
    await page.selectOption('select[name="state"]', recipient.state);
    await page.fill('input[name="zipCode"]', recipient.zipCode);
    await page.fill('input[name="householdSize"]', recipient.householdSize.toString());
    await page.selectOption('select[name="eligibilityStatus"]', recipient.eligibilityStatus);

    await page.click('button:has-text("Save")');

    // Verify recipient created
    await expect(page.locator(`text=${recipient.firstName} ${recipient.lastName}`)).toBeVisible();

    // Get recipient ID
    const url = page.url();
    const match = url.match(/recipients\/([a-f0-9-]+)/);
    recipientId = match ? match[1] : '';
    expect(recipientId).toBeTruthy();

    // Step 2: Create a distribution
    await page.goto('/distributions');
    await page.click('button:has-text("Add Distribution")');

    // Select recipient
    await page.selectOption('select[name="recipientId"]', recipientId);

    // Select today's date
    const today = new Date().toISOString().split('T')[0];
    await page.fill('input[name="distributionDate"]', today);

    // Step 3: Select inventory items
    // Click "Select Items" button
    await page.click('button:has-text("Select Items")');

    // Inventory selection modal/page should appear
    await expect(page.locator('text=Available Inventory')).toBeVisible();

    // Select first available item
    const firstItem = page.locator('[data-testid="inventory-item"]').first();
    await firstItem.locator('input[type="checkbox"]').check();

    // Set quantity
    await firstItem.locator('input[name="quantity"]').fill('2');

    // Select second item if available
    const secondItem = page.locator('[data-testid="inventory-item"]').nth(1);
    if (await secondItem.isVisible()) {
      await secondItem.locator('input[type="checkbox"]').check();
      await secondItem.locator('input[name="quantity"]').fill('1');
    }

    await page.click('button:has-text("Confirm Selection")');

    // Save distribution
    await page.fill('textarea[name="notes"]', 'Test distribution from E2E tests');
    await page.click('button:has-text("Save")');

    // Verify distribution created
    await expect(page.locator('text=Distribution created successfully')).toBeVisible();

    // Distribution should be in "Planned" status
    await expect(page.locator('text=Planned')).toBeVisible();

    // Step 4: Complete the distribution
    await page.click('button:has-text("Complete Distribution")');

    // Confirm completion
    await page.click('button:has-text("Confirm")');

    // Verify distribution marked as completed
    await expect(page.locator('text=Completed')).toBeVisible();
    await expect(page.locator('text=Distribution completed successfully')).toBeVisible();

    // Step 5: Verify inventory updated
    await page.goto('/inventory');

    // Check that inventory quantities were reduced
    // (Specific checks would depend on knowing the initial quantities)
    await expect(page.locator('[data-testid="inventory-table"]')).toBeVisible();

    // Step 6: Verify recipient history updated
    await page.goto(`/recipients/${recipientId}`);
    await expect(page.locator('text=Distribution History')).toBeVisible();

    // Should see the completed distribution in history
    const distributionHistory = page.locator('[data-testid="distribution-history"]');
    await expect(distributionHistory.locator('text=Completed')).toBeVisible();
  });

  test('should prevent over-distribution (insufficient inventory)', async ({ page }) => {
    await page.goto('/distributions');
    await page.click('button:has-text("Add Distribution")');

    // Select a recipient
    const recipientSelect = page.locator('select[name="recipientId"]');
    await recipientSelect.selectOption({ index: 1 });

    // Try to select more items than available in inventory
    await page.click('button:has-text("Select Items")');

    const firstItem = page.locator('[data-testid="inventory-item"]').first();
    await firstItem.locator('input[type="checkbox"]').check();

    // Get available quantity
    const availableQty = await firstItem.locator('[data-testid="available-quantity"]').textContent();
    const maxQty = parseInt(availableQty || '0');

    // Try to request more than available
    await firstItem.locator('input[name="quantity"]').fill((maxQty + 10).toString());

    await page.click('button:has-text("Confirm Selection")');

    // Should show error
    await expect(page.locator('text=Insufficient inventory')).toBeVisible();
  });

  test('should allow canceling a planned distribution', async ({ page }) => {
    await page.goto('/distributions');

    // Find first planned distribution
    const plannedDistribution = page.locator('[data-testid="distribution-row"]:has-text("Planned")').first();

    if (await plannedDistribution.isVisible()) {
      await plannedDistribution.click();

      // Cancel button should be visible
      await page.click('button:has-text("Cancel Distribution")');

      // Confirm cancellation
      await page.click('button:has-text("Confirm")');

      // Verify distribution canceled
      await expect(page.locator('text=Canceled')).toBeVisible();

      // Reserved inventory should be released back to available
      // (This would require checking inventory status)
    }
  });

  test('should show distribution manifest/printable view', async ({ page }) => {
    await page.goto('/distributions');

    // Click on first distribution
    const firstDistribution = page.locator('[data-testid="distribution-row"]').first();
    await firstDistribution.click();

    // Click print/manifest button
    await page.click('button:has-text("Print Manifest")');

    // Manifest view should appear
    await expect(page.locator('[data-testid="distribution-manifest"]')).toBeVisible();

    // Should show recipient info
    await expect(page.locator('text=Recipient Information')).toBeVisible();

    // Should show item list
    await expect(page.locator('text=Items')).toBeVisible();

    // Should show distribution date
    await expect(page.locator('text=Distribution Date')).toBeVisible();
  });

  test('should filter distributions by status', async ({ page }) => {
    await page.goto('/distributions');

    // Click on "Completed" filter
    await page.click('button:has-text("Completed")');

    // All visible distributions should be completed
    const statusBadges = page.locator('[data-testid="status-badge"]');
    const count = await statusBadges.count();

    for (let i = 0; i < count; i++) {
      await expect(statusBadges.nth(i)).toHaveText('Completed');
    }
  });

  test('should show PII masking in recipient list view', async ({ page }) => {
    await page.goto('/recipients');

    // In list view, sensitive information should be masked
    // Full names might show as "John D."
    // Phone numbers might show as "***-**-1234"
    const recipientRows = page.locator('[data-testid="recipient-row"]');

    if (await recipientRows.count() > 0) {
      // Check first row for masked data
      const firstRow = recipientRows.first();

      // Full details should NOT be visible in list
      const phoneCell = firstRow.locator('[data-testid="phone-cell"]');
      const phoneText = await phoneCell.textContent();

      // Phone should be masked (contain asterisks)
      expect(phoneText).toMatch(/\*/);
    }
  });

  test('should show full PII in recipient detail view', async ({ page }) => {
    await page.goto('/recipients');

    // Click on first recipient
    const firstRecipient = page.locator('[data-testid="recipient-row"]').first();
    await firstRecipient.click();

    // Detail view should show full information
    await expect(page.locator('[data-testid="full-name"]')).toBeVisible();
    await expect(page.locator('[data-testid="full-phone"]')).toBeVisible();
    await expect(page.locator('[data-testid="full-email"]')).toBeVisible();
    await expect(page.locator('[data-testid="full-address"]')).toBeVisible();
  });
});
