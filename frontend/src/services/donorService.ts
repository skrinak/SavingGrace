/**
 * Donor Service
 * Handles all donor-related API calls
 */

import apiClient from './apiClient';
import type { ApiResponse } from '../types/api';
import type {
  Donor,
  CreateDonorRequest,
  UpdateDonorRequest,
  DonorListParams,
  DonorListResponse,
  DonorStats,
} from '../types/donor';

/**
 * Get list of donors with optional filtering and pagination
 */
export const getDonors = async (params?: DonorListParams): Promise<DonorListResponse> => {
  const queryParams = new URLSearchParams();

  if (params?.search) queryParams.append('search', params.search);
  if (params?.type) queryParams.append('type', params.type);
  if (params?.status) queryParams.append('status', params.status);
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.lastKey) queryParams.append('lastKey', params.lastKey);

  const url = `/donors${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await apiClient.get<ApiResponse<DonorListResponse>>(url);
  return response.data.data;
};

/**
 * Get a single donor by ID
 */
export const getDonorById = async (donorId: string): Promise<Donor> => {
  const response = await apiClient.get<ApiResponse<Donor>>(`/donors/${donorId}`);
  return response.data.data;
};

/**
 * Create a new donor
 */
export const createDonor = async (data: CreateDonorRequest): Promise<Donor> => {
  const response = await apiClient.post<ApiResponse<Donor>>('/donors', data);
  return response.data.data;
};

/**
 * Update an existing donor
 */
export const updateDonor = async (donorId: string, data: UpdateDonorRequest): Promise<Donor> => {
  const response = await apiClient.put<ApiResponse<Donor>>(`/donors/${donorId}`, data);
  return response.data.data;
};

/**
 * Delete a donor
 */
export const deleteDonor = async (donorId: string): Promise<void> => {
  await apiClient.delete(`/donors/${donorId}`);
};

/**
 * Get donor statistics
 */
export const getDonorStats = async (): Promise<DonorStats> => {
  const response = await apiClient.get<ApiResponse<DonorStats>>('/donors/stats');
  return response.data.data;
};

/**
 * Export donors to CSV
 */
export const exportDonors = async (params?: DonorListParams): Promise<Blob> => {
  const queryParams = new URLSearchParams();

  if (params?.search) queryParams.append('search', params.search);
  if (params?.type) queryParams.append('type', params.type);
  if (params?.status) queryParams.append('status', params.status);

  const url = `/donors/export${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await apiClient.get(url, {
    responseType: 'blob',
  });
  return response.data;
};

/**
 * Get donation history for a donor
 */
export const getDonorDonations = async (
  donorId: string,
  params?: { limit?: number; lastKey?: string }
): Promise<{
  donations: Array<{
    donationId: string;
    date: string;
    items: Array<{ name: string; quantity: number; unit: string }>;
    status: string;
    estimatedValue: number;
  }>;
  lastKey?: string;
}> => {
  const queryParams = new URLSearchParams();
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.lastKey) queryParams.append('lastKey', params.lastKey);

  const url = `/donors/${donorId}/donations${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await apiClient.get<
    ApiResponse<{
      donations: Array<{
        donationId: string;
        date: string;
        items: Array<{ name: string; quantity: number; unit: string }>;
        status: string;
        estimatedValue: number;
      }>;
      lastKey?: string;
    }>
  >(url);
  return response.data.data;
};

export default {
  getDonors,
  getDonorById,
  createDonor,
  updateDonor,
  deleteDonor,
  getDonorStats,
  exportDonors,
  getDonorDonations,
};
