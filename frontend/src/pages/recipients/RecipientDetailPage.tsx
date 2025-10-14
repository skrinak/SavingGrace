/**
 * Recipient Detail Page
 * Displays detailed recipient information with distribution history
 */

import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { getRecipientById, getRecipientDistributionHistory, deleteRecipient } from '../../services/recipientService';
import type { Recipient, RecipientStatus, EligibilityStatus, RecipientDistribution } from '../../types/recipient';

const RecipientDetailPage: React.FC = () => {
  const { recipientId } = useParams<{ recipientId: string }>();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();

  const [recipient, setRecipient] = useState<Recipient | null>(null);
  const [distributions, setDistributions] = useState<RecipientDistribution[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingDistributions, setIsLoadingDistributions] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastKey, setLastKey] = useState<string | undefined>(undefined);
  const [hasMore, setHasMore] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  const canWrite = hasPermission('recipients:write');
  const canDelete = hasPermission('recipients:delete');

  useEffect(() => {
    if (recipientId) {
      loadRecipient(recipientId);
      loadDistributions(recipientId);
    }
  }, [recipientId]);

  const loadRecipient = async (id: string) => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await getRecipientById(id);
      setRecipient(data);
    } catch (err) {
      console.error('Error loading recipient:', err);
      setError('Failed to load recipient details. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadDistributions = async (id: string, append = false) => {
    try {
      setIsLoadingDistributions(true);
      const response = await getRecipientDistributionHistory(id, {
        limit: 10,
        lastKey: append ? lastKey : undefined,
      });

      if (append) {
        setDistributions((prev) => [...prev, ...response.distributions]);
      } else {
        setDistributions(response.distributions);
      }

      setLastKey(response.lastKey);
      setHasMore(!!response.lastKey);
    } catch (err) {
      console.error('Error loading distributions:', err);
    } finally {
      setIsLoadingDistributions(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirm) {
      setDeleteConfirm(true);
      setTimeout(() => setDeleteConfirm(false), 5000);
      return;
    }

    if (!recipientId) return;

    try {
      await deleteRecipient(recipientId);
      navigate('/recipients');
    } catch (err) {
      console.error('Error deleting recipient:', err);
      setError('Failed to delete recipient. Please try again.');
      setDeleteConfirm(false);
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error || !recipient) {
    return (
      <div className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="card">
            <div className="text-center py-12">
              <svg className="mx-auto h-12 w-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <h3 className="mt-4 text-lg font-medium text-gray-900">Error loading recipient</h3>
              <p className="mt-2 text-sm text-gray-600">{error || 'Recipient not found'}</p>
              <Link to="/recipients" className="mt-4 inline-block btn-primary">Back to Recipients</Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
            <Link to="/recipients" className="hover:text-primary-600">Recipients</Link>
            <span>/</span>
            <span className="text-gray-900">{recipient.firstName} {recipient.lastName}</span>
          </div>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{recipient.firstName} {recipient.lastName}</h1>
              <div className="flex items-center gap-3 mt-2">
                <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getStatusBadgeClass(recipient.status)}`}>
                  {recipient.status}
                </span>
                <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getEligibilityBadgeClass(recipient.eligibilityStatus)}`}>
                  {recipient.eligibilityStatus}
                </span>
              </div>
            </div>
            <div className="flex gap-2">
              {canWrite && (
                <Link to={`/recipients/${recipientId}/edit`} className="btn-secondary">Edit Recipient</Link>
              )}
              {canDelete && (
                <button onClick={handleDelete} className={`${deleteConfirm ? 'bg-red-600 text-white hover:bg-red-700' : 'bg-red-50 text-red-600 hover:bg-red-100'} px-4 py-2 rounded-md transition-colors`}>
                  {deleteConfirm ? 'Confirm Delete?' : 'Delete'}
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Phone</p>
                  <a href={`tel:${recipient.phone}`} className="text-sm text-primary-600 hover:text-primary-900">{recipient.phone}</a>
                </div>
                {recipient.email && (
                  <div>
                    <p className="text-sm font-medium text-gray-500">Email</p>
                    <a href={`mailto:${recipient.email}`} className="text-sm text-primary-600 hover:text-primary-900">{recipient.email}</a>
                  </div>
                )}
              </div>
            </div>

            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Address</h2>
              <div className="text-sm text-gray-900">
                <p>{recipient.address.street}</p>
                <p>{recipient.address.city}, {recipient.address.state} {recipient.address.zipCode}</p>
                <p>{recipient.address.country}</p>
              </div>
            </div>

            {recipient.dietaryRestrictions && recipient.dietaryRestrictions.length > 0 && (
              <div className="card">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Dietary Restrictions</h2>
                <div className="space-y-3">
                  {recipient.dietaryRestrictions.map((restriction, index) => (
                    <div key={index} className="border-b border-gray-200 last:border-0 pb-3 last:pb-0">
                      <p className="text-sm font-medium text-gray-900">{restriction.type}</p>
                      {restriction.notes && <p className="text-sm text-gray-600 mt-1">{restriction.notes}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {recipient.notes && (
              <div className="card">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Notes</h2>
                <p className="text-sm text-gray-900">{recipient.notes}</p>
              </div>
            )}

            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Distribution History</h2>
              {isLoadingDistributions && distributions.length === 0 ? (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                  <p className="mt-2 text-sm text-gray-600">Loading history...</p>
                </div>
              ) : distributions.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>No distributions recorded yet</p>
                </div>
              ) : (
                <>
                  <div className="space-y-4">
                    {distributions.map((distribution) => (
                      <div key={distribution.distributionId} className="border border-gray-200 rounded-md p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <Link to={`/distributions/${distribution.distributionId}`} className="text-sm font-medium text-primary-600 hover:text-primary-900">
                              {new Date(distribution.date).toLocaleDateString()}
                            </Link>
                            <p className="text-xs text-gray-500 mt-1">Status: {distribution.status}</p>
                          </div>
                          <p className="text-sm font-semibold text-gray-900">{distribution.items.length} items</p>
                        </div>
                        <div className="mt-2">
                          <p className="text-xs text-gray-500 mb-1">Items:</p>
                          <ul className="text-sm text-gray-900 space-y-1">
                            {distribution.items.map((item, idx) => (
                              <li key={idx}>{item.itemName} - {item.quantity} {item.unit}</li>
                            ))}
                          </ul>
                        </div>
                        {distribution.notes && (
                          <p className="mt-2 text-xs text-gray-600">{distribution.notes}</p>
                        )}
                      </div>
                    ))}
                  </div>
                  {hasMore && (
                    <div className="mt-4 text-center">
                      <button onClick={() => recipientId && loadDistributions(recipientId, true)} disabled={isLoadingDistributions} className="btn-secondary text-sm">
                        {isLoadingDistributions ? 'Loading...' : 'Load More'}
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <div className="card">
              <h3 className="text-sm font-medium text-gray-500 mb-3">Household</h3>
              <div className="space-y-3">
                <div>
                  <p className="text-2xl font-bold text-gray-900">{recipient.householdSize}</p>
                  <p className="text-xs text-gray-500">Members</p>
                </div>
              </div>
            </div>

            <div className="card">
              <h3 className="text-sm font-medium text-gray-500 mb-3">Statistics</h3>
              <div className="space-y-3">
                <div>
                  <p className="text-2xl font-bold text-gray-900">{recipient.totalDistributions || 0}</p>
                  <p className="text-xs text-gray-500">Total Distributions</p>
                </div>
                <div>
                  <p className="text-sm text-gray-900">{recipient.lastDistributionDate ? new Date(recipient.lastDistributionDate).toLocaleDateString() : 'Never'}</p>
                  <p className="text-xs text-gray-500">Last Distribution</p>
                </div>
              </div>
            </div>

            <div className="card">
              <h3 className="text-sm font-medium text-gray-500 mb-3">Timeline</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <p className="text-gray-500">Created</p>
                  <p className="text-gray-900">{new Date(recipient.createdAt).toLocaleDateString()}</p>
                </div>
                <div>
                  <p className="text-gray-500">Last Updated</p>
                  <p className="text-gray-900">{new Date(recipient.updatedAt).toLocaleDateString()}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecipientDetailPage;
