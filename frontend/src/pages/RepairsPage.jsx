import React, { useState, useEffect } from 'react';
import { Wrench, RefreshCw, Play } from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { api } from '../services/api';
import { mockRepairs } from '../data/mockData';

export function RepairsPage() {
  const [repairs, setRepairs] = useState(mockRepairs);
  const [loading, setLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState(null);

  const loadRepairs = async () => {
    setLoading(true);
    try {
      const res = await api.getRepairPlans();
      const list = res.results || res;
      if (Array.isArray(list) && list.length > 0) {
        const formatted = list.map(p => ({
          id: `REP-${(p.id || '').substring(0, 8).toUpperCase()}`,
          fullId: p.id,
          employeeName: p.employee_name || (p.employee && p.employee.full_name) || 'Rahul Kumar',
          employeeEmail: p.employee_email || (p.employee && p.employee.email) || 'rahul.kumar@reconcileos.internal',
          targetSystem: p.target_system || 'VPN',
          action: p.action || 'REVOKE_ACCESS',
          actionDetails: p.action_details || `Target connector action: ${p.action}`,
          reason: p.reason || 'HR Status is TERMINATED while access remains enabled',
          riskLevel: p.risk_level || 'HIGH',
          status: p.status || 'PENDING',
          createdAt: p.created_at ? new Date(p.created_at).toLocaleString() : 'Just now'
        }));
        setRepairs(formatted);
      }
    } catch (err) {
      console.warn('API error loading repairs, using mock data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRepairs();
  }, []);

  const handleExecutePlan = async (fullId) => {
    if (!fullId) return;
    setActionLoadingId(fullId);
    try {
      await api.executeRepairPlan(fullId);
      await api.verifyRepairPlan(fullId);
      await loadRepairs();
    } catch (err) {
      alert(`Execution error: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Wrench size={24} style={{ color: 'var(--accent-blue)' }} />
            Self-Healing Repair Plans
          </h1>
          <p className="page-subtitle">
            Deterministic remediation actions generated to enforce multi-system integrity
          </p>
        </div>
        <button className="btn btn-secondary" onClick={loadRepairs} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh Plans
        </button>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Repair Plan ID</th>
              <th>Employee Name</th>
              <th>Target System</th>
              <th>Action to Execute</th>
              <th>Justification / Invariant Violation</th>
              <th>Risk Level</th>
              <th>Execution Status</th>
              <th>Created At</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {repairs.map((rep) => (
              <tr key={rep.id}>
                <td className="mono" style={{ color: 'var(--accent-blue)', fontWeight: 600 }}>
                  {rep.id}
                </td>
                <td>
                  <div style={{ fontWeight: 600 }}>{rep.employeeName}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{rep.employeeEmail}</div>
                </td>
                <td>
                  <span className="badge badge-info">{rep.targetSystem}</span>
                </td>
                <td>
                  <div className="mono" style={{ fontWeight: 600, color: 'var(--status-warning)' }}>
                    {rep.action}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{rep.actionDetails}</div>
                </td>
                <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', maxWidth: '280px' }}>
                  {rep.reason}
                </td>
                <td>
                  <SeverityBadge severity={rep.riskLevel} />
                </td>
                <td>
                  <StatusBadge status={rep.status} />
                </td>
                <td className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {rep.createdAt}
                </td>
                <td>
                  {(rep.status === 'APPROVED' || rep.status === 'PENDING') && rep.fullId ? (
                    <button
                      className="btn btn-primary"
                      style={{ fontSize: '0.72rem', padding: '4px 8px' }}
                      onClick={() => handleExecutePlan(rep.fullId)}
                      disabled={actionLoadingId === rep.fullId}
                    >
                      <Play size={12} /> Execute & Verify
                    </button>
                  ) : (
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
