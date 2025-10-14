/**
 * Recipient Form Page
 * Create or edit recipient information
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getRecipientById, createRecipient, updateRecipient } from '../../services/recipientService';
import type { DietaryRestriction } from '../../types/recipient';

interface FormData {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  street: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
  householdSize: string;
  notes: string;
}

const RecipientFormPage: React.FC = () => {
  const navigate = useNavigate();
  const { recipientId } = useParams<{ recipientId: string }>();
  const isEditMode = !!recipientId;

  const [formData, setFormData] = useState<FormData>({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    street: '',
    city: '',
    state: '',
    zipCode: '',
    country: 'USA',
    householdSize: '1',
    notes: '',
  });

  const [dietaryRestrictions, setDietaryRestrictions] = useState<DietaryRestriction[]>([]);
  const [isLoading, setIsLoading] = useState(isEditMode);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isEditMode && recipientId) {
      loadRecipient(recipientId);
    }
  }, [recipientId, isEditMode]);

  const loadRecipient = async (id: string) => {
    try {
      setIsLoading(true);
      const recipient = await getRecipientById(id);

      setFormData({
        firstName: recipient.firstName,
        lastName: recipient.lastName,
        email: recipient.email || '',
        phone: recipient.phone,
        street: recipient.address.street,
        city: recipient.address.city,
        state: recipient.address.state,
        zipCode: recipient.address.zipCode,
        country: recipient.address.country,
        householdSize: recipient.householdSize.toString(),
        notes: recipient.notes || '',
      });

      setDietaryRestrictions(recipient.dietaryRestrictions || []);
    } catch (err) {
      console.error('Error loading recipient:', err);
      setError('Failed to load recipient. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError(null);
  };

  const addDietaryRestriction = () => {
    setDietaryRestrictions((prev) => [...prev, { type: '', notes: '' }]);
  };

  const updateDietaryRestriction = (index: number, field: keyof DietaryRestriction, value: string) => {
    setDietaryRestrictions((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const removeDietaryRestriction = (index: number) => {
    setDietaryRestrictions((prev) => prev.filter((_, i) => i !== index));
  };

  const validateForm = (): string | null => {
    if (!formData.firstName.trim()) return 'First name is required';
    if (!formData.lastName.trim()) return 'Last name is required';
    if (!formData.phone.trim()) return 'Phone number is required';
    if (!formData.street.trim()) return 'Street address is required';
    if (!formData.city.trim()) return 'City is required';
    if (!formData.state.trim()) return 'State is required';
    if (!formData.zipCode.trim()) return 'ZIP code is required';
    if (!formData.householdSize || parseInt(formData.householdSize) < 1) {
      return 'Valid household size is required';
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
        firstName: formData.firstName.trim(),
        lastName: formData.lastName.trim(),
        email: formData.email.trim() || undefined,
        phone: formData.phone.trim(),
        address: {
          street: formData.street.trim(),
          city: formData.city.trim(),
          state: formData.state.trim(),
          zipCode: formData.zipCode.trim(),
          country: formData.country.trim(),
        },
        householdSize: parseInt(formData.householdSize),
        dietaryRestrictions: dietaryRestrictions.filter((d) => d.type.trim()).length > 0
          ? dietaryRestrictions.filter((d) => d.type.trim())
          : undefined,
        notes: formData.notes.trim() || undefined,
      };

      if (isEditMode && recipientId) {
        await updateRecipient(recipientId, requestData);
      } else {
        await createRecipient(requestData);
      }

      navigate('/recipients');
    } catch (err) {
      console.error('Error saving recipient:', err);
      setError(`Failed to ${isEditMode ? 'update' : 'create'} recipient. Please try again.`);
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
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">{isEditMode ? 'Edit Recipient' : 'Add New Recipient'}</h1>
          <p className="mt-1 text-sm text-gray-600">{isEditMode ? 'Update recipient information' : 'Register a new recipient household'}</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md mb-6">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Personal Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="firstName" className="form-label">First Name *</label>
                <input id="firstName" name="firstName" type="text" required value={formData.firstName} onChange={handleInputChange} className="input-field" />
              </div>
              <div>
                <label htmlFor="lastName" className="form-label">Last Name *</label>
                <input id="lastName" name="lastName" type="text" required value={formData.lastName} onChange={handleInputChange} className="input-field" />
              </div>
              <div>
                <label htmlFor="phone" className="form-label">Phone Number *</label>
                <input id="phone" name="phone" type="tel" required value={formData.phone} onChange={handleInputChange} className="input-field" placeholder="(555) 123-4567" />
              </div>
              <div>
                <label htmlFor="email" className="form-label">Email (Optional)</label>
                <input id="email" name="email" type="email" value={formData.email} onChange={handleInputChange} className="input-field" placeholder="email@example.com" />
              </div>
            </div>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Address</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label htmlFor="street" className="form-label">Street Address *</label>
                <input id="street" name="street" type="text" required value={formData.street} onChange={handleInputChange} className="input-field" placeholder="123 Main St" />
              </div>
              <div>
                <label htmlFor="city" className="form-label">City *</label>
                <input id="city" name="city" type="text" required value={formData.city} onChange={handleInputChange} className="input-field" />
              </div>
              <div>
                <label htmlFor="state" className="form-label">State *</label>
                <input id="state" name="state" type="text" required value={formData.state} onChange={handleInputChange} className="input-field" placeholder="CA" />
              </div>
              <div>
                <label htmlFor="zipCode" className="form-label">ZIP Code *</label>
                <input id="zipCode" name="zipCode" type="text" required value={formData.zipCode} onChange={handleInputChange} className="input-field" placeholder="94102" />
              </div>
              <div>
                <label htmlFor="country" className="form-label">Country *</label>
                <input id="country" name="country" type="text" required value={formData.country} onChange={handleInputChange} className="input-field" />
              </div>
            </div>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Household Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="householdSize" className="form-label">Household Size *</label>
                <input id="householdSize" name="householdSize" type="number" min="1" required value={formData.householdSize} onChange={handleInputChange} className="input-field" />
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Dietary Restrictions</h2>
              <button type="button" onClick={addDietaryRestriction} className="btn-secondary text-sm">+ Add Restriction</button>
            </div>
            {dietaryRestrictions.length === 0 ? (
              <p className="text-sm text-gray-600">No dietary restrictions added</p>
            ) : (
              <div className="space-y-3">
                {dietaryRestrictions.map((restriction, index) => (
                  <div key={index} className="border border-gray-200 rounded-md p-3">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-sm font-medium text-gray-900">Restriction {index + 1}</h3>
                      <button type="button" onClick={() => removeDietaryRestriction(index)} className="text-red-600 hover:text-red-900 text-sm">Remove</button>
                    </div>
                    <div className="grid grid-cols-1 gap-2">
                      <input type="text" value={restriction.type} onChange={(e) => updateDietaryRestriction(index, 'type', e.target.value)} className="input-field" placeholder="Type (e.g., Gluten-free, Vegan)" />
                      <textarea rows={2} value={restriction.notes || ''} onChange={(e) => updateDietaryRestriction(index, 'notes', e.target.value)} className="input-field" placeholder="Additional notes (optional)" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Additional Notes</h2>
            <textarea id="notes" name="notes" rows={4} value={formData.notes} onChange={handleInputChange} className="input-field" placeholder="Any additional information..." />
          </div>

          <div className="flex justify-end gap-3">
            <button type="button" onClick={() => navigate('/recipients')} disabled={isSaving} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={isSaving} className="btn-primary flex items-center gap-2">
              {isSaving ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Saving...
                </>
              ) : (
                <>{isEditMode ? 'Update Recipient' : 'Create Recipient'}</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RecipientFormPage;
