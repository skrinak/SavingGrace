/**
 * Donor List Page
 * Displays all donors with search, filtering, and pagination
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { getDonors, deleteDonor, exportDonors } from '../../services/donorService';
import type { Donor, DonorType, DonorStatus } from '../../types/donor';

const DonorListPage: React.FC = () => {
  const navigate = useNavigate();
  const { hasPermission } = useAuth();

  const [donors, setDonors] = useState<Donor[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<DonorType | ''>('');
  const [filterStatus, setFilterStatus] = useState<DonorStatus | ''>('');
  const [lastKey, setLastKey] = useState<string | undefined>(undefined);
  const [hasMore, setHasMore] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const canWrite = hasPermission('donors:write');
  const canDelete = hasPermission('donors:delete');

  const fetchDonors = async (append = false) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await getDonors({
        search: searchTerm || undefined,
        type: filterType || undefined,
        status: filterStatus || undefined,
        limit: 20,
        lastKey: append ? lastKey : undefined,
      });

      if (append) {
        setDonors((prev) => [...prev, ...response.donors]);
      } else {
        setDonors(response.donors);
      }

      setLastKey(response.lastKey);
      setHasMore(!!response.lastKey);
    } catch (err) {
      console.error('Error fetching donors:', err);
      setError('Failed to load donors. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDonors();
  }, [searchTerm, filterType, filterStatus]);

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    setLastKey(undefined);
  };

  const handleDelete = async (donorId: string) => {
    if (deleteConfirm !== donorId) {
      setDeleteConfirm(donorId);
      setTimeout(() => setDeleteConfirm(null), 3000);
      return;
    }

    try {
      await deleteDonor(donorId);
      setDonors((prev) => prev.filter((d) => d.donorId !== donorId));
      setDeleteConfirm(null);
    } catch (err) {
      console.error('Error deleting donor:', err);
      setError('Failed to delete donor. Please try again.');
    }
  };

  const handleExport = async () => {
    try {
      setIsExporting(true);
      const blob = await exportDonors({
        search: searchTerm || undefined,
        type: filterType || undefined,
        status: filterStatus || undefined,
      });

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `donors-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error exporting donors:', err);
      setError('Failed to export donors. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  const getDonorTypeLabel = (type: DonorType): string => {
    const labels: Record<DonorType, string> = {
      individual: 'Individual',
      restaurant: 'Restaurant',
      grocery: 'Grocery Store',
      farm: 'Farm',
      manufacturer: 'Manufacturer',
      other: 'Other',
    };
    return labels[type];
  };

  const getStatusBadgeClass = (status: DonorStatus): string => {
    const classes: Record<DonorStatus, string> = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      suspended: 'bg-red-100 text-red-800',
    };
    return classes[status];
  };

  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Donors</h1>
            <p className="mt-1 text-sm text-gray-600">
              Manage donor organizations and individuals
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleExport}
              disabled={isExporting || donors.length === 0}
              className="btn-secondary flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              {isExporting ? 'Exporting...' : 'Export'}
            </button>
            {canWrite && (
              <button
                onClick={() => navigate('/donors/new')}
                className="btn-primary flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add Donor
              </button>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="card mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="search" className="form-label">
                Search
              </label>
              <input
                id="search"
                type="text"
                placeholder="Search by name, email, or phone..."
                value={searchTerm}
                onChange={(e) => handleSearch(e.target.value)}
                className="input-field"
              />
            </div>
            <div>
              <label htmlFor="type" className="form-label">
                Donor Type
              </label>
              <select
                id="type"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value as DonorType | '')}
                className="input-field"
              >
                <option value="">All Types</option>
                <option value="individual">Individual</option>
                <option value="restaurant">Restaurant</option>
                <option value="grocery">Grocery Store</option>
                <option value="farm">Farm</option>
                <option value="manufacturer">Manufacturer</option>
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
                onChange={(e) => setFilterStatus(e.target.value as DonorStatus | '')}
                className="input-field"
              >
                <option value="">All Statuses</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="suspended">Suspended</option>
              </select>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        {/* Donor List */}
        {isLoading && donors.length === 0 ? (
          <div className="card text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            <p className="mt-4 text-gray-600">Loading donors...</p>
          </div>
        ) : donors.length === 0 ? (
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
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">No donors found</h3>
            <p className="mt-2 text-sm text-gray-600">
              {searchTerm || filterType || filterStatus
                ? 'Try adjusting your search or filters'
                : 'Get started by adding your first donor'}
            </p>
            {canWrite && !searchTerm && !filterType && !filterStatus && (
              <button
                onClick={() => navigate('/donors/new')}
                className="mt-4 btn-primary inline-flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add First Donor
              </button>
            )}
          </div>
        ) : (
          <>
            <div className="bg-white shadow-md rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Donor
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Contact
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Donation
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {donors.map((donor) => (
                    <tr key={donor.donorId} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Link
                          to={`/donors/${donor.donorId}`}
                          className="text-sm font-medium text-primary-600 hover:text-primary-900"
                        >
                          {donor.name}
                        </Link>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-gray-900">
                          {getDonorTypeLabel(donor.type)}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">{donor.email}</div>
                        <div className="text-sm text-gray-500">{donor.phone}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadgeClass(
                            donor.status
                          )}`}
                        >
                          {donor.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {donor.lastDonationDate
                          ? new Date(donor.lastDonationDate).toLocaleDateString()
                          : 'Never'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex justify-end gap-2">
                          <Link
                            to={`/donors/${donor.donorId}`}
                            className="text-primary-600 hover:text-primary-900"
                          >
                            View
                          </Link>
                          {canWrite && (
                            <Link
                              to={`/donors/${donor.donorId}/edit`}
                              className="text-gray-600 hover:text-gray-900"
                            >
                              Edit
                            </Link>
                          )}
                          {canDelete && (
                            <button
                              onClick={() => handleDelete(donor.donorId)}
                              className={`${
                                deleteConfirm === donor.donorId
                                  ? 'text-red-600 font-semibold'
                                  : 'text-red-600 hover:text-red-900'
                              }`}
                            >
                              {deleteConfirm === donor.donorId ? 'Confirm?' : 'Delete'}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Load More */}
            {hasMore && (
              <div className="mt-6 text-center">
                <button
                  onClick={() => fetchDonors(true)}
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

export default DonorListPage;
