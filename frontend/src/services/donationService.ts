/**
 * Donation Service
 * Handles all donation-related API calls
 */

import apiClient from './apiClient';
import type { ApiResponse } from '../types/api';
import type {
  Donation,
  CreateDonationRequest,
  UpdateDonationRequest,
  DonationListParams,
  DonationListResponse,
  DonationStats,
  ExpiringDonationsResponse,
  ReceiptUploadUrlResponse,
} from '../types/donation';

/**
 * Get list of donations with optional filtering and pagination
 */
export const getDonations = async (params?: DonationListParams): Promise<DonationListResponse> => {
  const queryParams = new URLSearchParams();

  if (params?.search) queryParams.append('search', params.search);
  if (params?.donorId) queryParams.append('donorId', params.donorId);
  if (params?.category) queryParams.append('category', params.category);
  if (params?.status) queryParams.append('status', params.status);
  if (params?.startDate) queryParams.append('startDate', params.startDate);
  if (params?.endDate) queryParams.append('endDate', params.endDate);
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.lastKey) queryParams.append('lastKey', params.lastKey);

  const url = `/donations${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await apiClient.get<ApiResponse<DonationListResponse>>(url);
  return response.data.data;
};

/**
 * Get a single donation by ID
 */
export const getDonationById = async (donationId: string): Promise<Donation> => {
  const response = await apiClient.get<ApiResponse<Donation>>(`/donations/${donationId}`);
  return response.data.data;
};

/**
 * Create a new donation
 */
export const createDonation = async (data: CreateDonationRequest): Promise<Donation> => {
  const response = await apiClient.post<ApiResponse<Donation>>('/donations', data);
  return response.data.data;
};

/**
 * Update an existing donation
 */
export const updateDonation = async (
  donationId: string,
  data: UpdateDonationRequest
): Promise<Donation> => {
  const response = await apiClient.put<ApiResponse<Donation>>(`/donations/${donationId}`, data);
  return response.data.data;
};

/**
 * Delete a donation
 */
export const deleteDonation = async (donationId: string): Promise<void> => {
  await apiClient.delete(`/donations/${donationId}`);
};

/**
 * Get donation statistics
 */
export const getDonationStats = async (): Promise<DonationStats> => {
  const response = await apiClient.get<ApiResponse<DonationStats>>('/donations/stats');
  return response.data.data;
};

/**
 * Get expiring donations
 */
export const getExpiringDonations = async (days?: number): Promise<ExpiringDonationsResponse> => {
  const queryParams = new URLSearchParams();
  if (days) queryParams.append('days', days.toString());

  const url = `/donations/expiring${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await apiClient.get<ApiResponse<ExpiringDonationsResponse>>(url);
  return response.data.data;
};

/**
 * Get receipt upload URL (S3 pre-signed URL)
 */
export const getReceiptUploadUrl = async (
  donationId: string,
  fileName: string,
  fileType: string
): Promise<ReceiptUploadUrlResponse> => {
  const response = await apiClient.post<ApiResponse<ReceiptUploadUrlResponse>>(
    `/donations/${donationId}/receipt`,
    {
      fileName,
      fileType,
    }
  );
  return response.data.data;
};

/**
 * Upload receipt file to S3 using pre-signed URL
 */
export const uploadReceipt = async (uploadUrl: string, file: File): Promise<void> => {
  await fetch(uploadUrl, {
    method: 'PUT',
    body: file,
    headers: {
      'Content-Type': file.type,
    },
  });
};

/**
 * Full receipt upload workflow: get URL, upload file, and return receipt URL
 */
export const uploadReceiptComplete = async (
  donationId: string,
  file: File
): Promise<string> => {
  // Get pre-signed URL
  const { uploadUrl, receiptUrl } = await getReceiptUploadUrl(donationId, file.name, file.type);

  // Upload file to S3
  await uploadReceipt(uploadUrl, file);

  return receiptUrl;
};

/**
 * Export donations to CSV
 */
export const exportDonations = async (params?: DonationListParams): Promise<Blob> => {
  const queryParams = new URLSearchParams();

  if (params?.search) queryParams.append('search', params.search);
  if (params?.donorId) queryParams.append('donorId', params.donorId);
  if (params?.category) queryParams.append('category', params.category);
  if (params?.status) queryParams.append('status', params.status);
  if (params?.startDate) queryParams.append('startDate', params.startDate);
  if (params?.endDate) queryParams.append('endDate', params.endDate);

  const url = `/donations/export${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await apiClient.get(url, {
    responseType: 'blob',
  });
  return response.data;
};

export default {
  getDonations,
  getDonationById,
  createDonation,
  updateDonation,
  deleteDonation,
  getDonationStats,
  getExpiringDonations,
  getReceiptUploadUrl,
  uploadReceipt,
  uploadReceiptComplete,
  exportDonations,
};
