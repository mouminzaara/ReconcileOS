import React, { useState, useEffect } from 'react';
import { AlertTriangle, Filter, ExternalLink, RefreshCw } from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { api } from '../services/api';
import { mockViolations } from '../data/mockData';
import { Link } from 'react-router-dom';

export function ViolationsPage() {
  const [violations, setViolations] = useState(mockViolations);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('ALL');

  const loadViolations = async () => {
    setLoading(true);
    try {
      const res = await api.getViolations();
      const list = res.results || res;
      if (Array.isArray(list) && list.length > 0) {
        const formatted = list.map(v => ({
          id: `VIO-${(v.id || '').substring(0, 8).toUpperCase()}`,
          fullId: v.id,
          employeeName: v.employee_name || (v.employee && v.employee.full_name) || 'Rahul Kumar',
          employeeEmail: v.employee_email || (v.employee && v.employee.email) || 'rahul.kumar@reconcileos.internal',
          systemKey: v.affected_system || 'VPN',
          ruleId: v.rule_code || 'INV-RULE-001',
          ruleName: v.rule_name || 'Invariant Security Rule',
          expectedState: v.expected_state || 'DISABLED',
          actualState: v.actual_state || 'ENABLED',
          severity: v.severity || 'CRITICAL',
          status: v.status || 'OPEN',
          detectedAt: v.detected_at ? new Date(v.detected_at).toLocaleString() : 'Just now'
        }));
        setViolations(formatted);
      }
    } catch (err) {
      console.warn('API error loading violations, using mock data:', err);
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
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <AlertTriangle size={24} style={{ color: 'var(--status-danger)' }} />
            Authorization Drift Matrix (Violations)
          </h1>
          <p className="page-subtitle">
            Real-time detected authorization anomalies across downstream system states
          </p>
        </div>
        <button className="btn btn-secondary" onClick={loadViolations} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh Matrix
        </button>
      </div>

      <div className="card" style={{ marginBottom: '20px', padding: '16px' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <Filter size={16} style={{ color: 'var(--text-muted)' }} />
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Filter Severity:</span>
          <button
            className={`btn ${severityFilter === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '4px 12px', fontSize: '0.75rem' }}
            onClick={() => setSeverityFilter('ALL')}
          >
            All ({violations.length})
          </button>
          <button
            className={`btn ${severityFilter === 'CRITICAL' ? 'btn-danger' : 'btn-secondary'}`}
            style={{ padding: '4px 12px', fontSize: '0.75rem' }}
            onClick={() => setSeverityFilter('CRITICAL')}
          >
            Critical ({violations.filter(v => v.severity === 'CRITICAL').length})
          </button>
          <button
            className={`btn ${severityFilter === 'HIGH' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '4px 12px', fontSize: '0.75rem' }}
            onClick={() => setSeverityFilter('HIGH')}
          >
            High ({violations.filter(v => v.severity === 'HIGH').length})
          </button>
          <button
            className={`btn ${severityFilter === 'MEDIUM' ? 'btn-secondary' : 'btn-secondary'}`}
            style={{ padding: '4px 12px', fontSize: '0.75rem' }}
            onClick={() => setSeverityFilter('MEDIUM')}
          >
            Medium ({violations.filter(v => v.severity === 'MEDIUM').length})
          </button>
        </div>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Violation ID</th>
              <th>Employee Name</th>
              <th>System</th>
              <th>Evaluated Invariant Rule</th>
              <th>Expected State</th>
              <th>Actual State</th>
              <th>Severity</th>
              <th>Drift Status</th>
              <th>Detected Timestamp</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredViolations.map((vio) => (
              <tr key={vio.id}>
                <td className="mono" style={{ color: 'var(--accent-blue)', fontWeight: 600 }}>
                  {vio.id}
                </td>
                <td>
                  <div style={{ fontWeight: 600 }}>{vio.employeeName}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{vio.employeeEmail}</div>
                </td>
                <td>
                  <span className="badge badge-info">{vio.systemKey}</span>
                </td>
                <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  <div className="mono" style={{ color: 'var(--text-main)', fontSize: '0.75rem' }}>{vio.ruleId}</div>
                  {vio.ruleName}
                </td>
                <td>
                  <span className="mono" style={{ color: 'var(--status-success)', fontWeight: 600 }}>
                    {vio.expectedState}
                  </span>
                </td>
                <td>
                  <span className="mono" style={{ color: 'var(--status-danger)', fontWeight: 600 }}>
                    {vio.actualState}
                  </span>
                </td>
                <td>
                  <SeverityBadge severity={vio.severity} />
                </td>
                <td>
                  <StatusBadge status={vio.status} />
                </td>
                <td className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {vio.detectedAt}
                </td>
                <td>
                  <Link to="/approvals" className="btn btn-secondary" style={{ fontSize: '0.75rem', padding: '4px 8px' }}>
                    Remediate <ExternalLink size={12} />
                  </Link>
                </td>
              </tr>
            ))}
            {filteredViolations.length === 0 && (
              <tr>
                <td colSpan="10" style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                  No active drift violations found. System is 100% consistent!
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
