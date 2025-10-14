/**
 * Donation Detail Page
 * Displays detailed donation information with receipt upload
 */

import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { getDonationById, deleteDonation, uploadReceiptComplete } from '../../services/donationService';
import type { Donation, FoodCategory, DonationStatus } from '../../types/donation';

const DonationDetailPage: React.FC = () => {
  const { donationId } = useParams<{ donationId: string }>();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();

  const [donation, setDonation] = useState<Donation | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [isUploadingReceipt, setIsUploadingReceipt] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const canWrite = hasPermission('donations:write');
  const canDelete = hasPermission('donations:delete');

  useEffect(() => {
    if (donationId) {
      loadDonation(donationId);
    }
  }, [donationId]);

  const loadDonation = async (id: string) => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await getDonationById(id);
      setDonation(data);
    } catch (err) {
      console.error('Error loading donation:', err);
      setError('Failed to load donation details. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirm) {
      setDeleteConfirm(true);
      setTimeout(() => setDeleteConfirm(false), 5000);
      return;
    }

    if (!donationId) return;

    try {
      await deleteDonation(donationId);
      navigate('/donations');
    } catch (err) {
      console.error('Error deleting donation:', err);
      setError('Failed to delete donation. Please try again.');
      setDeleteConfirm(false);
    }
  };

  const handleReceiptUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !donationId) return;

    // Validate file type
    if (!file.type.startsWith('image/') && file.type !== 'application/pdf') {
      setUploadError('Please upload an image or PDF file');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setUploadError('File size must be less than 5MB');
      return;
    }

    setIsUploadingReceipt(true);
    setUploadError(null);

    try {
      const receiptUrl = await uploadReceiptComplete(donationId, file);

      // Update local state
      if (donation) {
        setDonation({ ...donation, receiptUrl });
      }
    } catch (err) {
      console.error('Error uploading receipt:', err);
      setUploadError('Failed to upload receipt. Please try again.');
    } finally {
      setIsUploadingReceipt(false);
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error || !donation) {
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
              <h3 className="mt-4 text-lg font-medium text-gray-900">Error loading donation</h3>
              <p className="mt-2 text-sm text-gray-600">{error || 'Donation not found'}</p>
              <Link to="/donations" className="mt-4 inline-block btn-primary">
                Back to Donations
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
            <Link to="/donations" className="hover:text-primary-600">
              Donations
            </Link>
            <span>/</span>
            <span className="text-gray-900">
              {donation.donorName} - {new Date(donation.date).toLocaleDateString()}
            </span>
          </div>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{donation.donorName}</h1>
              <div className="flex items-center gap-3 mt-2">
                <span
                  className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getStatusBadgeClass(
                    donation.status
                  )}`}
                >
                  {donation.status}
                </span>
                <span className="text-sm text-gray-600">
                  {new Date(donation.date).toLocaleDateString()}
                </span>
              </div>
            </div>
            <div className="flex gap-2">
              {canWrite && (
                <Link to={`/donations/${donationId}/edit`} className="btn-secondary">
                  Edit Donation
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
            {/* Donated Items */}
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Donated Items</h2>
              <div className="space-y-4">
                {donation.items.map((item, index) => (
                  <div key={item.itemId} className="border border-gray-200 rounded-md p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="text-base font-medium text-gray-900">{item.name}</h3>
                        <p className="text-sm text-gray-600">{getCategoryLabel(item.category)}</p>
                      </div>
                      <p className="text-base font-semibold text-gray-900">
                        ${item.estimatedValue.toFixed(2)}
                      </p>
                    </div>
                    <div className="grid grid-cols-2 gap-2 mt-3 text-sm">
                      <div>
                        <span className="text-gray-500">Quantity:</span>
                        <span className="ml-2 text-gray-900">
                          {item.quantity} {item.unit}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Expires:</span>
                        <span className="ml-2 text-gray-900">
                          {new Date(item.expirationDate).toLocaleDateString()}
                        </span>
                      </div>
                      {item.storageLocation && (
                        <div className="col-span-2">
                          <span className="text-gray-500">Storage:</span>
                          <span className="ml-2 text-gray-900">{item.storageLocation}</span>
                        </div>
                      )}
                      {item.notes && (
                        <div className="col-span-2">
                          <span className="text-gray-500">Notes:</span>
                          <span className="ml-2 text-gray-900">{item.notes}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Pickup Details */}
            {(donation.pickupLocation || donation.pickupTime || donation.notes) && (
              <div className="card">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Pickup Details</h2>
                <div className="space-y-3">
                  {donation.pickupLocation && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">Location</p>
                      <p className="text-sm text-gray-900">{donation.pickupLocation}</p>
                    </div>
                  )}
                  {donation.pickupTime && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">Time</p>
                      <p className="text-sm text-gray-900">{donation.pickupTime}</p>
                    </div>
                  )}
                  {donation.notes && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">Notes</p>
                      <p className="text-sm text-gray-900">{donation.notes}</p>
                    </div>
                  )}
                  {donation.receivedBy && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">Received By</p>
                      <p className="text-sm text-gray-900">{donation.receivedBy}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Summary */}
            <div className="card">
              <h3 className="text-sm font-medium text-gray-500 mb-3">Summary</h3>
              <div className="space-y-3">
                <div>
                  <p className="text-2xl font-bold text-gray-900">{donation.items.length}</p>
                  <p className="text-xs text-gray-500">Items</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">
                    ${donation.totalValue.toFixed(2)}
                  </p>
                  <p className="text-xs text-gray-500">Total Value</p>
                </div>
              </div>
            </div>

            {/* Receipt */}
            <div className="card">
              <h3 className="text-sm font-medium text-gray-500 mb-3">Receipt</h3>
              {donation.receiptUrl ? (
                <div className="space-y-3">
                  <a
                    href={donation.receiptUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block"
                  >
                    {donation.receiptUrl.toLowerCase().endsWith('.pdf') ? (
                      <div className="border border-gray-200 rounded-md p-4 text-center hover:bg-gray-50 transition">
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
                            d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                          />
                        </svg>
                        <p className="mt-2 text-sm text-gray-600">View PDF Receipt</p>
                      </div>
                    ) : (
                      <img
                        src={donation.receiptUrl}
                        alt="Receipt"
                        className="w-full rounded-md border border-gray-200"
                      />
                    )}
                  </a>
                  {canWrite && (
                    <label className="btn-secondary w-full text-center cursor-pointer block">
                      Replace Receipt
                      <input
                        type="file"
                        accept="image/*,application/pdf"
                        onChange={handleReceiptUpload}
                        className="hidden"
                        disabled={isUploadingReceipt}
                      />
                    </label>
                  )}
                </div>
              ) : (
                <div>
                  {canWrite ? (
                    <label className="btn-primary w-full text-center cursor-pointer block">
                      {isUploadingReceipt ? 'Uploading...' : 'Upload Receipt'}
                      <input
                        type="file"
                        accept="image/*,application/pdf"
                        onChange={handleReceiptUpload}
                        className="hidden"
                        disabled={isUploadingReceipt}
                      />
                    </label>
                  ) : (
                    <p className="text-sm text-gray-500">No receipt uploaded</p>
                  )}
                </div>
              )}
              {uploadError && (
                <p className="text-sm text-red-600 mt-2">{uploadError}</p>
              )}
            </div>

            {/* Timeline */}
            <div className="card">
              <h3 className="text-sm font-medium text-gray-500 mb-3">Timeline</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <p className="text-gray-500">Created</p>
                  <p className="text-gray-900">
                    {new Date(donation.createdAt).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Last Updated</p>
                  <p className="text-gray-900">
                    {new Date(donation.updatedAt).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>

            {/* Donor Link */}
            <div className="card">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Donor</h3>
              <Link
                to={`/donors/${donation.donorId}`}
                className="text-primary-600 hover:text-primary-900 font-medium"
              >
                {donation.donorName}
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DonationDetailPage;
