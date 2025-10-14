/**
 * Donor Type Definitions
 * Represents donor entities and related data structures
 */

export type DonorType = 'individual' | 'restaurant' | 'grocery' | 'farm' | 'manufacturer' | 'other';
export type DonorStatus = 'active' | 'inactive' | 'suspended';

export interface DonorContact {
  name: string;
  email: string;
  phone: string;
  title?: string;
  isPrimary: boolean;
}

export interface DonorAddress {
  street: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
}

export interface Donor {
  donorId: string;
  name: string;
  type: DonorType;
  status: DonorStatus;
  email: string;
  phone: string;
  address: DonorAddress;
  contacts: DonorContact[];
  taxId?: string;
  licenseNumber?: string;
  website?: string;
  notes?: string;
  preferredPickupTimes?: string;
  specialInstructions?: string;
  totalDonations?: number;
  lastDonationDate?: string;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  updatedBy: string;
}

export interface CreateDonorRequest {
  name: string;
  type: DonorType;
  email: string;
  phone: string;
  address: DonorAddress;
  contacts?: DonorContact[];
  taxId?: string;
  licenseNumber?: string;
  website?: string;
  notes?: string;
  preferredPickupTimes?: string;
  specialInstructions?: string;
}

export interface UpdateDonorRequest {
  name?: string;
  type?: DonorType;
  status?: DonorStatus;
  email?: string;
  phone?: string;
  address?: DonorAddress;
  contacts?: DonorContact[];
  taxId?: string;
  licenseNumber?: string;
  website?: string;
  notes?: string;
  preferredPickupTimes?: string;
  specialInstructions?: string;
}

export interface DonorListParams {
  search?: string;
  type?: DonorType;
  status?: DonorStatus;
  limit?: number;
  lastKey?: string;
}

export interface DonorListResponse {
  donors: Donor[];
  lastKey?: string;
  total: number;
}

export interface DonorStats {
  totalDonors: number;
  activeDonors: number;
  inactiveDonors: number;
  donorsByType: Record<DonorType, number>;
  topDonors: Array<{
    donorId: string;
    name: string;
    totalDonations: number;
  }>;
}
