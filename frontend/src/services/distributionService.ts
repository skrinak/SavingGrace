/**
 * Distribution Service
 */

import apiClient from './apiClient';
import type { ApiResponse } from '../types/api';
import type {
  Distribution,
  CreateDistributionRequest,
  UpdateDistributionRequest,
  DistributionListParams,
  DistributionListResponse,
} from '../types/distribution';

export const getDistributions = async (params?: DistributionListParams): Promise<DistributionListResponse> => {
  const queryParams = new URLSearchParams();
  if (params?.search) queryParams.append('search', params.search);
  if (params?.recipientId) queryParams.append('recipientId', params.recipientId);
  if (params?.status) queryParams.append('status', params.status);
  if (params?.startDate) queryParams.append('startDate', params.startDate);
  if (params?.endDate) queryParams.append('endDate', params.endDate);
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.lastKey) queryParams.append('lastKey', params.lastKey);

  const url = `/distributions${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await apiClient.get<ApiResponse<DistributionListResponse>>(url);
  return response.data.data;
};

export const getDistributionById = async (distributionId: string): Promise<Distribution> => {
  const response = await apiClient.get<ApiResponse<Distribution>>(`/distributions/${distributionId}`);
  return response.data.data;
};

export const createDistribution = async (data: CreateDistributionRequest): Promise<Distribution> => {
  const response = await apiClient.post<ApiResponse<Distribution>>('/distributions', data);
  return response.data.data;
};

export const updateDistribution = async (distributionId: string, data: UpdateDistributionRequest): Promise<Distribution> => {
  const response = await apiClient.put<ApiResponse<Distribution>>(`/distributions/${distributionId}`, data);
  return response.data.data;
};

export const completeDistribution = async (distributionId: string): Promise<Distribution> => {
  const response = await apiClient.post<ApiResponse<Distribution>>(`/distributions/${distributionId}/complete`, {});
  return response.data.data;
};

export const cancelDistribution = async (distributionId: string): Promise<void> => {
  await apiClient.delete(`/distributions/${distributionId}`);
};

export default {
  getDistributions,
  getDistributionById,
  createDistribution,
  updateDistribution,
  completeDistribution,
  cancelDistribution,
};
