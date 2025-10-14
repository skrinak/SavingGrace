/**
 * Donor Form Page
 * Create or edit donor information
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getDonorById, createDonor, updateDonor } from '../../services/donorService';
import type { DonorType, DonorContact } from '../../types/donor';

interface FormData {
  name: string;
  type: DonorType;
  email: string;
  phone: string;
  street: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
  taxId: string;
  licenseNumber: string;
  website: string;
  notes: string;
  preferredPickupTimes: string;
  specialInstructions: string;
}

const DonorFormPage: React.FC = () => {
  const navigate = useNavigate();
  const { donorId } = useParams<{ donorId: string }>();
  const isEditMode = !!donorId;

  const [formData, setFormData] = useState<FormData>({
    name: '',
    type: 'restaurant',
    email: '',
    phone: '',
    street: '',
    city: '',
    state: '',
    zipCode: '',
    country: 'USA',
    taxId: '',
    licenseNumber: '',
    website: '',
    notes: '',
    preferredPickupTimes: '',
    specialInstructions: '',
  });

  const [contacts, setContacts] = useState<DonorContact[]>([]);
  const [isLoading, setIsLoading] = useState(isEditMode);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isEditMode && donorId) {
      loadDonor(donorId);
    }
  }, [donorId, isEditMode]);

  const loadDonor = async (id: string) => {
    try {
      setIsLoading(true);
      const donor = await getDonorById(id);

      setFormData({
        name: donor.name,
        type: donor.type,
        email: donor.email,
        phone: donor.phone,
        street: donor.address.street,
        city: donor.address.city,
        state: donor.address.state,
        zipCode: donor.address.zipCode,
        country: donor.address.country,
        taxId: donor.taxId || '',
        licenseNumber: donor.licenseNumber || '',
        website: donor.website || '',
        notes: donor.notes || '',
        preferredPickupTimes: donor.preferredPickupTimes || '',
        specialInstructions: donor.specialInstructions || '',
      });

      setContacts(donor.contacts || []);
    } catch (err) {
      console.error('Error loading donor:', err);
      setError('Failed to load donor. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError(null);
  };

  const addContact = () => {
    setContacts((prev) => [
      ...prev,
      { name: '', email: '', phone: '', title: '', isPrimary: prev.length === 0 },
    ]);
  };

  const updateContact = (index: number, field: keyof DonorContact, value: string | boolean) => {
    setContacts((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };

      // If setting isPrimary to true, set all others to false
      if (field === 'isPrimary' && value === true) {
        updated.forEach((contact, i) => {
          if (i !== index) contact.isPrimary = false;
        });
      }

      return updated;
    });
  };

  const removeContact = (index: number) => {
    setContacts((prev) => {
      const updated = prev.filter((_, i) => i !== index);
      // If we removed the primary contact, make the first one primary
      if (updated.length > 0 && !updated.some((c) => c.isPrimary)) {
        updated[0].isPrimary = true;
      }
      return updated;
    });
  };

  const validateForm = (): string | null => {
    if (!formData.name.trim()) return 'Donor name is required';
    if (!formData.email.trim() || !formData.email.includes('@')) return 'Valid email is required';
    if (!formData.phone.trim()) return 'Phone number is required';
    if (!formData.street.trim()) return 'Street address is required';
    if (!formData.city.trim()) return 'City is required';
    if (!formData.state.trim()) return 'State is required';
    if (!formData.zipCode.trim()) return 'ZIP code is required';

    // Validate contacts if any
    for (let i = 0; i < contacts.length; i++) {
      const contact = contacts[i];
      if (!contact.name.trim()) return `Contact ${i + 1}: Name is required`;
      if (!contact.email.trim() || !contact.email.includes('@')) {
        return `Contact ${i + 1}: Valid email is required`;
      }
      if (!contact.phone.trim()) return `Contact ${i + 1}: Phone is required`;
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
      const requestData = {
        name: formData.name.trim(),
        type: formData.type,
        email: formData.email.trim(),
        phone: formData.phone.trim(),
        address: {
          street: formData.street.trim(),
          city: formData.city.trim(),
          state: formData.state.trim(),
          zipCode: formData.zipCode.trim(),
          country: formData.country.trim(),
        },
        contacts: contacts.length > 0 ? contacts : undefined,
        taxId: formData.taxId.trim() || undefined,
        licenseNumber: formData.licenseNumber.trim() || undefined,
        website: formData.website.trim() || undefined,
        notes: formData.notes.trim() || undefined,
        preferredPickupTimes: formData.preferredPickupTimes.trim() || undefined,
        specialInstructions: formData.specialInstructions.trim() || undefined,
      };

      if (isEditMode && donorId) {
        await updateDonor(donorId, requestData);
      } else {
        await createDonor(requestData);
      }

      navigate('/donors');
    } catch (err) {
      console.error('Error saving donor:', err);
      setError(`Failed to ${isEditMode ? 'update' : 'create'} donor. Please try again.`);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
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
            {isEditMode ? 'Edit Donor' : 'Add New Donor'}
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            {isEditMode ? 'Update donor information' : 'Register a new donor organization or individual'}
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
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label htmlFor="name" className="form-label">
                  Donor Name *
                </label>
                <input
                  id="name"
                  name="name"
                  type="text"
                  required
                  value={formData.name}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="ABC Restaurant"
                />
              </div>

              <div>
                <label htmlFor="type" className="form-label">
                  Donor Type *
                </label>
                <select
                  id="type"
                  name="type"
                  required
                  value={formData.type}
                  onChange={handleInputChange}
                  className="input-field"
                >
                  <option value="individual">Individual</option>
                  <option value="restaurant">Restaurant</option>
                  <option value="grocery">Grocery Store</option>
                  <option value="farm">Farm</option>
                  <option value="manufacturer">Manufacturer</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label htmlFor="email" className="form-label">
                  Email Address *
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="contact@example.com"
                />
              </div>

              <div>
                <label htmlFor="phone" className="form-label">
                  Phone Number *
                </label>
                <input
                  id="phone"
                  name="phone"
                  type="tel"
                  required
                  value={formData.phone}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="(555) 123-4567"
                />
              </div>

              <div>
                <label htmlFor="website" className="form-label">
                  Website
                </label>
                <input
                  id="website"
                  name="website"
                  type="url"
                  value={formData.website}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="https://example.com"
                />
              </div>
            </div>
          </div>

          {/* Address */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Address</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label htmlFor="street" className="form-label">
                  Street Address *
                </label>
                <input
                  id="street"
                  name="street"
                  type="text"
                  required
                  value={formData.street}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="123 Main St"
                />
              </div>

              <div>
                <label htmlFor="city" className="form-label">
                  City *
                </label>
                <input
                  id="city"
                  name="city"
                  type="text"
                  required
                  value={formData.city}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="San Francisco"
                />
              </div>

              <div>
                <label htmlFor="state" className="form-label">
                  State *
                </label>
                <input
                  id="state"
                  name="state"
                  type="text"
                  required
                  value={formData.state}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="CA"
                />
              </div>

              <div>
                <label htmlFor="zipCode" className="form-label">
                  ZIP Code *
                </label>
                <input
                  id="zipCode"
                  name="zipCode"
                  type="text"
                  required
                  value={formData.zipCode}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="94102"
                />
              </div>

              <div>
                <label htmlFor="country" className="form-label">
                  Country *
                </label>
                <input
                  id="country"
                  name="country"
                  type="text"
                  required
                  value={formData.country}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="USA"
                />
              </div>
            </div>
          </div>

          {/* Additional Contacts */}
          <div className="card">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Additional Contacts</h2>
              <button
                type="button"
                onClick={addContact}
                className="btn-secondary text-sm"
              >
                + Add Contact
              </button>
            </div>

            {contacts.length === 0 ? (
              <p className="text-sm text-gray-600">No additional contacts added</p>
            ) : (
              <div className="space-y-4">
                {contacts.map((contact, index) => (
                  <div key={index} className="border border-gray-200 rounded-md p-4">
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="text-sm font-medium text-gray-900">Contact {index + 1}</h3>
                      <button
                        type="button"
                        onClick={() => removeContact(index)}
                        className="text-red-600 hover:text-red-900 text-sm"
                      >
                        Remove
                      </button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div>
                        <input
                          type="text"
                          value={contact.name}
                          onChange={(e) => updateContact(index, 'name', e.target.value)}
                          className="input-field"
                          placeholder="Contact Name"
                        />
                      </div>
                      <div>
                        <input
                          type="email"
                          value={contact.email}
                          onChange={(e) => updateContact(index, 'email', e.target.value)}
                          className="input-field"
                          placeholder="email@example.com"
                        />
                      </div>
                      <div>
                        <input
                          type="tel"
                          value={contact.phone}
                          onChange={(e) => updateContact(index, 'phone', e.target.value)}
                          className="input-field"
                          placeholder="(555) 123-4567"
                        />
                      </div>
                      <div>
                        <input
                          type="text"
                          value={contact.title || ''}
                          onChange={(e) => updateContact(index, 'title', e.target.value)}
                          className="input-field"
                          placeholder="Title (optional)"
                        />
                      </div>
                      <div className="md:col-span-2">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={contact.isPrimary}
                            onChange={(e) => updateContact(index, 'isPrimary', e.target.checked)}
                            className="mr-2"
                          />
                          <span className="text-sm text-gray-700">Primary Contact</span>
                        </label>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Additional Details */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Additional Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="taxId" className="form-label">
                  Tax ID / EIN
                </label>
                <input
                  id="taxId"
                  name="taxId"
                  type="text"
                  value={formData.taxId}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="12-3456789"
                />
              </div>

              <div>
                <label htmlFor="licenseNumber" className="form-label">
                  License Number
                </label>
                <input
                  id="licenseNumber"
                  name="licenseNumber"
                  type="text"
                  value={formData.licenseNumber}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="ABC-123456"
                />
              </div>

              <div className="md:col-span-2">
                <label htmlFor="preferredPickupTimes" className="form-label">
                  Preferred Pickup Times
                </label>
                <input
                  id="preferredPickupTimes"
                  name="preferredPickupTimes"
                  type="text"
                  value={formData.preferredPickupTimes}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="e.g., Mon-Fri 2-4pm"
                />
              </div>

              <div className="md:col-span-2">
                <label htmlFor="specialInstructions" className="form-label">
                  Special Instructions
                </label>
                <textarea
                  id="specialInstructions"
                  name="specialInstructions"
                  rows={3}
                  value={formData.specialInstructions}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="Any special instructions for pickup or handling..."
                />
              </div>

              <div className="md:col-span-2">
                <label htmlFor="notes" className="form-label">
                  Internal Notes
                </label>
                <textarea
                  id="notes"
                  name="notes"
                  rows={3}
                  value={formData.notes}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="Internal notes about this donor..."
                />
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={() => navigate('/donors')}
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
                <>{isEditMode ? 'Update Donor' : 'Create Donor'}</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DonorFormPage;
