/**
 * Recipient Service
 * Handles all recipient-related API calls with privacy protection
 */

import apiClient from './apiClient';
import type { ApiResponse } from '../types/api';
import type {
  Recipient,
  CreateRecipientRequest,
  UpdateRecipientRequest,
  RecipientListParams,
  RecipientListResponse,
  RecipientStats,
  RecipientDistributionHistoryResponse,
} from '../types/recipient';

/**
 * Get list of recipients with privacy masking
 */
export const getRecipients = async (params?: RecipientListParams): Promise<RecipientListResponse> => {
  const queryParams = new URLSearchParams();

  if (params?.search) queryParams.append('search', params.search);
  if (params?.status) queryParams.append('status', params.status);
  if (params?.eligibilityStatus) queryParams.append('eligibilityStatus', params.eligibilityStatus);
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.lastKey) queryParams.append('lastKey', params.lastKey);

  const url = `/recipients${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await apiClient.get<ApiResponse<RecipientListResponse>>(url);
  return response.data.data;
};

/**
 * Get a single recipient by ID (full details - requires permission)
 */
export const getRecipientById = async (recipientId: string): Promise<Recipient> => {
  const response = await apiClient.get<ApiResponse<Recipient>>(`/recipients/${recipientId}`);
  return response.data.data;
};

/**
 * Create a new recipient
 */
export const createRecipient = async (data: CreateRecipientRequest): Promise<Recipient> => {
  const response = await apiClient.post<ApiResponse<Recipient>>('/recipients', data);
  return response.data.data;
};

/**
 * Update an existing recipient
 */
export const updateRecipient = async (
  recipientId: string,
  data: UpdateRecipientRequest
): Promise<Recipient> => {
  const response = await apiClient.put<ApiResponse<Recipient>>(`/recipients/${recipientId}`, data);
  return response.data.data;
};

/**
 * Delete a recipient (soft delete with audit trail)
 */
export const deleteRecipient = async (recipientId: string): Promise<void> => {
  await apiClient.delete(`/recipients/${recipientId}`);
};

/**
 * Get recipient statistics
 */
export const getRecipientStats = async (): Promise<RecipientStats> => {
  const response = await apiClient.get<ApiResponse<RecipientStats>>('/recipients/stats');
  return response.data.data;
};

/**
 * Get distribution history for a recipient
 */
export const getRecipientDistributionHistory = async (
  recipientId: string,
  params?: { limit?: number; lastKey?: string }
): Promise<RecipientDistributionHistoryResponse> => {
  const queryParams = new URLSearchParams();
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.lastKey) queryParams.append('lastKey', params.lastKey);

  const url = `/recipients/${recipientId}/history${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await apiClient.get<ApiResponse<RecipientDistributionHistoryResponse>>(url);
  return response.data.data;
};

/**
 * Export recipients to CSV
 */
export const exportRecipients = async (params?: RecipientListParams): Promise<Blob> => {
  const queryParams = new URLSearchParams();

  if (params?.search) queryParams.append('search', params.search);
  if (params?.status) queryParams.append('status', params.status);
  if (params?.eligibilityStatus) queryParams.append('eligibilityStatus', params.eligibilityStatus);

  const url = `/recipients/export${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await apiClient.get(url, {
    responseType: 'blob',
  });
  return response.data;
};

export default {
  getRecipients,
  getRecipientById,
  createRecipient,
  updateRecipient,
  deleteRecipient,
  getRecipientStats,
  getRecipientDistributionHistory,
  exportRecipients,
};
