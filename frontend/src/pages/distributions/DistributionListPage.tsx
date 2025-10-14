/**
 * Distribution List Page
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { getDistributions, cancelDistribution } from '../../services/distributionService';
import type { Distribution, DistributionStatus } from '../../types/distribution';

const DistributionListPage: React.FC = () => {
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const [distributions, setDistributions] = useState<Distribution[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<DistributionStatus | ''>('');
  const canWrite = hasPermission('distributions:write');

  useEffect(() => {
    fetchDistributions();
  }, [filterStatus]);

  const fetchDistributions = async () => {
    try {
      setIsLoading(true);
      const response = await getDistributions({
        status: filterStatus || undefined,
        limit: 20,
      });
      setDistributions(response.distributions);
    } catch (err) {
      setError('Failed to load distributions');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadgeClass = (status: DistributionStatus): string => {
    const classes: Record<DistributionStatus, string> = {
      planned: 'bg-yellow-100 text-yellow-800',
      'in-progress': 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-gray-100 text-gray-800',
    };
    return classes[status];
  };

  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Distributions</h1>
          {canWrite && (
            <button onClick={() => navigate('/distributions/new')} className="btn-primary">+ New Distribution</button>
          )}
        </div>

        <div className="card mb-6">
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value as DistributionStatus | '')} className="input-field">
            <option value="">All Statuses</option>
            <option value="planned">Planned</option>
            <option value="in-progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>

        {error && <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md mb-6">{error}</div>}

        {isLoading ? (
          <div className="card text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : distributions.length === 0 ? (
          <div className="card text-center py-12">
            <h3 className="text-lg font-medium text-gray-900">No distributions found</h3>
          </div>
        ) : (
          <div className="grid gap-4">
            {distributions.map((dist) => (
              <div key={dist.distributionId} className="card">
                <div className="flex justify-between items-start">
                  <div>
                    <Link to={`/distributions/${dist.distributionId}`} className="text-lg font-semibold text-primary-600 hover:text-primary-900">
                      {dist.recipientName}
                    </Link>
                    <p className="text-sm text-gray-500">{new Date(dist.date).toLocaleDateString()}</p>
                    <p className="text-sm text-gray-600">{dist.items.length} items</p>
                  </div>
                  <span className={`px-3 py-1 text-sm font-semibold rounded-full ${getStatusBadgeClass(dist.status)}`}>
                    {dist.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DistributionListPage;
