/**
 * Authentication and user types
 */

export type UserRole =
  | 'Admin'
  | 'DonorCoordinator'
  | 'DistributionManager'
  | 'Volunteer'
  | 'ReadOnly';

export interface User {
  userId: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  status: 'active' | 'inactive' | 'suspended';
  emailVerified: boolean;
  phoneNumber?: string;
  mfaEnabled: boolean;
  createdAt: string;
  updatedAt: string;
  lastLoginAt?: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  idToken: string;
  expiresIn: number;
}

export interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignupData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  phoneNumber?: string;
}

export interface ResetPasswordData {
  email: string;
  code: string;
  newPassword: string;
}

export interface ChangePasswordData {
  oldPassword: string;
  newPassword: string;
}

// Permission checks based on role hierarchy
export const ROLE_HIERARCHY: Record<UserRole, number> = {
  Admin: 5,
  DonorCoordinator: 4,
  DistributionManager: 3,
  Volunteer: 2,
  ReadOnly: 1,
};

// Permission definitions
export type Permission =
  | 'users:read'
  | 'users:write'
  | 'users:delete'
  | 'donors:read'
  | 'donors:write'
  | 'donors:delete'
  | 'donations:read'
  | 'donations:write'
  | 'donations:delete'
  | 'recipients:read'
  | 'recipients:write'
  | 'recipients:delete'
  | 'distributions:read'
  | 'distributions:write'
  | 'distributions:delete'
  | 'inventory:read'
  | 'inventory:write'
  | 'reports:read'
  | 'reports:export';

export const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  Admin: [
    'users:read',
    'users:write',
    'users:delete',
    'donors:read',
    'donors:write',
    'donors:delete',
    'donations:read',
    'donations:write',
    'donations:delete',
    'recipients:read',
    'recipients:write',
    'recipients:delete',
    'distributions:read',
    'distributions:write',
    'distributions:delete',
    'inventory:read',
    'inventory:write',
    'reports:read',
    'reports:export',
  ],
  DonorCoordinator: [
    'donors:read',
    'donors:write',
    'donations:read',
    'donations:write',
    'inventory:read',
    'inventory:write',
    'reports:read',
  ],
  DistributionManager: [
    'recipients:read',
    'recipients:write',
    'distributions:read',
    'distributions:write',
    'inventory:read',
    'reports:read',
  ],
  Volunteer: [
    'donors:read',
    'donations:read',
    'recipients:read',
    'distributions:read',
    'inventory:read',
  ],
  ReadOnly: [
    'donors:read',
    'donations:read',
    'recipients:read',
    'distributions:read',
    'inventory:read',
    'reports:read',
  ],
};
