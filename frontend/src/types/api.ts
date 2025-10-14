/**
 * API response types
 */

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: ApiError;
  pagination?: PaginationInfo;
}

export interface ApiError {
  message: string;
  code: string;
  details?: Record<string, unknown>;
}

export interface PaginationInfo {
  page: number;
  pageSize: number;
  totalCount: number;
  totalPages: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  nextPage?: number;
  previousPage?: number;
  lastEvaluatedKey?: Record<string, unknown>;
}

export interface PaginationParams {
  page?: number;
  pageSize?: number;
  lastEvaluatedKey?: Record<string, unknown>;
}

export interface ListResponse<T> {
  items: T[];
  pagination: PaginationInfo;
}

// HTTP request configuration
export interface RequestConfig {
  headers?: Record<string, string>;
  params?: Record<string, string | number | boolean>;
  timeout?: number;
  requiresAuth?: boolean;
}
