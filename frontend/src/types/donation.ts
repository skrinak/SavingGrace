/**
 * Donation Type Definitions
 * Represents donation entities and related data structures
 */

export type FoodCategory =
  | 'produce'
  | 'dairy'
  | 'protein'
  | 'grains'
  | 'canned'
  | 'frozen'
  | 'beverages'
  | 'bakery'
  | 'prepared'
  | 'other';

export type DonationStatus = 'pending' | 'received' | 'distributed' | 'expired' | 'cancelled';

export interface DonationItem {
  itemId: string;
  name: string;
  category: FoodCategory;
  quantity: number;
  unit: string;
  estimatedValue: number;
  expirationDate: string;
  storageLocation?: string;
  notes?: string;
}

export interface Donation {
  donationId: string;
  donorId: string;
  donorName: string;
  date: string;
  status: DonationStatus;
  items: DonationItem[];
  totalValue: number;
  receiptUrl?: string;
  pickupLocation?: string;
  pickupTime?: string;
  receivedBy?: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  updatedBy: string;
}

export interface CreateDonationItemRequest {
  name: string;
  category: FoodCategory;
  quantity: number;
  unit: string;
  estimatedValue: number;
  expirationDate: string;
  storageLocation?: string;
  notes?: string;
}

export interface CreateDonationRequest {
  donorId: string;
  date: string;
  items: CreateDonationItemRequest[];
  pickupLocation?: string;
  pickupTime?: string;
  notes?: string;
}

export interface UpdateDonationRequest {
  donorId?: string;
  date?: string;
  status?: DonationStatus;
  items?: CreateDonationItemRequest[];
  pickupLocation?: string;
  pickupTime?: string;
  receivedBy?: string;
  notes?: string;
}

export interface DonationListParams {
  search?: string;
  donorId?: string;
  category?: FoodCategory;
  status?: DonationStatus;
  startDate?: string;
  endDate?: string;
  limit?: number;
  lastKey?: string;
}

export interface DonationListResponse {
  donations: Donation[];
  lastKey?: string;
  total: number;
}

export interface ExpiringDonation {
  itemId: string;
  donationId: string;
  donorName: string;
  itemName: string;
  category: FoodCategory;
  quantity: number;
  unit: string;
  expirationDate: string;
  daysUntilExpiry: number;
  storageLocation?: string;
}

export interface ExpiringDonationsResponse {
  items: ExpiringDonation[];
  total: number;
}

export interface DonationStats {
  totalDonations: number;
  pendingDonations: number;
  receivedDonations: number;
  totalValue: number;
  donationsByCategory: Record<FoodCategory, number>;
  donationsByMonth: Array<{
    month: string;
    count: number;
    value: number;
  }>;
  topDonors: Array<{
    donorId: string;
    donorName: string;
    totalDonations: number;
    totalValue: number;
  }>;
}

export interface ReceiptUploadUrlResponse {
  uploadUrl: string;
  receiptUrl: string;
  expiresIn: number;
}
