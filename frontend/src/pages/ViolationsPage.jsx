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
          <h1 className="page-title">
            <span>Violations</span>
          </h1>
          <p className="page-subtitle">
            Authorization drift anomalies detected across system connectors
          </p>
        </div>
        <Button variant="secondary" icon={RefreshCw} onClick={loadViolations} disabled={loading}>
          Refresh
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

      <div className="card" style={{ marginBottom: '20px', padding: '16px' }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
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
      </div>

      <div className="plain-divided-container">
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
          <thead>
            <tr style={{ backgroundColor: 'var(--bg-base)', borderBottom: '1px solid var(--border-hairline)' }}>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>ID</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Employee</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>System</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Invariant Rule</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Expected</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Actual</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Severity</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Status</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase', textAlign: 'right' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredViolations.map((vio) => (
              <tr key={vio.id} style={{ borderBottom: '1px solid var(--border-hairline)' }}>
                <td className="font-mono" style={{ padding: '12px 16px', color: 'var(--accent-primary)', fontWeight: 600, fontSize: '12px' }}>
                  {vio.id}
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{vio.employeeName}</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{vio.employeeEmail}</div>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ fontSize: '12px', fontWeight: 600, padding: '2px 8px', borderRadius: 'var(--radius-pill)', backgroundColor: 'var(--accent-primary-light)', color: 'var(--accent-primary)' }}>
                    {vio.systemKey}
                  </span>
                </td>
                <td style={{ padding: '12px 16px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                  <div className="font-mono" style={{ color: 'var(--text-primary)', fontSize: '11px' }}>{vio.ruleId}</div>
                  {vio.ruleName}
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <span className="font-mono" style={{ color: 'var(--status-healthy)', fontWeight: 600, fontSize: '12px' }}>
                    {vio.expectedState}
                  </span>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <span className="font-mono" style={{ color: 'var(--status-critical)', fontWeight: 600, fontSize: '12px' }}>
                    {vio.actualState}
                  </span>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <StatusPill status={vio.severity.toLowerCase()} label={vio.severity} size="small" />
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <StatusPill status={vio.status === 'OPEN' ? 'warning' : 'healthy'} label={vio.status} size="small" />
                </td>
                <td style={{ padding: '12px 16px', textAlign: 'right' }}>
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
                <td colSpan="9" style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
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
