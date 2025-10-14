import { Page, APIRequestContext } from '@playwright/test';

/**
 * API Helper for E2E Tests
 * Provides methods for making authenticated API requests
 */

export class ApiHelper {
  private baseURL: string;

  constructor(private page: Page, private request: APIRequestContext) {
    this.baseURL = process.env.API_URL || 'https://a9np4bbum8.execute-api.us-west-2.amazonaws.com/dev';
  }

  /**
   * Get access token from localStorage
   */
  private async getAccessToken(): Promise<string | null> {
    return await this.page.evaluate(() => localStorage.getItem('access_token'));
  }

  /**
   * Make authenticated GET request
   */
  async get(endpoint: string): Promise<any> {
    const token = await this.getAccessToken();
    const response = await this.request.get(`${this.baseURL}${endpoint}`, {
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json',
      },
    });
    return await response.json();
  }

  /**
   * Make authenticated POST request
   */
  async post(endpoint: string, data: any): Promise<any> {
    const token = await this.getAccessToken();
    const response = await this.request.post(`${this.baseURL}${endpoint}`, {
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json',
      },
      data,
    });
    return await response.json();
  }

  /**
   * Make authenticated PUT request
   */
  async put(endpoint: string, data: any): Promise<any> {
    const token = await this.getAccessToken();
    const response = await this.request.put(`${this.baseURL}${endpoint}`, {
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json',
      },
      data,
    });
    return await response.json();
  }

  /**
   * Make authenticated DELETE request
   */
  async delete(endpoint: string): Promise<any> {
    const token = await this.getAccessToken();
    const response = await this.request.delete(`${this.baseURL}${endpoint}`, {
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json',
      },
    });
    return await response.json();
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.request.get(`${this.baseURL}/health`);
      return response.ok();
    } catch {
      return false;
    }
  }
}
