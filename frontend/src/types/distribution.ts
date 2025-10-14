/**
 * Distribution Type Definitions
 */

export type DistributionStatus = 'planned' | 'in-progress' | 'completed' | 'cancelled';

export interface DistributionItem {
  inventoryItemId: string;
  itemName: string;
  category: string;
  quantity: number;
  unit: string;
}

export interface Distribution {
  distributionId: string;
  recipientId: string;
  recipientName: string;
  date: string;
  status: DistributionStatus;
  items: DistributionItem[];
  notes?: string;
  completedBy?: string;
  completedAt?: string;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  updatedBy: string;
}

export interface CreateDistributionRequest {
  recipientId: string;
  date: string;
  items: Array<{
    inventoryItemId: string;
    quantity: number;
  }>;
  notes?: string;
}

export interface UpdateDistributionRequest {
  status?: DistributionStatus;
  date?: string;
  items?: Array<{
    inventoryItemId: string;
    quantity: number;
  }>;
  notes?: string;
}

export interface DistributionListParams {
  search?: string;
  recipientId?: string;
  status?: DistributionStatus;
  startDate?: string;
  endDate?: string;
  limit?: number;
  lastKey?: string;
}

export interface DistributionListResponse {
  distributions: Distribution[];
  lastKey?: string;
  total: number;
}
