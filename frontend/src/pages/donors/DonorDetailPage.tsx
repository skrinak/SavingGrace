/**
 * Donor Detail Page
 * Displays detailed donor information and donation history
 */

import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { getDonorById, getDonorDonations, deleteDonor } from '../../services/donorService';
import type { Donor, DonorType, DonorStatus } from '../../types/donor';

const DonorDetailPage: React.FC = () => {
  const { donorId } = useParams<{ donorId: string }>();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();

  const [donor, setDonor] = useState<Donor | null>(null);
  const [donations, setDonations] = useState<
    Array<{
      donationId: string;
      date: string;
      items: Array<{ name: string; quantity: number; unit: string }>;
      status: string;
      estimatedValue: number;
    }>
  >([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingDonations, setIsLoadingDonations] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastKey, setLastKey] = useState<string | undefined>(undefined);
  const [hasMore, setHasMore] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  const canWrite = hasPermission('donors:write');
  const canDelete = hasPermission('donors:delete');

  useEffect(() => {
    if (donorId) {
      loadDonor(donorId);
      loadDonations(donorId);
    }
  }, [donorId]);

  const loadDonor = async (id: string) => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await getDonorById(id);
      setDonor(data);
    } catch (err) {
      console.error('Error loading donor:', err);
      setError('Failed to load donor details. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadDonations = async (id: string, append = false) => {
    try {
      setIsLoadingDonations(true);
      const response = await getDonorDonations(id, {
        limit: 10,
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
      console.error('Error loading donations:', err);
      // Don't set error for donations since it's not critical
    } finally {
      setIsLoadingDonations(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirm) {
      setDeleteConfirm(true);
      setTimeout(() => setDeleteConfirm(false), 5000);
      return;
    }

    if (!donorId) return;

    try {
      await deleteDonor(donorId);
      navigate('/donors');
    } catch (err) {
      console.error('Error deleting donor:', err);
      setError('Failed to delete donor. Please try again.');
      setDeleteConfirm(false);
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error || !donor) {
    return (
      <div className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="card">
            <div className="text-center py-12">
              <svg
                className="mx-auto h-12 w-12 text-red-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <h3 className="mt-4 text-lg font-medium text-gray-900">Error loading donor</h3>
              <p className="mt-2 text-sm text-gray-600">{error || 'Donor not found'}</p>
              <Link to="/donors" className="mt-4 inline-block btn-primary">
                Back to Donors
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
            <Link to="/donors" className="hover:text-primary-600">
              Donors
            </Link>
            <span>/</span>
            <span className="text-gray-900">{donor.name}</span>
          </div>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{donor.name}</h1>
              <div className="flex items-center gap-3 mt-2">
                <span
                  className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getStatusBadgeClass(
                    donor.status
                  )}`}
                >
                  {donor.status}
                </span>
                <span className="text-sm text-gray-600">{getDonorTypeLabel(donor.type)}</span>
              </div>
            </div>
            <div className="flex gap-2">
              {canWrite && (
                <Link to={`/donors/${donorId}/edit`} className="btn-secondary">
                  Edit Donor
                </Link>
              )}
              {canDelete && (
                <button
                  onClick={handleDelete}
                  className={`${
                    deleteConfirm
                      ? 'bg-red-600 text-white hover:bg-red-700'
                      : 'bg-red-50 text-red-600 hover:bg-red-100'
                  } px-4 py-2 rounded-md transition-colors`}
                >
                  {deleteConfirm ? 'Confirm Delete?' : 'Delete'}
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Info */}
          <div className="lg:col-span-2 space-y-6">
            {/* Contact Information */}
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Email</p>
                  <a
                    href={`mailto:${donor.email}`}
                    className="text-sm text-primary-600 hover:text-primary-900"
                  >
                    {donor.email}
                  </a>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Phone</p>
                  <a
                    href={`tel:${donor.phone}`}
                    className="text-sm text-primary-600 hover:text-primary-900"
                  >
                    {donor.phone}
                  </a>
                </div>
                {donor.website && (
                  <div className="sm:col-span-2">
                    <p className="text-sm font-medium text-gray-500">Website</p>
                    <a
                      href={donor.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-primary-600 hover:text-primary-900"
                    >
                      {donor.website}
                    </a>
                  </div>
                )}
              </div>
            </div>

            {/* Address */}
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Address</h2>
              <div className="text-sm text-gray-900">
                <p>{donor.address.street}</p>
                <p>
                  {donor.address.city}, {donor.address.state} {donor.address.zipCode}
                </p>
                <p>{donor.address.country}</p>
              </div>
            </div>

            {/* Additional Contacts */}
            {donor.contacts && donor.contacts.length > 0 && (
              <div className="card">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Additional Contacts</h2>
                <div className="space-y-4">
                  {donor.contacts.map((contact, index) => (
                    <div key={index} className="border-b border-gray-200 last:border-0 pb-4 last:pb-0">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {contact.name}
                            {contact.isPrimary && (
                              <span className="ml-2 inline-flex px-2 py-0.5 text-xs font-semibold rounded-full bg-primary-100 text-primary-800">
                                Primary
                              </span>
                            )}
                          </p>
                          {contact.title && <p className="text-xs text-gray-500">{contact.title}</p>}
                        </div>
                      </div>
                      <div className="mt-2 text-sm text-gray-600">
                        <p>{contact.email}</p>
                        <p>{contact.phone}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Additional Details */}
            {(donor.taxId ||
              donor.licenseNumber ||
              donor.preferredPickupTimes ||
              donor.specialInstructions ||
              donor.notes) && (
              <div className="card">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Additional Details</h2>
                <div className="space-y-3">
                  {donor.taxId && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">Tax ID / EIN</p>
                      <p className="text-sm text-gray-900">{donor.taxId}</p>
                    </div>
                  )}
                  {donor.licenseNumber && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">License Number</p>
                      <p className="text-sm text-gray-900">{donor.licenseNumber}</p>
                    </div>
                  )}
                  {donor.preferredPickupTimes && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">Preferred Pickup Times</p>
                      <p className="text-sm text-gray-900">{donor.preferredPickupTimes}</p>
                    </div>
                  )}
                  {donor.specialInstructions && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">Special Instructions</p>
                      <p className="text-sm text-gray-900">{donor.specialInstructions}</p>
                    </div>
                  )}
                  {donor.notes && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">Internal Notes</p>
                      <p className="text-sm text-gray-900">{donor.notes}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Donation History */}
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Donation History</h2>

              {isLoadingDonations && donations.length === 0 ? (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                  <p className="mt-2 text-sm text-gray-600">Loading donations...</p>
                </div>
              ) : donations.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>No donations recorded yet</p>
                </div>
              ) : (
                <>
                  <div className="space-y-4">
                    {donations.map((donation) => (
                      <div
                        key={donation.donationId}
                        className="border border-gray-200 rounded-md p-4"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <Link
                              to={`/donations/${donation.donationId}`}
                              className="text-sm font-medium text-primary-600 hover:text-primary-900"
                            >
                              {new Date(donation.date).toLocaleDateString()}
                            </Link>
                            <p className="text-xs text-gray-500 mt-1">
                              Status: {donation.status}
                            </p>
                          </div>
                          <p className="text-sm font-semibold text-gray-900">
                            ${donation.estimatedValue.toFixed(2)}
                          </p>
                        </div>
                        <div className="mt-2">
                          <p className="text-xs text-gray-500 mb-1">Items:</p>
                          <ul className="text-sm text-gray-900 space-y-1">
                            {donation.items.map((item, idx) => (
                              <li key={idx}>
                                {item.name} - {item.quantity} {item.unit}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ))}
                  </div>

                  {hasMore && (
                    <div className="mt-4 text-center">
                      <button
                        onClick={() => donorId && loadDonations(donorId, true)}
                        disabled={isLoadingDonations}
                        className="btn-secondary text-sm"
                      >
                        {isLoadingDonations ? 'Loading...' : 'Load More'}
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Stats */}
            <div className="card">
              <h3 className="text-sm font-medium text-gray-500 mb-3">Statistics</h3>
              <div className="space-y-3">
                <div>
                  <p className="text-2xl font-bold text-gray-900">
                    {donor.totalDonations || 0}
                  </p>
                  <p className="text-xs text-gray-500">Total Donations</p>
                </div>
                <div>
                  <p className="text-sm text-gray-900">
                    {donor.lastDonationDate
                      ? new Date(donor.lastDonationDate).toLocaleDateString()
                      : 'Never'}
                  </p>
                  <p className="text-xs text-gray-500">Last Donation</p>
                </div>
              </div>
            </div>

            {/* Timeline */}
            <div className="card">
              <h3 className="text-sm font-medium text-gray-500 mb-3">Timeline</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <p className="text-gray-500">Created</p>
                  <p className="text-gray-900">
                    {new Date(donor.createdAt).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Last Updated</p>
                  <p className="text-gray-900">
                    {new Date(donor.updatedAt).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DonorDetailPage;
