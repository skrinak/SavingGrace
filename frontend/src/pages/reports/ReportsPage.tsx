/**
 * Reports Page - Placeholder
 */

import React from 'react';

const ReportsPage: React.FC = () => {
  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900">Reports & Analytics</h1>
        <p className="mt-2 text-sm text-gray-600">View reports and export data</p>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Donation Report</h3>
            <p className="text-sm text-gray-600 mb-4">Track donations over time</p>
            <button className="btn-primary">Generate Report</button>
          </div>
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Distribution Report</h3>
            <p className="text-sm text-gray-600 mb-4">View distribution statistics</p>
            <button className="btn-primary">Generate Report</button>
          </div>
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Impact Report</h3>
            <p className="text-sm text-gray-600 mb-4">Measure community impact</p>
            <button className="btn-primary">Generate Report</button>
          </div>
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Custom Report</h3>
            <p className="text-sm text-gray-600 mb-4">Create custom reports</p>
            <button className="btn-primary">Create Report</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
