/**
 * Authentication Service
 * Wraps AWS Amplify Auth methods and provides typed interfaces
 */

import {
  signIn,
  signUp,
  confirmSignUp,
  signOut,
  resetPassword,
  confirmResetPassword,
  getCurrentUser,
  fetchAuthSession,
  updatePassword,
  resendSignUpCode,
} from 'aws-amplify/auth';
import type {
  LoginCredentials,
  SignupData,
  ResetPasswordData,
  ChangePasswordData,
  AuthTokens,
  User,
} from '../types/auth';

/**
 * Sign in with email and password
 */
export const login = async (
  credentials: LoginCredentials
): Promise<{ requiresMFA: boolean; session?: string }> => {
  try {
    const result = await signIn({
      username: credentials.email,
      password: credentials.password,
    });

    return {
      requiresMFA: !result.isSignedIn,
      session: result.nextStep?.signInStep,
    };
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

/**
 * Sign up new user
 */
export const signup = async (data: SignupData): Promise<{ userId: string }> => {
  try {
    const result = await signUp({
      username: data.email,
      password: data.password,
      options: {
        userAttributes: {
          email: data.email,
          given_name: data.firstName,
          family_name: data.lastName,
          ...(data.phoneNumber && { phone_number: data.phoneNumber }),
        },
      },
    });

    return {
      userId: result.userId || '',
    };
  } catch (error) {
    console.error('Signup error:', error);
    throw error;
  }
};

/**
 * Confirm sign up with verification code
 */
export const confirmSignup = async (
  email: string,
  code: string
): Promise<void> => {
  try {
    await confirmSignUp({
      username: email,
      confirmationCode: code,
    });
  } catch (error) {
    console.error('Confirm signup error:', error);
    throw error;
  }
};

/**
 * Resend verification code
 */
export const resendVerificationCode = async (email: string): Promise<void> => {
  try {
    await resendSignUpCode({ username: email });
  } catch (error) {
    console.error('Resend code error:', error);
    throw error;
  }
};

/**
 * Sign out user
 */
export const logout = async (): Promise<void> => {
  try {
    await signOut();
  } catch (error) {
    console.error('Logout error:', error);
    throw error;
  }
};

/**
 * Initiate password reset
 */
export const initiatePasswordReset = async (email: string): Promise<void> => {
  try {
    await resetPassword({ username: email });
  } catch (error) {
    console.error('Password reset error:', error);
    throw error;
  }
};

/**
 * Confirm password reset with code
 */
export const confirmPasswordReset = async (
  data: ResetPasswordData
): Promise<void> => {
  try {
    await confirmResetPassword({
      username: data.email,
      confirmationCode: data.code,
      newPassword: data.newPassword,
    });
  } catch (error) {
    console.error('Confirm password reset error:', error);
    throw error;
  }
};

/**
 * Change password for authenticated user
 */
export const changePassword = async (
  data: ChangePasswordData
): Promise<void> => {
  try {
    await updatePassword({
      oldPassword: data.oldPassword,
      newPassword: data.newPassword,
    });
  } catch (error) {
    console.error('Change password error:', error);
    throw error;
  }
};

/**
 * Get current authenticated user
 */
export const getCurrentAuthUser = async (): Promise<User | null> => {
  try {
    const cognitoUser = await getCurrentUser();
    const session = await fetchAuthSession();

    if (!cognitoUser || !session.tokens) {
      return null;
    }

    // Extract user attributes from ID token
    const idToken = session.tokens.idToken?.payload;

    const user: User = {
      userId: cognitoUser.userId,
      email: (idToken?.email as string) || '',
      firstName: (idToken?.given_name as string) || '',
      lastName: (idToken?.family_name as string) || '',
      role: ((idToken?.['custom:role'] as string) || 'ReadOnly') as User['role'],
      status: 'active',
      emailVerified: (idToken?.email_verified as boolean) || false,
      phoneNumber: (idToken?.phone_number as string) || undefined,
      mfaEnabled: false, // This would need to be fetched from user settings
      createdAt: '',
      updatedAt: '',
      lastLoginAt: new Date().toISOString(),
    };

    return user;
  } catch (error) {
    console.error('Get current user error:', error);
    return null;
  }
};

/**
 * Get authentication tokens
 */
export const getAuthTokens = async (): Promise<AuthTokens | null> => {
  try {
    const session = await fetchAuthSession();

    if (!session.tokens) {
      return null;
    }

    return {
      accessToken: session.tokens.accessToken.toString(),
      refreshToken: session.tokens.refreshToken?.toString() || '',
      idToken: session.tokens.idToken?.toString() || '',
      expiresIn: 3600, // Default 1 hour, can be extracted from token
    };
  } catch (error) {
    console.error('Get auth tokens error:', error);
    return null;
  }
};

/**
 * Refresh authentication session
 */
export const refreshSession = async (): Promise<AuthTokens | null> => {
  try {
    const session = await fetchAuthSession({ forceRefresh: true });

    if (!session.tokens) {
      return null;
    }

    return {
      accessToken: session.tokens.accessToken.toString(),
      refreshToken: session.tokens.refreshToken?.toString() || '',
      idToken: session.tokens.idToken?.toString() || '',
      expiresIn: 3600,
    };
  } catch (error) {
    console.error('Refresh session error:', error);
    return null;
  }
};
