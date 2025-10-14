/**
 * Forgot Password Page
 * Password reset flow with verification code
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const ForgotPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const { initiatePasswordReset, confirmPasswordReset, clearError } = useAuth();

  const [step, setStep] = useState<'request' | 'reset'>('request');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    setIsLoading(true);

    try {
      await initiatePasswordReset(email.trim());
      setStep('reset');
    } catch (err) {
      console.error('Password reset request error:', err);
      setError(
        err instanceof Error ? err.message : 'Failed to send reset code. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const validatePassword = (): string | null => {
    if (newPassword.length < 8) {
      return 'Password must be at least 8 characters long';
    }

    if (!/(?=.*[a-z])/.test(newPassword)) {
      return 'Password must contain at least one lowercase letter';
    }

    if (!/(?=.*[A-Z])/.test(newPassword)) {
      return 'Password must contain at least one uppercase letter';
    }

    if (!/(?=.*\d)/.test(newPassword)) {
      return 'Password must contain at least one number';
    }

    if (!/(?=.*[@$!%*?&#])/.test(newPassword)) {
      return 'Password must contain at least one special character (@$!%*?&#)';
    }

    if (newPassword !== confirmPassword) {
      return 'Passwords do not match';
    }

    return null;
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!code || code.length < 6) {
      setError('Please enter the 6-digit verification code');
      return;
    }

    const passwordError = validatePassword();
    if (passwordError) {
      setError(passwordError);
      return;
    }

    setIsLoading(true);

    try {
      await confirmPasswordReset({
        email: email.trim(),
        code: code.trim(),
        newPassword,
      });

      // Navigate to login with success message
      navigate('/login', {
        state: { message: 'Password reset successful! Please sign in with your new password.' },
      });
    } catch (err) {
      console.error('Password reset error:', err);
      setError(
        err instanceof Error ? err.message : 'Failed to reset password. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendCode = async () => {
    setError(null);
    setIsLoading(true);

    try {
      await initiatePasswordReset(email);
      setError('Reset code sent! Please check your email.');
    } catch (err) {
      console.error('Resend code error:', err);
      setError('Failed to resend code. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (step === 'reset') {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <h1 className="text-center text-3xl font-bold text-gray-900">
            SavingGrace
          </h1>
          <h2 className="mt-6 text-center text-2xl font-semibold text-gray-700">
            Reset your password
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Enter the code sent to <strong>{email}</strong>
          </p>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="card">
            <form onSubmit={handleResetPassword} className="space-y-6">
              {error && (
                <div
                  className={`${
                    error.includes('sent')
                      ? 'bg-green-50 border-green-200 text-green-800'
                      : 'bg-red-50 border-red-200 text-red-800'
                  } border px-4 py-3 rounded-md text-sm`}
                >
                  {error}
                </div>
              )}

              <div>
                <label htmlFor="code" className="form-label">
                  Verification Code
                </label>
                <input
                  id="code"
                  name="code"
                  type="text"
                  required
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="input-field text-center text-2xl tracking-widest"
                  placeholder="000000"
                  maxLength={6}
                  disabled={isLoading}
                />
              </div>

              <div>
                <label htmlFor="newPassword" className="form-label">
                  New Password
                </label>
                <input
                  id="newPassword"
                  name="newPassword"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="input-field"
                  placeholder="••••••••"
                  disabled={isLoading}
                />
                <p className="mt-1 text-xs text-gray-500">
                  Must be 8+ characters with uppercase, lowercase, number, and special character
                </p>
              </div>

              <div>
                <label htmlFor="confirmPassword" className="form-label">
                  Confirm New Password
                </label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="input-field"
                  placeholder="••••••••"
                  disabled={isLoading}
                />
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full btn-primary flex justify-center items-center"
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Resetting password...
                    </>
                  ) : (
                    'Reset Password'
                  )}
                </button>
              </div>

              <div className="flex items-center justify-between text-sm">
                <button
                  type="button"
                  onClick={handleResendCode}
                  disabled={isLoading}
                  className="font-medium text-primary-600 hover:text-primary-500"
                >
                  Resend code
                </button>
                <Link
                  to="/login"
                  className="font-medium text-gray-600 hover:text-gray-500"
                >
                  Back to sign in
                </Link>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h1 className="text-center text-3xl font-bold text-gray-900">
          SavingGrace
        </h1>
        <h2 className="mt-6 text-center text-2xl font-semibold text-gray-700">
          Reset your password
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Enter your email and we'll send you a verification code
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="card">
          <form onSubmit={handleRequestReset} className="space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md text-sm">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="form-label">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setError(null);
                  clearError();
                }}
                className="input-field"
                placeholder="you@example.com"
                disabled={isLoading}
              />
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full btn-primary flex justify-center items-center"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Sending code...
                  </>
                ) : (
                  'Send Reset Code'
                )}
              </button>
            </div>

            <div className="text-center text-sm">
              <Link
                to="/login"
                className="font-medium text-primary-600 hover:text-primary-500"
              >
                Back to sign in
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
