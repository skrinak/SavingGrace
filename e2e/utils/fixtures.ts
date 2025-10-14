/**
 * Test Data Fixtures for E2E Tests
 * Provides reusable test data for various entities
 */

export const TestDonor = {
  create: () => ({
    name: `Test Donor ${Date.now()}`,
    contactEmail: `donor${Date.now()}@test.com`,
    contactPhone: '555-0100',
    address: '123 Test Street',
    city: 'Seattle',
    state: 'WA',
    zipCode: '98101',
    type: 'Individual',
    notes: 'Test donor created by E2E tests',
  }),
};

export const TestDonation = {
  create: (donorId: string) => ({
    donorId,
    donationDate: new Date().toISOString().split('T')[0],
    items: [
      {
        category: 'Produce',
        itemName: 'Apples',
        quantity: 10,
        unit: 'lbs',
        expirationDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        condition: 'Fresh',
      },
      {
        category: 'Canned Goods',
        itemName: 'Canned Beans',
        quantity: 24,
        unit: 'cans',
        expirationDate: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        condition: 'Good',
      },
    ],
    notes: 'Test donation created by E2E tests',
  }),
};

export const TestRecipient = {
  create: () => ({
    firstName: `Test${Date.now()}`,
    lastName: 'Recipient',
    contactPhone: '555-0200',
    email: `recipient${Date.now()}@test.com`,
    address: '456 Test Avenue',
    city: 'Seattle',
    state: 'WA',
    zipCode: '98102',
    householdSize: 4,
    dietaryRestrictions: ['Vegetarian'],
    eligibilityStatus: 'Verified',
    notes: 'Test recipient created by E2E tests',
  }),
};

export const TestDistribution = {
  create: (recipientId: string, inventoryItems: Array<{ id: string; quantity: number }>) => ({
    recipientId,
    distributionDate: new Date().toISOString().split('T')[0],
    items: inventoryItems,
    notes: 'Test distribution created by E2E tests',
  }),
};

export const TestUser = {
  create: (role: string = 'Volunteer') => ({
    email: `testuser${Date.now()}@savinggrace.test`,
    name: `Test User ${Date.now()}`,
    role,
    password: 'TestPassword123!',
  }),
};

/**
 * Wait utility for async operations
 */
export const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Generate random string
 */
export const randomString = (length: number = 8): string => {
  return Math.random().toString(36).substring(2, 2 + length);
};
