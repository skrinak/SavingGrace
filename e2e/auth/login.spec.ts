import { test, expect } from '@playwright/test';
import { AuthHelper, TEST_USERS } from '../utils/auth.helper';

/**
 * Authentication E2E Tests
 * Tests login, logout, and session management
 */

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    const auth = new AuthHelper(page);
    await auth.clearAuthState();
  });

  test('should login successfully with valid credentials', async ({ page }) => {
    const auth = new AuthHelper(page);
    await auth.loginAs('admin');

    // Verify user is on dashboard
    await expect(page).toHaveURL(/\/(dashboard|home)/);

    // Verify token is stored
    const token = await auth.getAccessToken();
    expect(token).toBeTruthy();
  });

  test('should fail login with invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'invalid@test.com');
    await page.fill('input[name="password"]', 'WrongPassword123!');
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('[role="alert"]')).toContainText(/incorrect/i);

    // Should still be on login page
    await expect(page).toHaveURL(/\/login/);
  });

  test('should logout successfully', async ({ page }) => {
    const auth = new AuthHelper(page);
    await auth.loginAs('admin');

    // Logout
    await auth.logout();

    // Verify redirected to login
    await expect(page).toHaveURL(/\/login/);

    // Verify token is cleared
    const token = await auth.getAccessToken();
    expect(token).toBeNull();
  });

  test('should redirect to login when accessing protected route without auth', async ({ page }) => {
    await page.goto('/donors');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should persist session after page reload', async ({ page }) => {
    const auth = new AuthHelper(page);
    await auth.loginAs('admin');

    // Reload page
    await page.reload();

    // Should still be authenticated
    await expect(page).toHaveURL(/\/(dashboard|home)/);
    const token = await auth.getAccessToken();
    expect(token).toBeTruthy();
  });
});

test.describe('Password Reset', () => {
  test('should show password reset form', async ({ page }) => {
    await page.goto('/login');
    await page.click('text=Forgot Password');

    // Should be on reset password page
    await expect(page).toHaveURL(/\/reset-password/);
    await expect(page.locator('input[name="email"]')).toBeVisible();
  });

  test('should submit password reset request', async ({ page }) => {
    await page.goto('/reset-password');
    await page.fill('input[name="email"]', 'admin@savinggrace.test');
    await page.click('button[type="submit"]');

    // Should show success message
    await expect(page.locator('[role="alert"]')).toContainText(/check your email/i);
  });
});

test.describe('Signup', () => {
  test('should show signup form', async ({ page }) => {
    await page.goto('/signup');

    // Verify form fields
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('input[name="confirmPassword"]')).toBeVisible();
    await expect(page.locator('input[name="name"]')).toBeVisible();
  });

  test('should validate password strength', async ({ page }) => {
    await page.goto('/signup');
    await page.fill('input[name="email"]', 'newuser@test.com');
    await page.fill('input[name="password"]', 'weak');
    await page.fill('input[name="confirmPassword"]', 'weak');
    await page.fill('input[name="name"]', 'New User');
    await page.click('button[type="submit"]');

    // Should show password strength error
    await expect(page.locator('[role="alert"]')).toContainText(/password/i);
  });
});
