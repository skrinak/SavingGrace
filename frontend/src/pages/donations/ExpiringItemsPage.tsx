/**
 * Expiring Items Page
 * Displays items that are expiring soon with visual alerts
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getExpiringDonations } from '../../services/donationService';
import type { ExpiringDonation, FoodCategory } from '../../types/donation';

const ExpiringItemsPage: React.FC = () => {
  const [items, setItems] = useState<ExpiringDonation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dayFilter, setDayFilter] = useState<number>(7);

  useEffect(() => {
    fetchExpiringItems();
  }, [dayFilter]);

  const fetchExpiringItems = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getExpiringDonations(dayFilter);
      setItems(response.items);
    } catch (err) {
      console.error('Error fetching expiring items:', err);
      setError('Failed to load expiring items. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const getUrgencyClass = (daysUntilExpiry: number): string => {
    if (daysUntilExpiry < 0) {
      return 'bg-red-100 border-red-300 text-red-900';
    } else if (daysUntilExpiry <= 1) {
      return 'bg-red-50 border-red-200 text-red-800';
    } else if (daysUntilExpiry <= 3) {
      return 'bg-orange-50 border-orange-200 text-orange-800';
    } else {
      return 'bg-yellow-50 border-yellow-200 text-yellow-800';
    }
  };

  const getUrgencyBadge = (daysUntilExpiry: number): { label: string; class: string } => {
    if (daysUntilExpiry < 0) {
      return { label: 'EXPIRED', class: 'bg-red-600 text-white' };
    } else if (daysUntilExpiry === 0) {
      return { label: 'EXPIRES TODAY', class: 'bg-red-500 text-white' };
    } else if (daysUntilExpiry === 1) {
      return { label: 'EXPIRES TOMORROW', class: 'bg-orange-500 text-white' };
    } else if (daysUntilExpiry <= 3) {
      return { label: `${daysUntilExpiry} DAYS LEFT`, class: 'bg-orange-400 text-white' };
    } else {
      return { label: `${daysUntilExpiry} DAYS LEFT`, class: 'bg-yellow-400 text-gray-900' };
    }
  };

  const getCategoryLabel = (category: FoodCategory): string => {
    const labels: Record<FoodCategory, string> = {
      produce: 'Produce',
      dairy: 'Dairy',
      protein: 'Protein',
      grains: 'Grains',
      canned: 'Canned',
      frozen: 'Frozen',
      beverages: 'Beverages',
      bakery: 'Bakery',
      prepared: 'Prepared',
      other: 'Other',
    };
    return labels[category];
  };

  const groupedItems = items.reduce((acc, item) => {
    const key = item.daysUntilExpiry < 0 ? 'expired' :
                item.daysUntilExpiry <= 1 ? 'critical' :
                item.daysUntilExpiry <= 3 ? 'warning' : 'upcoming';
    if (!acc[key]) acc[key] = [];
    acc[key].push(item);
    return acc;
  }, {} as Record<string, ExpiringDonation[]>);

  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
            <Link to="/donations" className="hover:text-primary-600">
              Donations
            </Link>
            <span>/</span>
            <span className="text-gray-900">Expiring Items</span>
          </div>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Expiring Items</h1>
              <p className="mt-1 text-sm text-gray-600">
                Monitor items nearing expiration to minimize waste
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Show items expiring in:</span>
              <select
                value={dayFilter}
                onChange={(e) => setDayFilter(Number(e.target.value))}
                className="input-field w-auto"
              >
                <option value={3}>3 days</option>
                <option value={7}>7 days</option>
                <option value={14}>14 days</option>
                <option value={30}>30 days</option>
              </select>
            </div>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="card bg-red-50 border border-red-200">
            <h3 className="text-sm font-medium text-red-900">Expired</h3>
            <p className="mt-2 text-3xl font-bold text-red-600">
              {groupedItems.expired?.length || 0}
            </p>
          </div>
          <div className="card bg-orange-50 border border-orange-200">
            <h3 className="text-sm font-medium text-orange-900">Critical (0-1 days)</h3>
            <p className="mt-2 text-3xl font-bold text-orange-600">
              {groupedItems.critical?.length || 0}
            </p>
          </div>
          <div className="card bg-yellow-50 border border-yellow-200">
            <h3 className="text-sm font-medium text-yellow-900">Warning (2-3 days)</h3>
            <p className="mt-2 text-3xl font-bold text-yellow-600">
              {groupedItems.warning?.length || 0}
            </p>
          </div>
          <div className="card">
            <h3 className="text-sm font-medium text-gray-500">Upcoming (4+ days)</h3>
            <p className="mt-2 text-3xl font-bold text-gray-900">
              {groupedItems.upcoming?.length || 0}
            </p>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        {/* Items List */}
        {isLoading ? (
          <div className="card text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            <p className="mt-4 text-gray-600">Loading expiring items...</p>
          </div>
        ) : items.length === 0 ? (
          <div className="card text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-green-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">All clear!</h3>
            <p className="mt-2 text-sm text-gray-600">
              No items expiring in the next {dayFilter} days
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Expired Items */}
            {groupedItems.expired && groupedItems.expired.length > 0 && (
              <div>
                <h2 className="text-lg font-semibold text-red-900 mb-3">
                  Expired Items ({groupedItems.expired.length})
                </h2>
                <div className="space-y-3">
                  {groupedItems.expired.map((item) => {
                    const urgency = getUrgencyBadge(item.daysUntilExpiry);
                    return (
                      <div
                        key={item.itemId}
                        className={`border rounded-md p-4 ${getUrgencyClass(
                          item.daysUntilExpiry
                        )}`}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <span
                                className={`inline-flex px-2 py-1 text-xs font-bold rounded ${urgency.class}`}
                              >
                                {urgency.label}
                              </span>
                              <h3 className="font-semibold">{item.itemName}</h3>
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              <div>
                                <span className="font-medium">Donor:</span>
                                <Link
                                  to={`/donations/${item.donationId}`}
                                  className="ml-2 hover:underline"
                                >
                                  {item.donorName}
                                </Link>
                              </div>
                              <div>
                                <span className="font-medium">Category:</span>
                                <span className="ml-2">{getCategoryLabel(item.category)}</span>
                              </div>
                              <div>
                                <span className="font-medium">Quantity:</span>
                                <span className="ml-2">
                                  {item.quantity} {item.unit}
                                </span>
                              </div>
                              <div>
                                <span className="font-medium">Expiration:</span>
                                <span className="ml-2">
                                  {new Date(item.expirationDate).toLocaleDateString()}
                                </span>
                              </div>
                              {item.storageLocation && (
                                <div className="col-span-2">
                                  <span className="font-medium">Location:</span>
                                  <span className="ml-2">{item.storageLocation}</span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Critical Items */}
            {groupedItems.critical && groupedItems.critical.length > 0 && (
              <div>
                <h2 className="text-lg font-semibold text-orange-900 mb-3">
                  Critical - Expires in 0-1 Days ({groupedItems.critical.length})
                </h2>
                <div className="space-y-3">
                  {groupedItems.critical.map((item) => {
                    const urgency = getUrgencyBadge(item.daysUntilExpiry);
                    return (
                      <div
                        key={item.itemId}
                        className={`border rounded-md p-4 ${getUrgencyClass(
                          item.daysUntilExpiry
                        )}`}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <span
                                className={`inline-flex px-2 py-1 text-xs font-bold rounded ${urgency.class}`}
                              >
                                {urgency.label}
                              </span>
                              <h3 className="font-semibold">{item.itemName}</h3>
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              <div>
                                <span className="font-medium">Donor:</span>
                                <Link
                                  to={`/donations/${item.donationId}`}
                                  className="ml-2 hover:underline"
                                >
                                  {item.donorName}
                                </Link>
                              </div>
                              <div>
                                <span className="font-medium">Category:</span>
                                <span className="ml-2">{getCategoryLabel(item.category)}</span>
                              </div>
                              <div>
                                <span className="font-medium">Quantity:</span>
                                <span className="ml-2">
                                  {item.quantity} {item.unit}
                                </span>
                              </div>
                              <div>
                                <span className="font-medium">Expiration:</span>
                                <span className="ml-2">
                                  {new Date(item.expirationDate).toLocaleDateString()}
                                </span>
                              </div>
                              {item.storageLocation && (
                                <div className="col-span-2">
                                  <span className="font-medium">Location:</span>
                                  <span className="ml-2">{item.storageLocation}</span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Warning Items */}
            {groupedItems.warning && groupedItems.warning.length > 0 && (
              <div>
                <h2 className="text-lg font-semibold text-yellow-900 mb-3">
                  Warning - Expires in 2-3 Days ({groupedItems.warning.length})
                </h2>
                <div className="space-y-3">
                  {groupedItems.warning.map((item) => {
                    const urgency = getUrgencyBadge(item.daysUntilExpiry);
                    return (
                      <div
                        key={item.itemId}
                        className={`border rounded-md p-4 ${getUrgencyClass(
                          item.daysUntilExpiry
                        )}`}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <span
                                className={`inline-flex px-2 py-1 text-xs font-bold rounded ${urgency.class}`}
                              >
                                {urgency.label}
                              </span>
                              <h3 className="font-semibold">{item.itemName}</h3>
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              <div>
                                <span className="font-medium">Donor:</span>
                                <Link
                                  to={`/donations/${item.donationId}`}
                                  className="ml-2 hover:underline"
                                >
                                  {item.donorName}
                                </Link>
                              </div>
                              <div>
                                <span className="font-medium">Category:</span>
                                <span className="ml-2">{getCategoryLabel(item.category)}</span>
                              </div>
                              <div>
                                <span className="font-medium">Quantity:</span>
                                <span className="ml-2">
                                  {item.quantity} {item.unit}
                                </span>
                              </div>
                              <div>
                                <span className="font-medium">Expiration:</span>
                                <span className="ml-2">
                                  {new Date(item.expirationDate).toLocaleDateString()}
                                </span>
                              </div>
                              {item.storageLocation && (
                                <div className="col-span-2">
                                  <span className="font-medium">Location:</span>
                                  <span className="ml-2">{item.storageLocation}</span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Upcoming Items */}
            {groupedItems.upcoming && groupedItems.upcoming.length > 0 && (
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-3">
                  Upcoming - Expires in 4+ Days ({groupedItems.upcoming.length})
                </h2>
                <div className="space-y-3">
                  {groupedItems.upcoming.map((item) => {
                    const urgency = getUrgencyBadge(item.daysUntilExpiry);
                    return (
                      <div key={item.itemId} className="card">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <span
                                className={`inline-flex px-2 py-1 text-xs font-bold rounded ${urgency.class}`}
                              >
                                {urgency.label}
                              </span>
                              <h3 className="font-semibold">{item.itemName}</h3>
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              <div>
                                <span className="text-gray-600">Donor:</span>
                                <Link
                                  to={`/donations/${item.donationId}`}
                                  className="ml-2 text-primary-600 hover:text-primary-900"
                                >
                                  {item.donorName}
                                </Link>
                              </div>
                              <div>
                                <span className="text-gray-600">Category:</span>
                                <span className="ml-2">{getCategoryLabel(item.category)}</span>
                              </div>
                              <div>
                                <span className="text-gray-600">Quantity:</span>
                                <span className="ml-2">
                                  {item.quantity} {item.unit}
                                </span>
                              </div>
                              <div>
                                <span className="text-gray-600">Expiration:</span>
                                <span className="ml-2">
                                  {new Date(item.expirationDate).toLocaleDateString()}
                                </span>
                              </div>
                              {item.storageLocation && (
                                <div className="col-span-2">
                                  <span className="text-gray-600">Location:</span>
                                  <span className="ml-2">{item.storageLocation}</span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ExpiringItemsPage;
