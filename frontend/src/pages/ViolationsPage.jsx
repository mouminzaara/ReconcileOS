import React, { useState, useEffect } from 'react';
import { Filter, ExternalLink, RefreshCw, AlertCircle } from 'lucide-react';
import { StatusPill } from '../components/ui/StatusPill';
import { Button } from '../components/ui/Button';
import { api } from '../services/api';
import { Link } from 'react-router-dom';

export function ViolationsPage() {
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [severityFilter, setSeverityFilter] = useState('ALL');

  const loadViolations = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getViolations();
      const list = res.results || res;
      if (Array.isArray(list)) {
        const formatted = list.map(v => ({
          id: `VIO-${(v.id || '').substring(0, 8).toUpperCase()}`,
          fullId: v.id,
          employeeName: v.employee_name || (v.employee && v.employee.full_name) || 'Unknown Employee',
          employeeEmail: v.employee_email || (v.employee && v.employee.email) || '',
          systemKey: v.affected_system || 'VPN',
          ruleId: v.rule_code || (v.rule && v.rule.rule_code) || 'INV-RULE',
          ruleName: v.rule_name || (v.rule && v.rule.name) || 'Invariant Security Rule',
          expectedState: v.expected_state || 'DISABLED',
          actualState: v.actual_state || 'ENABLED',
          severity: v.severity || 'CRITICAL',
          status: v.status || 'OPEN',
          detectedAt: v.detected_at ? new Date(v.detected_at).toLocaleString() : 'Just now'
        }));
        setViolations(formatted);
      } else {
        setViolations([]);
      }
    } catch (err) {
      console.error('API error loading violations:', err);
      setError(err.message || 'Failed to load violations from backend.');
      setViolations([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadViolations();
  }, []);

  const filteredViolations = violations.filter(v =>
    severityFilter === 'ALL' || v.severity === severityFilter
  );

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <div className="page-eyebrow">
            <span className="page-eyebrow-dot" />
            <span>Drift Detection</span>
          </div>
          <h1 className="page-title">Authorization Violations</h1>
          <p className="page-subtitle">
            Real-time access discrepancies detected between HR status and downstream target applications
          </p>
        </div>
        <div className="page-header-actions">
          <Button variant="secondary" icon={RefreshCw} onClick={loadViolations} disabled={loading}>
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <div
          style={{
            marginBottom: 'var(--space-xl)',
            padding: '14px 20px',
            borderRadius: '10px',
            backgroundColor: 'var(--status-critical-bg)',
            border: '1px solid var(--status-critical-border)',
            color: 'var(--status-critical)',
            fontSize: '13px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Controls & Filter Bar — Clean toolbar without card enclosure */}
      <div style={{ marginBottom: 'var(--space-xl)', display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
        <Filter size={15} style={{ color: 'var(--text-muted)' }} />
        <span style={{ fontSize: '13px', color: 'var(--text-muted)', marginRight: '4px' }}>Filter Severity:</span>
        <Button
          variant={severityFilter === 'ALL' ? 'primary' : 'secondary'}
          size="small"
          onClick={() => setSeverityFilter('ALL')}
        >
          All ({violations.length})
        </Button>
        <Button
          variant={severityFilter === 'CRITICAL' ? 'danger' : 'secondary'}
          size="small"
          onClick={() => setSeverityFilter('CRITICAL')}
        >
          Critical ({violations.filter(v => v.severity === 'CRITICAL').length})
        </Button>
        <Button
          variant={severityFilter === 'HIGH' ? 'primary' : 'secondary'}
          size="small"
          onClick={() => setSeverityFilter('HIGH')}
        >
          High ({violations.filter(v => v.severity === 'HIGH').length})
        </Button>
        <Button
          variant={severityFilter === 'MEDIUM' ? 'secondary' : 'secondary'}
          size="small"
          onClick={() => setSeverityFilter('MEDIUM')}
        >
          Medium ({violations.filter(v => v.severity === 'MEDIUM').length})
        </Button>
      </div>

      <div className="editorial-table-container">
        <table className="editorial-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Employee</th>
              <th>System</th>
              <th>Invariant Rule</th>
              <th>Expected</th>
              <th>Actual</th>
              <th>Severity</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredViolations.map((vio) => (
              <tr key={vio.id}>
                <td className="font-mono" style={{ padding: '14px 18px', color: 'var(--accent-primary)', fontWeight: 600, fontSize: '12px' }}>
                  {vio.id}
                </td>
                <td style={{ padding: '14px 18px' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{vio.employeeName}</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>{vio.employeeEmail}</div>
                </td>
                <td style={{ padding: '14px 18px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 600, padding: '3px 8px', borderRadius: 'var(--radius-pill)', backgroundColor: 'var(--accent-primary-light)', color: 'var(--accent-primary)' }}>
                    {vio.systemKey}
                  </span>
                </td>
                <td style={{ padding: '14px 18px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                  <div className="font-mono" style={{ color: 'var(--text-primary)', fontSize: '11px', fontWeight: 600 }}>{vio.ruleId}</div>
                  <div style={{ marginTop: '2px' }}>{vio.ruleName}</div>
                </td>
                <td style={{ padding: '14px 18px' }}>
                  <span className="font-mono" style={{ color: 'var(--status-healthy)', fontWeight: 600, fontSize: '12px' }}>
                    {vio.expectedState}
                  </span>
                </td>
                <td style={{ padding: '14px 18px' }}>
                  <span className="font-mono" style={{ color: 'var(--status-critical)', fontWeight: 600, fontSize: '12px' }}>
                    {vio.actualState}
                  </span>
                </td>
                <td style={{ padding: '14px 18px' }}>
                  <StatusPill status={vio.severity.toLowerCase()} label={vio.severity} size="small" />
                </td>
                <td style={{ padding: '14px 18px' }}>
                  <StatusPill status={vio.status === 'OPEN' ? 'warning' : 'healthy'} label={vio.status} size="small" />
                </td>
                <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                  <Link to="/approvals">
                    <Button variant="secondary" size="small" icon={ExternalLink}>
                      Remediate
                    </Button>
                  </Link>
                </td>
              </tr>
            ))}
            {filteredViolations.length === 0 && (
              <tr>
                <td colSpan="9" style={{ textAlign: 'center', padding: '48px 24px', color: 'var(--text-muted)' }}>
                  No active drift violations found. System state is verified!
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
