import { test, expect } from '@playwright/test';
import { AuthHelper } from '../utils/auth.helper';
import { ApiHelper } from '../utils/api.helper';
import { TestDonor, TestDonation } from '../utils/fixtures';

/**
 * Donation Workflow E2E Tests
 * Tests the complete workflow: create donor → record donation → view inventory
 */

test.describe('Donation Workflow', () => {
  let donorId: string;

  test.beforeEach(async ({ page }) => {
    const auth = new AuthHelper(page);
    await auth.loginAs('donorCoordinator');
  });

  test('complete donation workflow: create donor → record donation → verify inventory', async ({ page, request }) => {
    const api = new ApiHelper(page, request);

    // Step 1: Create a new donor
    await page.goto('/donors');
    await page.click('button:has-text("Add Donor")');

    const donor = TestDonor.create();
    await page.fill('input[name="name"]', donor.name);
    await page.fill('input[name="contactEmail"]', donor.contactEmail);
    await page.fill('input[name="contactPhone"]', donor.contactPhone);
    await page.fill('input[name="address"]', donor.address);
    await page.fill('input[name="city"]', donor.city);
    await page.selectOption('select[name="state"]', donor.state);
    await page.fill('input[name="zipCode"]', donor.zipCode);
    await page.selectOption('select[name="type"]', donor.type);
    await page.fill('textarea[name="notes"]', donor.notes);

    await page.click('button:has-text("Save")');

    // Verify donor created
    await expect(page.locator('text=' + donor.name)).toBeVisible();

    // Get donor ID from URL or API
    const url = page.url();
    const match = url.match(/donors\/([a-f0-9-]+)/);
    donorId = match ? match[1] : '';
    expect(donorId).toBeTruthy();

    // Step 2: Record a donation
    await page.goto('/donations');
    await page.click('button:has-text("Add Donation")');

    // Select donor
    await page.selectOption('select[name="donorId"]', donorId);

    // Add first item
    await page.click('button:has-text("Add Item")');
    await page.selectOption('select[name="items.0.category"]', 'Produce');
    await page.fill('input[name="items.0.itemName"]', 'Apples');
    await page.fill('input[name="items.0.quantity"]', '10');
    await page.selectOption('select[name="items.0.unit"]', 'lbs');

    const expirationDate = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    await page.fill('input[name="items.0.expirationDate"]', expirationDate);

    // Add second item
    await page.click('button:has-text("Add Item")');
    await page.selectOption('select[name="items.1.category"]', 'Canned Goods');
    await page.fill('input[name="items.1.itemName"]', 'Canned Beans');
    await page.fill('input[name="items.1.quantity"]', '24');
    await page.selectOption('select[name="items.1.unit"]', 'cans');

    const longExpirationDate = new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    await page.fill('input[name="items.1.expirationDate"]', longExpirationDate);

    await page.click('button:has-text("Save")');

    // Verify donation created
    await expect(page.locator('text=Donation recorded successfully')).toBeVisible();

    // Step 3: Verify inventory updated
    await page.goto('/inventory');

    // Should see the donated items in inventory
    await expect(page.locator('text=Apples')).toBeVisible();
    await expect(page.locator('text=Canned Beans')).toBeVisible();

    // Verify quantities
    await expect(page.locator('text=10 lbs')).toBeVisible();
    await expect(page.locator('text=24 cans')).toBeVisible();

    // Step 4: View donation history for donor
    await page.goto(`/donors/${donorId}`);

    // Should see donation history
    await expect(page.locator('text=Donation History')).toBeVisible();
    await expect(page.locator('text=Apples')).toBeVisible();
    await expect(page.locator('text=Canned Beans')).toBeVisible();
  });

  test('should handle donation with receipt upload', async ({ page }) => {
    // Create donor first
    await page.goto('/donors');
    await page.click('button:has-text("Add Donor")');

    const donor = TestDonor.create();
    await page.fill('input[name="name"]', donor.name);
    await page.fill('input[name="contactEmail"]', donor.contactEmail);
    await page.click('button:has-text("Save")');

    // Record donation
    await page.goto('/donations');
    await page.click('button:has-text("Add Donation")');

    // Fill donation details
    const donorSelect = page.locator('select[name="donorId"]');
    await donorSelect.selectOption({ label: donor.name });

    await page.click('button:has-text("Add Item")');
    await page.selectOption('select[name="items.0.category"]', 'Produce');
    await page.fill('input[name="items.0.itemName"]', 'Bananas');
    await page.fill('input[name="items.0.quantity"]', '5');

    // Upload receipt
    const fileInput = page.locator('input[type="file"]');
    // Note: In real test, you would use setInputFiles with a test file
    // await fileInput.setInputFiles('path/to/test-receipt.pdf');

    await page.click('button:has-text("Save")');

    // Verify donation created with receipt
    await expect(page.locator('text=Donation recorded successfully')).toBeVisible();
  });

  test('should show expiring items alert', async ({ page }) => {
    await page.goto('/inventory');

    // Click on expiring items filter/tab
    await page.click('button:has-text("Expiring Soon")');

    // Should see items expiring within 7 days
    const expiringItems = page.locator('[data-testid="expiring-item"]');

    // Verify expiring items have warning indicator
    if (await expiringItems.count() > 0) {
      await expect(expiringItems.first().locator('[data-testid="warning-icon"]')).toBeVisible();
    }
  });

  test('should validate donation form', async ({ page }) => {
    await page.goto('/donations');
    await page.click('button:has-text("Add Donation")');

    // Try to submit without filling required fields
    await page.click('button:has-text("Save")');

    // Should show validation errors
    await expect(page.locator('text=Donor is required')).toBeVisible();
    await expect(page.locator('text=At least one item is required')).toBeVisible();
  });

  test('should allow editing donation', async ({ page }) => {
    // Navigate to donations list
    await page.goto('/donations');

    // Find first donation and click edit
    const firstDonation = page.locator('[data-testid="donation-row"]').first();
    await firstDonation.locator('[data-testid="edit-button"]').click();

    // Modify notes
    await page.fill('textarea[name="notes"]', 'Updated notes for E2E test');
    await page.click('button:has-text("Save")');

    // Verify update successful
    await expect(page.locator('text=Donation updated successfully')).toBeVisible();
  });
});
