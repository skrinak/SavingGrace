/**
 * Distribution Form Page
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createDistribution } from '../../services/distributionService';

const DistributionFormPage: React.FC = () => {
  const navigate = useNavigate();
  const [recipientId, setRecipientId] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [notes, setNotes] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!recipientId) {
      setError('Recipient is required');
      return;
    }

    setIsSaving(true);
    try {
      await createDistribution({
        recipientId,
        date: new Date(date).toISOString(),
        items: [],
        notes: notes || undefined,
      });
      navigate('/distributions');
    } catch (err) {
      setError('Failed to create distribution');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="py-6">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold mb-6">Create Distribution</h1>
        {error && <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md mb-6">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="card">
            <div className="grid gap-4">
              <div>
                <label className="form-label">Recipient ID *</label>
                <input type="text" required value={recipientId} onChange={(e) => setRecipientId(e.target.value)} className="input-field" placeholder="recipient-uuid" />
              </div>
              <div>
                <label className="form-label">Date *</label>
                <input type="date" required value={date} onChange={(e) => setDate(e.target.value)} className="input-field" />
              </div>
              <div>
                <label className="form-label">Notes</label>
                <textarea rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} className="input-field" />
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-3">
            <button type="button" onClick={() => navigate('/distributions')} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={isSaving} className="btn-primary">{isSaving ? 'Saving...' : 'Create'}</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DistributionFormPage;
