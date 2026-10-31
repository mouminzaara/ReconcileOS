import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Filter, ExternalLink, RefreshCw, AlertCircle } from 'lucide-react';
import { StatusPill } from '../components/ui/StatusPill';
import { Button } from '../components/ui/Button';
import { api } from '../services/api';
import { PaginationControls } from '../components/ui/PaginationControls';
import { Link, useSearchParams } from 'react-router-dom';

export function ViolationsPage() {
  const [searchParams] = useSearchParams();
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const fetchIdRef = useRef(0);

  useEffect(() => {
    const q = searchParams.get('search');
    if (q !== null) {
      setSearchQuery(q);
    }
  }, [searchParams]);

  const loadViolations = useCallback(async (page, search, severity) => {
    setLoading(true);
    setError(null);
    const fetchId = ++fetchIdRef.current;
    try {
      const params = new URLSearchParams();
      params.set('page', String(page));
      if (search && search.trim()) params.set('search', search.trim());
      if (severity && severity !== 'ALL') params.set('severity', severity);
      const res = await api.getViolations(`?${params.toString()}`);
      if (fetchId !== fetchIdRef.current) return;
      const list = res.results || res;
      const count = res.count != null ? res.count : (Array.isArray(list) ? list.length : 0);
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
        setTotalCount(count);
      } else {
        setViolations([]);
        setTotalCount(0);
      }
    } catch (err) {
      if (fetchId !== fetchIdRef.current) return;
      console.error('API error loading violations:', err);
      setError(err.message || 'Failed to load violations from backend.');
      setViolations([]);
      setTotalCount(0);
    } finally {
      if (fetchId === fetchIdRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    loadViolations(currentPage, searchQuery, severityFilter);
  }, [currentPage, searchQuery, severityFilter, loadViolations]);


  const handleSeverityFilterChange = (value) => {
    setSeverityFilter(value);
    setCurrentPage(1);
  };

  // Server-side filtering: violations are already filtered by the backend
  const filteredViolations = violations;

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
          <Button variant="secondary" icon={RefreshCw} onClick={() => loadViolations(currentPage, searchQuery, severityFilter)} disabled={loading}>
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
          onClick={() => handleSeverityFilterChange('ALL')}
        >
          All ({totalCount})
        </Button>
        <Button
          variant={severityFilter === 'CRITICAL' ? 'danger' : 'secondary'}
          size="small"
          onClick={() => handleSeverityFilterChange('CRITICAL')}
        >
          Critical
        </Button>
        <Button
          variant={severityFilter === 'HIGH' ? 'primary' : 'secondary'}
          size="small"
          onClick={() => handleSeverityFilterChange('HIGH')}
        >
          High
        </Button>
        <Button
          variant={severityFilter === 'MEDIUM' ? 'secondary' : 'secondary'}
          size="small"
          onClick={() => handleSeverityFilterChange('MEDIUM')}
        >
          Medium
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
                <td style={{ padding: '12px 16px' }}>
                  <span className="font-mono" style={{ color: 'var(--status-healthy)', backgroundColor: 'var(--status-healthy-bg)', border: '1px solid var(--status-healthy-border)', padding: '2px 6px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>
                    {vio.expectedState}
                  </span>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <span className="font-mono" style={{ color: 'var(--status-critical)', backgroundColor: 'var(--status-critical-bg)', border: '1px solid var(--status-critical-border)', padding: '2px 6px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>
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

      {/* Server-side Pagination Controls */}
      <PaginationControls
        currentPage={currentPage}
        pageSize={20}
        totalCount={totalCount}
        onPageChange={setCurrentPage}
        loading={loading}
      />
    </div>
  );
}
