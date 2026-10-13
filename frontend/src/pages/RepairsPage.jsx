import React, { useState, useEffect } from 'react';
import { RefreshCw, Play, AlertCircle } from 'lucide-react';
import { StatusPill } from '../components/ui/StatusPill';
import { Button } from '../components/ui/Button';
import { api } from '../services/api';

export function RepairsPage() {
  const [repairs, setRepairs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoadingId, setActionLoadingId] = useState(null);

  const loadRepairs = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getRepairPlans();
      const list = res.results || res;
      if (Array.isArray(list)) {
        const formatted = list.map(p => ({
          id: `REP-${(p.id || '').substring(0, 8).toUpperCase()}`,
          fullId: p.id,
          employeeName: p.employee_name || (p.employee && p.employee.full_name) || 'Unknown Employee',
          employeeEmail: p.employee_email || (p.employee && p.employee.email) || '',
          targetSystem: p.target_system || 'VPN',
          action: p.action || 'REVOKE_ACCESS',
          actionDetails: p.action_details || `Target connector action: ${p.action}`,
          reason: p.reason || 'HR Status is TERMINATED while access remains enabled',
          riskLevel: p.risk_level || 'HIGH',
          status: p.status || 'PENDING',
          createdAt: p.created_at ? new Date(p.created_at).toLocaleString() : 'Just now'
        }));
        setRepairs(formatted);
      } else {
        setRepairs([]);
      }
    } catch (err) {
      console.error('API error loading repairs:', err);
      setError(err.message || 'Failed to load repair plans from backend.');
      setRepairs([]);
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
    <div className="page-content">
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <span>Repairs Engine</span>
          </h1>
          <p className="page-subtitle">
            Deterministic remediation repair plans generated to fix authorization drift
          </p>
        </div>
        <Button variant="secondary" icon={RefreshCw} onClick={loadRepairs} disabled={loading}>
          Refresh Plans
        </Button>
      </div>

      {error && (
        <div
          style={{
            marginBottom: '20px',
            padding: '12px 18px',
            borderRadius: 'var(--radius-btn)',
            backgroundColor: 'var(--status-critical-bg)',
            border: '1px solid var(--status-critical-border)',
            color: 'var(--status-critical)',
            fontSize: '13px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      <div className="plain-divided-container">
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
          <thead>
            <tr style={{ backgroundColor: 'var(--bg-base)', borderBottom: '1px solid var(--border-hairline)' }}>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Plan ID</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Employee</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Target System</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Action</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Justification</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Risk</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Status</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase', textAlign: 'right' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {repairs.map((rep) => (
              <tr key={rep.id} style={{ borderBottom: '1px solid var(--border-hairline)' }}>
                <td className="font-mono" style={{ padding: '12px 16px', color: 'var(--accent-primary)', fontWeight: 600, fontSize: '12px' }}>
                  {rep.id}
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{rep.employeeName}</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{rep.employeeEmail}</div>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ fontSize: '12px', fontWeight: 600, padding: '2px 8px', borderRadius: 'var(--radius-pill)', backgroundColor: 'var(--accent-primary-light)', color: 'var(--accent-primary)' }}>
                    {rep.targetSystem}
                  </span>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <div className="font-mono" style={{ fontWeight: 600, color: 'var(--status-warning)', fontSize: '12px' }}>
                    {rep.action}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{rep.actionDetails}</div>
                </td>
                <td style={{ padding: '12px 16px', fontSize: '13px', color: 'var(--text-secondary)', maxWidth: '280px' }}>
                  {rep.reason}
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <StatusPill status={rep.riskLevel.toLowerCase()} label={rep.riskLevel} size="small" />
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <StatusPill status={rep.status === 'SUCCESS' || rep.status === 'COMPLETED' ? 'healthy' : rep.status === 'EXECUTING' ? 'warning' : 'neutral'} label={rep.status} size="small" />
                </td>
                <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                  {(rep.status === 'APPROVED' || rep.status === 'PENDING') && rep.fullId ? (
                    <Button
                      variant="primary"
                      size="small"
                      icon={Play}
                      onClick={() => handleExecutePlan(rep.fullId)}
                      disabled={actionLoadingId === rep.fullId}
                    >
                      Execute & Verify
                    </Button>
                  ) : (
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>—</span>
                  )}
                </td>
              </tr>
            ))}
            {repairs.length === 0 && (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                  {loading ? 'Loading repair plans...' : 'No remediation repair plans found. Systems are compliant!'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

