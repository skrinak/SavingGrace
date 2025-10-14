/**
 * Dashboard Page
 * Main landing page after login showing key metrics and recent activity
 */

import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

const DashboardPage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-sm text-gray-600">
          Welcome back, {user?.firstName} {user?.lastName}
        </p>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {/* Metric Cards */}
          <div className="card">
            <h3 className="text-sm font-medium text-gray-500">Total Donations</h3>
            <p className="mt-2 text-3xl font-bold text-gray-900">0</p>
            <p className="mt-1 text-sm text-gray-600">This month</p>
          </div>

          <div className="card">
            <h3 className="text-sm font-medium text-gray-500">Distributions</h3>
            <p className="mt-2 text-3xl font-bold text-gray-900">0</p>
            <p className="mt-1 text-sm text-gray-600">This month</p>
          </div>

          <div className="card">
            <h3 className="text-sm font-medium text-gray-500">Meals Provided</h3>
            <p className="mt-2 text-3xl font-bold text-gray-900">0</p>
            <p className="mt-1 text-sm text-gray-600">This month</p>
          </div>

          <div className="card">
            <h3 className="text-sm font-medium text-gray-500">Households Served</h3>
            <p className="mt-2 text-3xl font-bold text-gray-900">0</p>
            <p className="mt-1 text-sm text-gray-600">This month</p>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="mt-8">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
            <div className="text-center py-12 text-gray-500">
              <p>No recent activity</p>
              <p className="text-sm mt-2">Activity will appear here as you use the system</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
