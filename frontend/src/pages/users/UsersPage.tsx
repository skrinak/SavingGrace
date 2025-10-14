/**
 * Users Page - Placeholder (Admin Only)
 */

import React from 'react';

const UsersPage: React.FC = () => {
  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
            <p className="mt-1 text-sm text-gray-600">Manage system users and permissions</p>
          </div>
          <button className="btn-primary">+ Add User</button>
        </div>

        <div className="card">
          <div className="text-center py-12 text-gray-500">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <p className="mt-4">User list will be displayed here</p>
            <p className="text-sm mt-2">Create, edit, and manage user accounts</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UsersPage;
