/**
 * Recipient Type Definitions
 * Represents recipient entities with PII protection
 */

export type RecipientStatus = 'active' | 'inactive' | 'suspended';
export type EligibilityStatus = 'eligible' | 'pending' | 'ineligible';

export interface DietaryRestriction {
  type: string;
  notes?: string;
}

export interface Recipient {
  recipientId: string;
  firstName: string;
  lastName: string;
  email?: string;
  phone: string;
  address: {
    street: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
  };
  householdSize: number;
  dietaryRestrictions: DietaryRestriction[];
  eligibilityStatus: EligibilityStatus;
  status: RecipientStatus;
  notes?: string;
  totalDistributions?: number;
  lastDistributionDate?: string;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  updatedBy: string;
}

export interface RecipientListItem {
  recipientId: string;
  firstName: string;
  lastNameInitial: string; // Privacy: only show initial
  phoneLastFour: string; // Privacy: only show last 4 digits
  cityState: string; // Privacy: only show city and state
  householdSize: number;
  eligibilityStatus: EligibilityStatus;
  status: RecipientStatus;
  lastDistributionDate?: string;
}

export interface CreateRecipientRequest {
  firstName: string;
  lastName: string;
  email?: string;
  phone: string;
  address: {
    street: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
  };
  householdSize: number;
  dietaryRestrictions?: DietaryRestriction[];
  notes?: string;
}

export interface UpdateRecipientRequest {
  firstName?: string;
  lastName?: string;
  email?: string;
  phone?: string;
  address?: {
    street: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
  };
  householdSize?: number;
  dietaryRestrictions?: DietaryRestriction[];
  eligibilityStatus?: EligibilityStatus;
  status?: RecipientStatus;
  notes?: string;
}

export interface RecipientListParams {
  search?: string;
  status?: RecipientStatus;
  eligibilityStatus?: EligibilityStatus;
  limit?: number;
  lastKey?: string;
}

export interface RecipientListResponse {
  recipients: RecipientListItem[];
  lastKey?: string;
  total: number;
}

export interface RecipientDistribution {
  distributionId: string;
  date: string;
  items: Array<{
    itemName: string;
    category: string;
    quantity: number;
    unit: string;
  }>;
  status: string;
  notes?: string;
}

export interface RecipientDistributionHistoryResponse {
  distributions: RecipientDistribution[];
  lastKey?: string;
  total: number;
}

export interface RecipientStats {
  totalRecipients: number;
  activeRecipients: number;
  eligibleRecipients: number;
  totalHouseholds: number;
  averageHouseholdSize: number;
  recipientsByStatus: Record<RecipientStatus, number>;
  recipientsByEligibility: Record<EligibilityStatus, number>;
}

/**
 * Utility function to mask PII for list view
 */
export const maskRecipientForList = (recipient: Recipient): RecipientListItem => {
  return {
    recipientId: recipient.recipientId,
    firstName: recipient.firstName,
    lastNameInitial: recipient.lastName.charAt(0) + '.',
    phoneLastFour: recipient.phone.slice(-4),
    cityState: `${recipient.address.city}, ${recipient.address.state}`,
    householdSize: recipient.householdSize,
    eligibilityStatus: recipient.eligibilityStatus,
    status: recipient.status,
    lastDistributionDate: recipient.lastDistributionDate,
  };
};
