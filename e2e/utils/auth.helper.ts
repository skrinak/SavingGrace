import { Page, expect } from '@playwright/test';

/**
 * Authentication Helper for E2E Tests
 * Provides methods for login, logout, and token management
 */

export interface TestUser {
  email: string;
  password: string;
  role: 'Admin' | 'Donor Coordinator' | 'Distribution Manager' | 'Volunteer' | 'Read-Only';
}

export const TEST_USERS: Record<string, TestUser> = {
  admin: {
    email: 'admin@savinggrace.test',
    password: 'AdminPassword123!',
    role: 'Admin',
  },
  donorCoordinator: {
    email: 'coordinator@savinggrace.test',
    password: 'Coordinator123!',
    role: 'Donor Coordinator',
  },
  distributionManager: {
    email: 'manager@savinggrace.test',
    password: 'Manager123!',
    role: 'Distribution Manager',
  },
  volunteer: {
    email: 'volunteer@savinggrace.test',
    password: 'Volunteer123!',
    role: 'Volunteer',
  },
  readOnly: {
    email: 'readonly@savinggrace.test',
    password: 'ReadOnly123!',
    role: 'Read-Only',
  },
};

export class AuthHelper {
  constructor(private page: Page) {}

  /**
   * Login with email and password
   */
  async login(email: string, password: string): Promise<void> {
    await this.page.goto('/login');
    await this.page.fill('input[name="email"]', email);
    await this.page.fill('input[name="password"]', password);
    await this.page.click('button[type="submit"]');

    // Wait for redirect to dashboard
    await expect(this.page).toHaveURL(/\/(dashboard|home)/);
  }

  /**
   * Login with test user role
   */
  async loginAs(role: keyof typeof TEST_USERS): Promise<void> {
    const user = TEST_USERS[role];
    await this.login(user.email, user.password);
  }

  /**
   * Logout current user
   */
  async logout(): Promise<void> {
    // Click user menu
    await this.page.click('[data-testid="user-menu"]');
    // Click logout button
    await this.page.click('[data-testid="logout-button"]');
    // Wait for redirect to login
    await expect(this.page).toHaveURL(/\/login/);
  }

  /**
   * Get access token from localStorage
   */
  async getAccessToken(): Promise<string | null> {
    const token = await this.page.evaluate(() => {
      return localStorage.getItem('access_token');
    });
    return token;
  }

  /**
   * Check if user is logged in
   */
  async isLoggedIn(): Promise<boolean> {
    const token = await this.getAccessToken();
    return !!token;
  }

  /**
   * Set up authenticated state (useful for bypassing login in tests)
   */
  async setupAuthState(accessToken: string, refreshToken: string): Promise<void> {
    await this.page.evaluate(
      ({ accessToken, refreshToken }) => {
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
      },
      { accessToken, refreshToken }
    );
  }

  /**
   * Clear authentication state
   */
  async clearAuthState(): Promise<void> {
    await this.page.evaluate(() => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    });
  }
}
