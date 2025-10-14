/**
 * Authentication Context
 * Provides authentication state and methods throughout the application
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type {
  AuthState,
  User,
  AuthTokens,
  LoginCredentials,
  SignupData,
  ResetPasswordData,
  ChangePasswordData,
  Permission,
  UserRole,
} from '../types/auth';
import { ROLE_PERMISSIONS } from '../types/auth';
import * as authService from '../services/authService';

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  signup: (data: SignupData) => Promise<{ userId: string }>;
  confirmSignup: (email: string, code: string) => Promise<void>;
  resendVerificationCode: (email: string) => Promise<void>;
  logout: () => Promise<void>;
  initiatePasswordReset: (email: string) => Promise<void>;
  confirmPasswordReset: (data: ResetPasswordData) => Promise<void>;
  changePassword: (data: ChangePasswordData) => Promise<void>;
  refreshTokens: () => Promise<void>;
  hasPermission: (permission: Permission) => boolean;
  hasRole: (role: UserRole | UserRole[]) => boolean;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    user: null,
    tokens: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  // Initialize authentication state
  const initializeAuth = useCallback(async () => {
    try {
      const user = await authService.getCurrentAuthUser();
      const tokens = await authService.getAuthTokens();

      if (user && tokens) {
        setState({
          user,
          tokens,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
      } else {
        setState({
          user: null,
          tokens: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
      }
    } catch (error) {
      console.error('Auth initialization error:', error);
      setState({
        user: null,
        tokens: null,
        isAuthenticated: false,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Authentication error',
      });
    }
  }, []);

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  // Login
  const login = async (credentials: LoginCredentials) => {
    try {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      await authService.login(credentials);

      // Fetch user and tokens after successful login
      const user = await authService.getCurrentAuthUser();
      const tokens = await authService.getAuthTokens();

      if (!user || !tokens) {
        throw new Error('Failed to retrieve user information');
      }

      setState({
        user,
        tokens,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      throw error;
    }
  };

  // Signup
  const signup = async (data: SignupData) => {
    try {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      const result = await authService.signup(data);

      setState((prev) => ({ ...prev, isLoading: false }));

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Signup failed';
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      throw error;
    }
  };

  // Confirm signup
  const confirmSignup = async (email: string, code: string) => {
    try {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      await authService.confirmSignup(email, code);

      setState((prev) => ({ ...prev, isLoading: false }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Verification failed';
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      throw error;
    }
  };

  // Resend verification code
  const resendVerificationCode = async (email: string) => {
    try {
      await authService.resendVerificationCode(email);
    } catch (error) {
      throw error;
    }
  };

  // Logout
  const logout = async () => {
    try {
      await authService.logout();

      setState({
        user: null,
        tokens: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Logout failed';
      setState((prev) => ({ ...prev, error: errorMessage }));
      throw error;
    }
  };

  // Initiate password reset
  const initiatePasswordReset = async (email: string) => {
    try {
      setState((prev) => ({ ...prev, error: null }));
      await authService.initiatePasswordReset(email);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Password reset failed';
      setState((prev) => ({ ...prev, error: errorMessage }));
      throw error;
    }
  };

  // Confirm password reset
  const confirmPasswordReset = async (data: ResetPasswordData) => {
    try {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      await authService.confirmPasswordReset(data);

      setState((prev) => ({ ...prev, isLoading: false }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Password reset failed';
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      throw error;
    }
  };

  // Change password
  const changePassword = async (data: ChangePasswordData) => {
    try {
      await authService.changePassword(data);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Password change failed';
      setState((prev) => ({ ...prev, error: errorMessage }));
      throw error;
    }
  };

  // Refresh tokens
  const refreshTokens = async () => {
    try {
      const tokens = await authService.refreshSession();

      if (tokens) {
        setState((prev) => ({ ...prev, tokens }));
      } else {
        // If refresh fails, log out user
        await logout();
      }
    } catch (error) {
      console.error('Token refresh error:', error);
      await logout();
    }
  };

  // Check if user has specific permission
  const hasPermission = (permission: Permission): boolean => {
    if (!state.user) return false;

    const userPermissions = ROLE_PERMISSIONS[state.user.role];
    return userPermissions.includes(permission);
  };

  // Check if user has specific role(s)
  const hasRole = (role: UserRole | UserRole[]): boolean => {
    if (!state.user) return false;

    if (Array.isArray(role)) {
      return role.includes(state.user.role);
    }

    return state.user.role === role;
  };

  // Clear error
  const clearError = () => {
    setState((prev) => ({ ...prev, error: null }));
  };

  const value: AuthContextType = {
    ...state,
    login,
    signup,
    confirmSignup,
    resendVerificationCode,
    logout,
    initiatePasswordReset,
    confirmPasswordReset,
    changePassword,
    refreshTokens,
    hasPermission,
    hasRole,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
