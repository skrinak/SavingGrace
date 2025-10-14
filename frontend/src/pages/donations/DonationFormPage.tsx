/**
 * Donation Form Page
 * Create or edit donation with multi-item entry
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getDonationById, createDonation, updateDonation } from '../../services/donationService';
import { getDonors } from '../../services/donorService';
import type { FoodCategory, CreateDonationItemRequest } from '../../types/donation';
import type { Donor } from '../../types/donor';

interface ItemFormData {
  name: string;
  category: FoodCategory;
  quantity: string;
  unit: string;
  estimatedValue: string;
  expirationDate: string;
  storageLocation: string;
  notes: string;
}

const DonationFormPage: React.FC = () => {
  const navigate = useNavigate();
  const { donationId } = useParams<{ donationId: string }>();
  const isEditMode = !!donationId;

  const [donorId, setDonorId] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [pickupLocation, setPickupLocation] = useState('');
  const [pickupTime, setPickupTime] = useState('');
  const [notes, setNotes] = useState('');
  const [items, setItems] = useState<ItemFormData[]>([
    {
      name: '',
      category: 'produce',
      quantity: '',
      unit: 'lbs',
      estimatedValue: '',
      expirationDate: '',
      storageLocation: '',
      notes: '',
    },
  ]);

  const [donors, setDonors] = useState<Donor[]>([]);
  const [isLoadingDonors, setIsLoadingDonors] = useState(true);
  const [isLoading, setIsLoading] = useState(isEditMode);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDonors();
    if (isEditMode && donationId) {
      loadDonation(donationId);
    }
  }, [donationId, isEditMode]);

  const loadDonors = async () => {
    try {
      setIsLoadingDonors(true);
      const response = await getDonors({ status: 'active', limit: 100 });
      setDonors(response.donors);
    } catch (err) {
      console.error('Error loading donors:', err);
      setError('Failed to load donors. Please try again.');
    } finally {
      setIsLoadingDonors(false);
    }
  };

  const loadDonation = async (id: string) => {
    try {
      setIsLoading(true);
      const donation = await getDonationById(id);

      setDonorId(donation.donorId);
      setDate(donation.date.split('T')[0]);
      setPickupLocation(donation.pickupLocation || '');
      setPickupTime(donation.pickupTime || '');
      setNotes(donation.notes || '');

      setItems(
        donation.items.map((item) => ({
          name: item.name,
          category: item.category,
          quantity: item.quantity.toString(),
          unit: item.unit,
          estimatedValue: item.estimatedValue.toString(),
          expirationDate: item.expirationDate.split('T')[0],
          storageLocation: item.storageLocation || '',
          notes: item.notes || '',
        }))
      );
    } catch (err) {
      console.error('Error loading donation:', err);
      setError('Failed to load donation. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const addItem = () => {
    setItems((prev) => [
      ...prev,
      {
        name: '',
        category: 'produce',
        quantity: '',
        unit: 'lbs',
        estimatedValue: '',
        expirationDate: '',
        storageLocation: '',
        notes: '',
      },
    ]);
  };

  const removeItem = (index: number) => {
    setItems((prev) => prev.filter((_, i) => i !== index));
  };

  const updateItem = (index: number, field: keyof ItemFormData, value: string) => {
    setItems((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const validateForm = (): string | null => {
    if (!donorId) return 'Please select a donor';
    if (!date) return 'Please select a date';
    if (items.length === 0) return 'Please add at least one item';

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (!item.name.trim()) return `Item ${i + 1}: Name is required`;
      if (!item.quantity || parseFloat(item.quantity) <= 0) {
        return `Item ${i + 1}: Valid quantity is required`;
      }
      if (!item.unit.trim()) return `Item ${i + 1}: Unit is required`;
      if (!item.estimatedValue || parseFloat(item.estimatedValue) < 0) {
        return `Item ${i + 1}: Valid estimated value is required`;
      }
      if (!item.expirationDate) return `Item ${i + 1}: Expiration date is required`;
    }

    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSaving(true);

    try {
      const requestItems: CreateDonationItemRequest[] = items.map((item) => ({
        name: item.name.trim(),
        category: item.category,
        quantity: parseFloat(item.quantity),
        unit: item.unit.trim(),
        estimatedValue: parseFloat(item.estimatedValue),
        expirationDate: new Date(item.expirationDate).toISOString(),
        storageLocation: item.storageLocation.trim() || undefined,
        notes: item.notes.trim() || undefined,
      }));

      const requestData = {
        donorId,
        date: new Date(date).toISOString(),
        items: requestItems,
        pickupLocation: pickupLocation.trim() || undefined,
        pickupTime: pickupTime.trim() || undefined,
        notes: notes.trim() || undefined,
      };

      if (isEditMode && donationId) {
        await updateDonation(donationId, requestData);
      } else {
        await createDonation(requestData);
      }

      navigate('/donations');
    } catch (err) {
      console.error('Error saving donation:', err);
      setError(`Failed to ${isEditMode ? 'update' : 'create'} donation. Please try again.`);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading || isLoadingDonors) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="py-6">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">
            {isEditMode ? 'Edit Donation' : 'Record New Donation'}
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            {isEditMode ? 'Update donation information' : 'Record a new food donation with multiple items'}
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Donation Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="donorId" className="form-label">
                  Donor *
                </label>
                <select
                  id="donorId"
                  required
                  value={donorId}
                  onChange={(e) => setDonorId(e.target.value)}
                  className="input-field"
                  disabled={isEditMode}
                >
                  <option value="">Select a donor...</option>
                  {donors.map((donor) => (
                    <option key={donor.donorId} value={donor.donorId}>
                      {donor.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="date" className="form-label">
                  Donation Date *
                </label>
                <input
                  id="date"
                  type="date"
                  required
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="input-field"
                />
              </div>

              <div>
                <label htmlFor="pickupLocation" className="form-label">
                  Pickup Location
                </label>
                <input
                  id="pickupLocation"
                  type="text"
                  value={pickupLocation}
                  onChange={(e) => setPickupLocation(e.target.value)}
                  className="input-field"
                  placeholder="e.g., Main entrance"
                />
              </div>

              <div>
                <label htmlFor="pickupTime" className="form-label">
                  Pickup Time
                </label>
                <input
                  id="pickupTime"
                  type="time"
                  value={pickupTime}
                  onChange={(e) => setPickupTime(e.target.value)}
                  className="input-field"
                />
              </div>

              <div className="md:col-span-2">
                <label htmlFor="notes" className="form-label">
                  Notes
                </label>
                <textarea
                  id="notes"
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="input-field"
                  placeholder="Any additional information about this donation..."
                />
              </div>
            </div>
          </div>

          {/* Donated Items */}
          <div className="card">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Donated Items</h2>
              <button type="button" onClick={addItem} className="btn-secondary text-sm">
                + Add Item
              </button>
            </div>

            <div className="space-y-4">
              {items.map((item, index) => (
                <div key={index} className="border border-gray-200 rounded-md p-4">
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="text-sm font-medium text-gray-900">Item {index + 1}</h3>
                    {items.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeItem(index)}
                        className="text-red-600 hover:text-red-900 text-sm"
                      >
                        Remove
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="md:col-span-2">
                      <input
                        type="text"
                        value={item.name}
                        onChange={(e) => updateItem(index, 'name', e.target.value)}
                        className="input-field"
                        placeholder="Item name *"
                        required
                      />
                    </div>

                    <div>
                      <select
                        value={item.category}
                        onChange={(e) => updateItem(index, 'category', e.target.value)}
                        className="input-field"
                        required
                      >
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

                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="number"
                        step="0.01"
                        value={item.quantity}
                        onChange={(e) => updateItem(index, 'quantity', e.target.value)}
                        className="input-field"
                        placeholder="Quantity *"
                        required
                      />
                      <input
                        type="text"
                        value={item.unit}
                        onChange={(e) => updateItem(index, 'unit', e.target.value)}
                        className="input-field"
                        placeholder="Unit *"
                        required
                      />
                    </div>

                    <div>
                      <input
                        type="number"
                        step="0.01"
                        value={item.estimatedValue}
                        onChange={(e) => updateItem(index, 'estimatedValue', e.target.value)}
                        className="input-field"
                        placeholder="Estimated value ($) *"
                        required
                      />
                    </div>

                    <div>
                      <input
                        type="date"
                        value={item.expirationDate}
                        onChange={(e) => updateItem(index, 'expirationDate', e.target.value)}
                        className="input-field"
                        placeholder="Expiration date *"
                        required
                      />
                    </div>

                    <div className="md:col-span-2">
                      <input
                        type="text"
                        value={item.storageLocation}
                        onChange={(e) => updateItem(index, 'storageLocation', e.target.value)}
                        className="input-field"
                        placeholder="Storage location (optional)"
                      />
                    </div>

                    <div className="md:col-span-2">
                      <textarea
                        rows={2}
                        value={item.notes}
                        onChange={(e) => updateItem(index, 'notes', e.target.value)}
                        className="input-field"
                        placeholder="Item notes (optional)"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={() => navigate('/donations')}
              disabled={isSaving}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="btn-primary flex items-center gap-2"
            >
              {isSaving ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Saving...
                </>
              ) : (
                <>{isEditMode ? 'Update Donation' : 'Create Donation'}</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DonationFormPage;
