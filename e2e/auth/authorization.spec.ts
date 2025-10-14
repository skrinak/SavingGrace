import { test, expect } from '@playwright/test';
import { AuthHelper, TEST_USERS } from '../utils/auth.helper';

/**
 * Authorization E2E Tests
 * Tests role-based access control (RBAC)
 */

test.describe('Authorization - Admin Role', () => {
  test.beforeEach(async ({ page }) => {
    const auth = new AuthHelper(page);
    await auth.loginAs('admin');
  });

  test('should have access to all features', async ({ page }) => {
    // Admin should see all menu items
    await expect(page.locator('[href="/donors"]')).toBeVisible();
    await expect(page.locator('[href="/donations"]')).toBeVisible();
    await expect(page.locator('[href="/recipients"]')).toBeVisible();
    await expect(page.locator('[href="/distributions"]')).toBeVisible();
    await expect(page.locator('[href="/inventory"]')).toBeVisible();
    await expect(page.locator('[href="/reports"]')).toBeVisible();
    await expect(page.locator('[href="/users"]')).toBeVisible();
  });

  test('should be able to manage users', async ({ page }) => {
    await page.goto('/users');

    // Should see user management interface
    await expect(page.locator('text=Users')).toBeVisible();
    await expect(page.locator('button:has-text("Add User")')).toBeVisible();
  });

  test('should be able to delete items', async ({ page }) => {
    await page.goto('/donors');

    // Should see delete buttons (if donors exist)
    const deleteButtons = page.locator('[data-testid="delete-button"]');
    if (await deleteButtons.count() > 0) {
      await expect(deleteButtons.first()).toBeVisible();
    }
  });
});

test.describe('Authorization - Donor Coordinator Role', () => {
  test.beforeEach(async ({ page }) => {
    const auth = new AuthHelper(page);
    await auth.loginAs('donorCoordinator');
  });

  test('should have access to donors and donations', async ({ page }) => {
    // Should see donors and donations menu
    await expect(page.locator('[href="/donors"]')).toBeVisible();
    await expect(page.locator('[href="/donations"]')).toBeVisible();
    await expect(page.locator('[href="/inventory"]')).toBeVisible();
  });

  test('should NOT have access to user management', async ({ page }) => {
    // Should not see users menu
    await expect(page.locator('[href="/users"]')).not.toBeVisible();

    // Direct navigation should be blocked
    await page.goto('/users');
    await expect(page).not.toHaveURL(/\/users/);
  });

  test('should be able to create donors', async ({ page }) => {
    await page.goto('/donors');

    // Should see add button
    await expect(page.locator('button:has-text("Add Donor")')).toBeVisible();
  });
});

test.describe('Authorization - Distribution Manager Role', () => {
  test.beforeEach(async ({ page }) => {
    const auth = new AuthHelper(page);
    await auth.loginAs('distributionManager');
  });

  test('should have access to recipients and distributions', async ({ page }) => {
    // Should see recipients and distributions menu
    await expect(page.locator('[href="/recipients"]')).toBeVisible();
    await expect(page.locator('[href="/distributions"]')).toBeVisible();
    await expect(page.locator('[href="/inventory"]')).toBeVisible();
  });

  test('should NOT have access to donor management', async ({ page }) => {
    // Should not see donors menu (or it should be read-only)
    const donorsLink = page.locator('[href="/donors"]');
    if (await donorsLink.isVisible()) {
      // If visible, should be read-only
      await page.goto('/donors');
      await expect(page.locator('button:has-text("Add Donor")')).not.toBeVisible();
    }
  });

  test('should be able to create distributions', async ({ page }) => {
    await page.goto('/distributions');

    // Should see add button
    await expect(page.locator('button:has-text("Add Distribution")')).toBeVisible();
  });
});

test.describe('Authorization - Volunteer Role', () => {
  test.beforeEach(async ({ page }) => {
    const auth = new AuthHelper(page);
    await auth.loginAs('volunteer');
  });

  test('should have read access to most features', async ({ page }) => {
    // Should see menu items but not create/edit/delete buttons
    await expect(page.locator('[href="/donors"]')).toBeVisible();
    await expect(page.locator('[href="/donations"]')).toBeVisible();
    await expect(page.locator('[href="/recipients"]')).toBeVisible();
  });

  test('should NOT be able to create donors', async ({ page }) => {
    await page.goto('/donors');

    // Should not see add button
    await expect(page.locator('button:has-text("Add Donor")')).not.toBeVisible();
  });

  test('should NOT be able to edit items', async ({ page }) => {
    await page.goto('/donors');

    // Should not see edit buttons
    await expect(page.locator('[data-testid="edit-button"]')).not.toBeVisible();
  });
});

test.describe('Authorization - Read-Only Role', () => {
  test.beforeEach(async ({ page }) => {
    const auth = new AuthHelper(page);
    await auth.loginAs('readOnly');
  });

  test('should only have view access', async ({ page }) => {
    // Should see menu items
    await expect(page.locator('[href="/donors"]')).toBeVisible();
    await expect(page.locator('[href="/reports"]')).toBeVisible();
  });

  test('should NOT see any action buttons', async ({ page }) => {
    await page.goto('/donors');

    // Should not see any create/edit/delete buttons
    await expect(page.locator('button:has-text("Add")')).not.toBeVisible();
    await expect(page.locator('[data-testid="edit-button"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="delete-button"]')).not.toBeVisible();
  });

  test('should NOT have access to user management', async ({ page }) => {
    await expect(page.locator('[href="/users"]')).not.toBeVisible();

    await page.goto('/users');
    await expect(page).not.toHaveURL(/\/users/);
  });
});
