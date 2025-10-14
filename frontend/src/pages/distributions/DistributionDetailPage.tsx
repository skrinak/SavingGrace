/**
 * Distribution Detail Page
 */

import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { getDistributionById, completeDistribution } from '../../services/distributionService';
import type { Distribution } from '../../types/distribution';

const DistributionDetailPage: React.FC = () => {
  const { distributionId } = useParams<{ distributionId: string }>();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const [distribution, setDistribution] = useState<Distribution | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const canWrite = hasPermission('distributions:write');

  useEffect(() => {
    if (distributionId) {
      loadDistribution(distributionId);
    }
  }, [distributionId]);

  const loadDistribution = async (id: string) => {
    try {
      setIsLoading(true);
      const data = await getDistributionById(id);
      setDistribution(data);
    } catch (err) {
      setError('Failed to load distribution');
    } finally {
      setIsLoading(false);
    }
  };

  const handleComplete = async () => {
    if (!distributionId) return;
    try {
      await completeDistribution(distributionId);
      loadDistribution(distributionId);
    } catch (err) {
      setError('Failed to complete distribution');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!distribution) {
    return (
      <div className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="card text-center py-12">
            <p className="text-gray-600">Distribution not found</p>
            <Link to="/distributions" className="mt-4 inline-block btn-primary">Back</Link>
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
            <Link to="/distributions" className="hover:text-primary-600">Distributions</Link>
            <span>/</span>
            <span className="text-gray-900">{distribution.recipientName}</span>
          </div>
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold">{distribution.recipientName}</h1>
            {canWrite && distribution.status === 'planned' && (
              <button onClick={handleComplete} className="btn-primary">Complete Distribution</button>
            )}
          </div>
        </div>

        {error && <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md mb-6">{error}</div>}

        <div className="grid gap-6">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Details</h2>
            <div className="grid gap-2 text-sm">
              <div><span className="text-gray-600">Date:</span> {new Date(distribution.date).toLocaleDateString()}</div>
              <div><span className="text-gray-600">Status:</span> {distribution.status}</div>
              <div><span className="text-gray-600">Items:</span> {distribution.items.length}</div>
              {distribution.notes && <div><span className="text-gray-600">Notes:</span> {distribution.notes}</div>}
            </div>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Items</h2>
            <div className="space-y-2">
              {distribution.items.map((item, idx) => (
                <div key={idx} className="border-b pb-2 last:border-0">
                  <p className="font-medium">{item.itemName}</p>
                  <p className="text-sm text-gray-600">{item.quantity} {item.unit} - {item.category}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DistributionDetailPage;
