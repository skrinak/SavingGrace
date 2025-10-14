/**
 * Inventory Page - Placeholder
 */

import React from 'react';

const InventoryPage: React.FC = () => {
  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900">Inventory Dashboard</h1>
        <p className="mt-2 text-sm text-gray-600">Inventory management interface</p>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="card">
            <h3 className="text-sm font-medium text-gray-500">Total Items</h3>
            <p className="mt-2 text-3xl font-bold text-gray-900">0</p>
          </div>
          <div className="card">
            <h3 className="text-sm font-medium text-gray-500">Expiring Soon</h3>
            <p className="mt-2 text-3xl font-bold text-yellow-600">0</p>
          </div>
          <div className="card">
            <h3 className="text-sm font-medium text-gray-500">Low Stock</h3>
            <p className="mt-2 text-3xl font-bold text-red-600">0</p>
          </div>
        </div>

        <div className="mt-6 card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Inventory by Category</h2>
          <p className="text-gray-600">Category breakdown will be displayed here</p>
        </div>
      </div>
    </div>
  );
};

export default InventoryPage;
