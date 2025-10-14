/**
 * Donation List Page
 * Displays all donations with search, filtering, and pagination
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { getDonations, deleteDonation, exportDonations } from '../../services/donationService';
import type { Donation, FoodCategory, DonationStatus } from '../../types/donation';

const DonationListPage: React.FC = () => {
  const navigate = useNavigate();
  const { hasPermission } = useAuth();

  const [donations, setDonations] = useState<Donation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState<FoodCategory | ''>('');
  const [filterStatus, setFilterStatus] = useState<DonationStatus | ''>('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [lastKey, setLastKey] = useState<string | undefined>(undefined);
  const [hasMore, setHasMore] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const canWrite = hasPermission('donations:write');
  const canDelete = hasPermission('donations:delete');

  const fetchDonations = async (append = false) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await getDonations({
        search: searchTerm || undefined,
        category: filterCategory || undefined,
        status: filterStatus || undefined,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
        limit: 20,
        lastKey: append ? lastKey : undefined,
      });

      if (append) {
        setDonations((prev) => [...prev, ...response.donations]);
      } else {
        setDonations(response.donations);
      }

      setLastKey(response.lastKey);
      setHasMore(!!response.lastKey);
    } catch (err) {
      console.error('Error fetching donations:', err);
      setError('Failed to load donations. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDonations();
  }, [searchTerm, filterCategory, filterStatus, startDate, endDate]);

  const handleDelete = async (donationId: string) => {
    if (deleteConfirm !== donationId) {
      setDeleteConfirm(donationId);
      setTimeout(() => setDeleteConfirm(null), 3000);
      return;
    }

    try {
      await deleteDonation(donationId);
      setDonations((prev) => prev.filter((d) => d.donationId !== donationId));
      setDeleteConfirm(null);
    } catch (err) {
      console.error('Error deleting donation:', err);
      setError('Failed to delete donation. Please try again.');
    }
  };

  const handleExport = async () => {
    try {
      setIsExporting(true);
      const blob = await exportDonations({
        search: searchTerm || undefined,
        category: filterCategory || undefined,
        status: filterStatus || undefined,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
      });

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `donations-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error exporting donations:', err);
      setError('Failed to export donations. Please try again.');
    } finally {
      setIsExporting(false);
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

  const getStatusBadgeClass = (status: DonationStatus): string => {
    const classes: Record<DonationStatus, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      received: 'bg-green-100 text-green-800',
      distributed: 'bg-blue-100 text-blue-800',
      expired: 'bg-red-100 text-red-800',
      cancelled: 'bg-gray-100 text-gray-800',
    };
    return classes[status];
  };

  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Donations</h1>
            <p className="mt-1 text-sm text-gray-600">Track food donations and inventory</p>
          </div>
          <div className="flex gap-2">
            <Link to="/donations/expiring" className="btn-secondary flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              Expiring Items
            </Link>
            <button
              onClick={handleExport}
              disabled={isExporting || donations.length === 0}
              className="btn-secondary flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              {isExporting ? 'Exporting...' : 'Export'}
            </button>
            {canWrite && (
              <button
                onClick={() => navigate('/donations/new')}
                className="btn-primary flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                Record Donation
              </button>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="card mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div>
              <label htmlFor="search" className="form-label">
                Search
              </label>
              <input
                id="search"
                type="text"
                placeholder="Search by donor..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input-field"
              />
            </div>
            <div>
              <label htmlFor="category" className="form-label">
                Category
              </label>
              <select
                id="category"
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value as FoodCategory | '')}
                className="input-field"
              >
                <option value="">All Categories</option>
                <option value="produce">Produce</option>
                <option value="dairy">Dairy</option>
                <option value="protein">Protein</option>
                <option value="grains">Grains</option>
                <option value="canned">Canned</option>
                <option value="frozen">Frozen</option>
                <option value="beverages">Beverages</option>
                <option value="bakery">Bakery</option>
                <option value="prepared">Prepared</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label htmlFor="status" className="form-label">
                Status
              </label>
              <select
                id="status"
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value as DonationStatus | '')}
                className="input-field"
              >
                <option value="">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="received">Received</option>
                <option value="distributed">Distributed</option>
                <option value="expired">Expired</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
            <div>
              <label htmlFor="startDate" className="form-label">
                Start Date
              </label>
              <input
                id="startDate"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="input-field"
              />
            </div>
            <div>
              <label htmlFor="endDate" className="form-label">
                End Date
              </label>
              <input
                id="endDate"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="input-field"
              />
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        {/* Donation List */}
        {isLoading && donations.length === 0 ? (
          <div className="card text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            <p className="mt-4 text-gray-600">Loading donations...</p>
          </div>
        ) : donations.length === 0 ? (
          <div className="card text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
              />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">No donations found</h3>
            <p className="mt-2 text-sm text-gray-600">
              {searchTerm || filterCategory || filterStatus || startDate || endDate
                ? 'Try adjusting your search or filters'
                : 'Get started by recording your first donation'}
            </p>
            {canWrite && !searchTerm && !filterCategory && !filterStatus && (
              <button
                onClick={() => navigate('/donations/new')}
                className="mt-4 btn-primary inline-flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                Record First Donation
              </button>
            )}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {donations.map((donation) => (
                <div key={donation.donationId} className="card hover:shadow-lg transition-shadow">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <Link
                        to={`/donations/${donation.donationId}`}
                        className="text-lg font-semibold text-primary-600 hover:text-primary-900"
                      >
                        {donation.donorName}
                      </Link>
                      <p className="text-sm text-gray-500">
                        {new Date(donation.date).toLocaleDateString()}
                      </p>
                    </div>
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadgeClass(
                        donation.status
                      )}`}
                    >
                      {donation.status}
                    </span>
                  </div>

                  <div className="space-y-2 mb-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Items:</span>
                      <span className="font-medium">{donation.items.length}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Value:</span>
                      <span className="font-medium">${donation.totalValue.toFixed(2)}</span>
                    </div>
                    {donation.receiptUrl && (
                      <div className="text-sm text-green-600">
                        <svg
                          className="w-4 h-4 inline mr-1"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                        Receipt attached
                      </div>
                    )}
                  </div>

                  <div className="flex justify-end gap-2 pt-3 border-t border-gray-200">
                    <Link
                      to={`/donations/${donation.donationId}`}
                      className="text-sm text-primary-600 hover:text-primary-900"
                    >
                      View
                    </Link>
                    {canWrite && (
                      <Link
                        to={`/donations/${donation.donationId}/edit`}
                        className="text-sm text-gray-600 hover:text-gray-900"
                      >
                        Edit
                      </Link>
                    )}
                    {canDelete && (
                      <button
                        onClick={() => handleDelete(donation.donationId)}
                        className={`text-sm ${
                          deleteConfirm === donation.donationId
                            ? 'text-red-600 font-semibold'
                            : 'text-red-600 hover:text-red-900'
                        }`}
                      >
                        {deleteConfirm === donation.donationId ? 'Confirm?' : 'Delete'}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Load More */}
            {hasMore && (
              <div className="mt-6 text-center">
                <button
                  onClick={() => fetchDonations(true)}
                  disabled={isLoading}
                  className="btn-secondary"
                >
                  {isLoading ? 'Loading...' : 'Load More'}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default DonationListPage;
