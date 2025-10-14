/**
 * Main App Component
 * Configures routing and authentication
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { configureAmplify } from './config/amplify';
import ProtectedRoute from './components/common/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';

// Auth pages
import LoginPage from './pages/auth/LoginPage';
import SignupPage from './pages/auth/SignupPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';

// Dashboard
import DashboardPage from './pages/dashboard/DashboardPage';

// Donors
import DonorListPage from './pages/donors/DonorListPage';
import DonorFormPage from './pages/donors/DonorFormPage';
import DonorDetailPage from './pages/donors/DonorDetailPage';

// Donations
import DonationListPage from './pages/donations/DonationListPage';
import DonationFormPage from './pages/donations/DonationFormPage';
import DonationDetailPage from './pages/donations/DonationDetailPage';
import ExpiringItemsPage from './pages/donations/ExpiringItemsPage';

// Recipients
import RecipientListPage from './pages/recipients/RecipientListPage';
import RecipientFormPage from './pages/recipients/RecipientFormPage';
import RecipientDetailPage from './pages/recipients/RecipientDetailPage';

// Distributions
import DistributionListPage from './pages/distributions/DistributionListPage';
import DistributionFormPage from './pages/distributions/DistributionFormPage';
import DistributionDetailPage from './pages/distributions/DistributionDetailPage';

// Configure AWS Amplify on app initialization
configureAmplify();

const App: React.FC = () => {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />

          {/* Protected routes */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<DashboardPage />} />

            {/* Donors */}
            <Route
              path="/donors"
              element={
                <ProtectedRoute requirePermission="donors:read">
                  <DonorListPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/donors/new"
              element={
                <ProtectedRoute requirePermission="donors:write">
                  <DonorFormPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/donors/:donorId"
              element={
                <ProtectedRoute requirePermission="donors:read">
                  <DonorDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/donors/:donorId/edit"
              element={
                <ProtectedRoute requirePermission="donors:write">
                  <DonorFormPage />
                </ProtectedRoute>
              }
            />

            {/* Donations */}
            <Route
              path="/donations"
              element={
                <ProtectedRoute requirePermission="donations:read">
                  <DonationListPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/donations/new"
              element={
                <ProtectedRoute requirePermission="donations:write">
                  <DonationFormPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/donations/expiring"
              element={
                <ProtectedRoute requirePermission="donations:read">
                  <ExpiringItemsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/donations/:donationId"
              element={
                <ProtectedRoute requirePermission="donations:read">
                  <DonationDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/donations/:donationId/edit"
              element={
                <ProtectedRoute requirePermission="donations:write">
                  <DonationFormPage />
                </ProtectedRoute>
              }
            />

            {/* Recipients */}
            <Route
              path="/recipients"
              element={
                <ProtectedRoute requirePermission="recipients:read">
                  <RecipientListPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/recipients/new"
              element={
                <ProtectedRoute requirePermission="recipients:write">
                  <RecipientFormPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/recipients/:recipientId"
              element={
                <ProtectedRoute requirePermission="recipients:read">
                  <RecipientDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/recipients/:recipientId/edit"
              element={
                <ProtectedRoute requirePermission="recipients:write">
                  <RecipientFormPage />
                </ProtectedRoute>
              }
            />

            {/* Distributions */}
            <Route
              path="/distributions"
              element={
                <ProtectedRoute requirePermission="distributions:read">
                  <DistributionListPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/distributions/new"
              element={
                <ProtectedRoute requirePermission="distributions:write">
                  <DistributionFormPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/distributions/:distributionId"
              element={
                <ProtectedRoute requirePermission="distributions:read">
                  <DistributionDetailPage />
                </ProtectedRoute>
              }
            />

            {/* Inventory */}
            <Route
              path="/inventory"
              element={
                <ProtectedRoute requirePermission="inventory:read">
                  <div className="p-6">
                    <h1 className="text-2xl font-bold">Inventory</h1>
                    <p className="mt-2 text-gray-600">Inventory dashboard coming soon</p>
                  </div>
                </ProtectedRoute>
              }
            />

            {/* Reports */}
            <Route
              path="/reports"
              element={
                <ProtectedRoute requirePermission="reports:read">
                  <div className="p-6">
                    <h1 className="text-2xl font-bold">Reports</h1>
                    <p className="mt-2 text-gray-600">Reports and analytics coming soon</p>
                  </div>
                </ProtectedRoute>
              }
            />

            {/* Users */}
            <Route
              path="/users"
              element={
                <ProtectedRoute requirePermission="users:read">
                  <div className="p-6">
                    <h1 className="text-2xl font-bold">User Management</h1>
                    <p className="mt-2 text-gray-600">User administration coming soon</p>
                  </div>
                </ProtectedRoute>
              }
            />

            {/* Profile */}
            <Route
              path="/profile"
              element={
                <div className="p-6">
                  <h1 className="text-2xl font-bold">Profile Settings</h1>
                  <p className="mt-2 text-gray-600">Profile management coming soon</p>
                </div>
              }
            />
          </Route>

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* 404 */}
          <Route
            path="*"
            element={
              <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="card max-w-md">
                  <h1 className="text-4xl font-bold text-gray-900 mb-4">404</h1>
                  <p className="text-gray-600 mb-4">Page not found</p>
                  <a href="/dashboard" className="btn-primary">
                    Go to Dashboard
                  </a>
                </div>
              </div>
            }
          />
        </Routes>
      </AuthProvider>
    </Router>
  );
};

export default App;
