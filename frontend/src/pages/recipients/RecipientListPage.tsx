/**
 * Recipient List Page
 * Displays recipients with PII masking for privacy
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { getRecipients, deleteRecipient, exportRecipients } from '../../services/recipientService';
import type { RecipientListItem, RecipientStatus, EligibilityStatus } from '../../types/recipient';

const RecipientListPage: React.FC = () => {
  const navigate = useNavigate();
  const { hasPermission } = useAuth();

  const [recipients, setRecipients] = useState<RecipientListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<RecipientStatus | ''>('');
  const [filterEligibility, setFilterEligibility] = useState<EligibilityStatus | ''>('');
  const [lastKey, setLastKey] = useState<string | undefined>(undefined);
  const [hasMore, setHasMore] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const canWrite = hasPermission('recipients:write');
  const canDelete = hasPermission('recipients:delete');

  const fetchRecipients = async (append = false) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await getRecipients({
        search: searchTerm || undefined,
        status: filterStatus || undefined,
        eligibilityStatus: filterEligibility || undefined,
        limit: 20,
        lastKey: append ? lastKey : undefined,
      });

      if (append) {
        setRecipients((prev) => [...prev, ...response.recipients]);
      } else {
        setRecipients(response.recipients);
      }

      setLastKey(response.lastKey);
      setHasMore(!!response.lastKey);
    } catch (err) {
      console.error('Error fetching recipients:', err);
      setError('Failed to load recipients. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRecipients();
  }, [searchTerm, filterStatus, filterEligibility]);

  const handleDelete = async (recipientId: string) => {
    if (deleteConfirm !== recipientId) {
      setDeleteConfirm(recipientId);
      setTimeout(() => setDeleteConfirm(null), 3000);
      return;
    }

    try {
      await deleteRecipient(recipientId);
      setRecipients((prev) => prev.filter((r) => r.recipientId !== recipientId));
      setDeleteConfirm(null);
    } catch (err) {
      console.error('Error deleting recipient:', err);
      setError('Failed to delete recipient. Please try again.');
    }
  };

  const handleExport = async () => {
    try {
      setIsExporting(true);
      const blob = await exportRecipients({
        search: searchTerm || undefined,
        status: filterStatus || undefined,
        eligibilityStatus: filterEligibility || undefined,
      });

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `recipients-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error exporting recipients:', err);
      setError('Failed to export recipients. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  const getStatusBadgeClass = (status: RecipientStatus): string => {
    const classes: Record<RecipientStatus, string> = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      suspended: 'bg-red-100 text-red-800',
    };
    return classes[status];
  };

  const getEligibilityBadgeClass = (status: EligibilityStatus): string => {
    const classes: Record<EligibilityStatus, string> = {
      eligible: 'bg-blue-100 text-blue-800',
      pending: 'bg-yellow-100 text-yellow-800',
      ineligible: 'bg-gray-100 text-gray-800',
    };
    return classes[status];
  };

  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Recipients</h1>
            <p className="mt-1 text-sm text-gray-600">Manage recipient households (privacy protected)</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleExport}
              disabled={isExporting || recipients.length === 0}
              className="btn-secondary flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              {isExporting ? 'Exporting...' : 'Export'}
            </button>
            {canWrite && (
              <button onClick={() => navigate('/recipients/new')} className="btn-primary flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add Recipient
              </button>
            )}
          </div>
        </div>

        <div className="card mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="search" className="form-label">Search</label>
              <input
                id="search"
                type="text"
                placeholder="Search by name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input-field"
              />
            </div>
            <div>
              <label htmlFor="status" className="form-label">Status</label>
              <select
                id="status"
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value as RecipientStatus | '')}
                className="input-field"
              >
                <option value="">All Statuses</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="suspended">Suspended</option>
              </select>
            </div>
            <div>
              <label htmlFor="eligibility" className="form-label">Eligibility</label>
              <select
                id="eligibility"
                value={filterEligibility}
                onChange={(e) => setFilterEligibility(e.target.value as EligibilityStatus | '')}
                className="input-field"
              >
                <option value="">All</option>
                <option value="eligible">Eligible</option>
                <option value="pending">Pending</option>
                <option value="ineligible">Ineligible</option>
              </select>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        {isLoading && recipients.length === 0 ? (
          <div className="card text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            <p className="mt-4 text-gray-600">Loading recipients...</p>
          </div>
        ) : recipients.length === 0 ? (
          <div className="card text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">No recipients found</h3>
            <p className="mt-2 text-sm text-gray-600">
              {searchTerm || filterStatus || filterEligibility ? 'Try adjusting your filters' : 'Get started by adding your first recipient'}
            </p>
          </div>
        ) : (
          <>
            <div className="bg-white shadow-md rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Recipient</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contact (Protected)</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Household</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Distribution</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {recipients.map((recipient) => (
                    <tr key={recipient.recipientId} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Link to={`/recipients/${recipient.recipientId}`} className="text-sm font-medium text-primary-600 hover:text-primary-900">
                          {recipient.firstName} {recipient.lastNameInitial}
                        </Link>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">***-***-{recipient.phoneLastFour}</div>
                        <div className="text-sm text-gray-500">{recipient.cityState}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-gray-900">{recipient.householdSize} members</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-col gap-1">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadgeClass(recipient.status)}`}>
                            {recipient.status}
                          </span>
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getEligibilityBadgeClass(recipient.eligibilityStatus)}`}>
                            {recipient.eligibilityStatus}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {recipient.lastDistributionDate ? new Date(recipient.lastDistributionDate).toLocaleDateString() : 'Never'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex justify-end gap-2">
                          <Link to={`/recipients/${recipient.recipientId}`} className="text-primary-600 hover:text-primary-900">View</Link>
                          {canWrite && (
                            <Link to={`/recipients/${recipient.recipientId}/edit`} className="text-gray-600 hover:text-gray-900">Edit</Link>
                          )}
                          {canDelete && (
                            <button
                              onClick={() => handleDelete(recipient.recipientId)}
                              className={`${deleteConfirm === recipient.recipientId ? 'text-red-600 font-semibold' : 'text-red-600 hover:text-red-900'}`}
                            >
                              {deleteConfirm === recipient.recipientId ? 'Confirm?' : 'Delete'}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {hasMore && (
              <div className="mt-6 text-center">
                <button onClick={() => fetchRecipients(true)} disabled={isLoading} className="btn-secondary">
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

export default RecipientListPage;
