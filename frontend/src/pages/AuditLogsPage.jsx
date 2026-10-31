import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { RefreshCw, AlertCircle, ShieldCheck, ShieldAlert } from 'lucide-react';
import { TimelineEntry } from '../components/ui/TimelineEntry';
import { StatusPill } from '../components/ui/StatusPill';
import { Button } from '../components/ui/Button';
import { api } from '../services/api';
import { PaginationControls } from '../components/ui/PaginationControls';

export function AuditLogsPage() {
  const [searchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState('TIMELINE');
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [error, setError] = useState(null);
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

  const fetchAuditLogs = useCallback(async (page, search) => {
    setLoading(true);
    setError(null);
    const fetchId = ++fetchIdRef.current;
    try {
      const params = new URLSearchParams();
      params.set('page', String(page));
      if (search && search.trim()) params.set('search', search.trim());
      const res = await api.getAuditLogs(`?${params.toString()}`);
      if (fetchId !== fetchIdRef.current) return;
      const rawList = res.results || res;
      const count = res.count != null ? res.count : (Array.isArray(rawList) ? rawList.length : 0);
      if (Array.isArray(rawList)) {
        const formatted = rawList.map((item) => ({
          id: item.id ? `AUD-${String(item.id).substring(0, 8).toUpperCase()}` : (item.correlation_id || 'AUD-0000'),
          timestamp: item.timestamp ? new Date(item.timestamp).toLocaleString() : 'Just now',
          eventType: item.event_type || 'EVENT',
          actor: item.actor || 'SYSTEM',
          target: item.employee_name || item.employee_email || item.action || 'Directory Resource',
          system: item.system || 'SYSTEM',
          status: item.result || 'SUCCESS',
          details: item.action || `Event: ${item.event_type}`
        }));
        setLogs(formatted);
        setTotalCount(count);
      }
    } catch (err) {
      if (fetchId !== fetchIdRef.current) return;
      console.warn('API error fetching audit logs:', err);
      setError(err.message || 'Failed to fetch audit logs from backend.');
    } finally {
      if (fetchId === fetchIdRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    fetchAuditLogs(currentPage, searchQuery);
  }, [currentPage, searchQuery, fetchAuditLogs]);

  // Server-side filtering: logs are already filtered by the backend
  const filteredLogs = logs;

  const handleVerifyChain = async () => {
    setVerifying(true);
    setVerificationResult(null);
    try {
      const res = await api.verifyAuditChain();
      setVerificationResult({
        isValid: res.is_valid,
        message: res.message,
        details: res.details
      });
    } catch (err) {
      if (err.data && err.data.is_valid === false) {
        setVerificationResult({
          isValid: false,
          message: err.data.message || 'Audit chain integrity validation failed.',
          details: err.data.details
        });
      } else {
        setVerificationResult({
          error: true,
          message: err.message || 'Failed to communicate with audit verification endpoint.'
        });
      }
    } finally {
      setVerifying(false);
    }
  };


  return (
    <div className="page-content">
      {/* Editorial Header */}
      <div className="page-header" style={{ marginBottom: '40px' }}>
        <div>
          <div className="page-eyebrow">
            <span className="page-eyebrow-dot" />
            Cryptographic Chain
          </div>
          <h1 className="page-title">
            <span>Audit Stream & Tamper-Evidence</span>
          </h1>
          <p className="page-subtitle">
            Cryptographically chained SHA-256 event trail guaranteeing non-repudiation of all identity decisions.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <Button
            variant="primary"
            icon={ShieldCheck}
            onClick={handleVerifyChain}
            disabled={verifying || loading}
          >
            {verifying ? 'Verifying Integrity...' : 'Verify Cryptographic Chain'}
          </Button>
          <Button variant="secondary" icon={RefreshCw} onClick={() => fetchAuditLogs(currentPage, searchQuery)} disabled={loading || verifying}>
            Refresh
          </Button>
          <div style={{ display: 'flex', gap: '4px', backgroundColor: 'var(--bg-surface)', padding: '3px', borderRadius: 'var(--radius-btn)', border: '1px solid var(--border-hairline)' }}>
            <Button
              variant={activeTab === 'TIMELINE' ? 'primary' : 'ghost'}
              size="small"
              onClick={() => setActiveTab('TIMELINE')}
            >
              Timeline
            </Button>
            <Button
              variant={activeTab === 'TABLE' ? 'primary' : 'ghost'}
              size="small"
              onClick={() => setActiveTab('TABLE')}
            >
              Data Grid
            </Button>
          </div>
        </div>
      </div>

      {verificationResult && (
        verificationResult.error ? (
          <div
            style={{
              marginBottom: '24px',
              padding: '14px 18px',
              borderRadius: 'var(--radius-card)',
              backgroundColor: 'var(--status-critical-bg)',
              border: '1px solid var(--status-critical-border)',
              color: 'var(--status-critical)',
              fontSize: '13px',
              fontWeight: 500,
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}
          >
            <AlertCircle size={18} />
            <span>Verification Error: {verificationResult.message}</span>
          </div>
        ) : verificationResult.isValid ? (
          <div
            style={{
              marginBottom: '24px',
              padding: '18px 22px',
              borderRadius: 'var(--radius-card)',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--status-healthy-border)',
              boxShadow: 'var(--shadow-card)',
              color: 'var(--status-healthy)',
              fontSize: '13px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontWeight: 600, fontSize: '14px' }}>
              <ShieldCheck size={18} />
              <span>{verificationResult.message}</span>
            </div>
            {verificationResult.details && (
              <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginLeft: '28px' }}>
                Verified {verificationResult.details.verified_records} of {verificationResult.details.total_records} record(s) intact.
                {verificationResult.details.head_hash && (
                  <span className="font-mono" style={{ marginLeft: '8px', fontSize: '11px', color: 'var(--accent-primary)' }}>
                    (Head SHA-256: {verificationResult.details.head_hash.substring(0, 20)}...)
                  </span>
                )}
              </div>
            )}
          </div>
        ) : (
          <div
            style={{
              marginBottom: '24px',
              padding: '18px 22px',
              borderRadius: 'var(--radius-card)',
              backgroundColor: 'var(--status-critical-bg)',
              border: '1px solid var(--status-critical-border)',
              color: 'var(--status-critical)',
              fontSize: '13px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontWeight: 600, fontSize: '14px' }}>
              <ShieldAlert size={18} />
              <span>{verificationResult.message}</span>
            </div>
            {verificationResult.details && (
              <div style={{ fontSize: '12.5px', opacity: 0.9, marginLeft: '28px' }}>
                Reason: {verificationResult.details.reason} (Tampered Record ID: {verificationResult.details.tampered_record_id || 'Unknown'})
              </div>
            )}
          </div>
        )
      )}

      {error && (
        <div
          style={{
            marginBottom: '24px',
            padding: '14px 18px',
            borderRadius: 'var(--radius-card)',
            backgroundColor: 'var(--status-critical-bg)',
            border: '1px solid var(--status-critical-border)',
            color: 'var(--status-critical)',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div style={{ padding: '60px 24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
          Loading cryptographic audit chain...
        </div>
      ) : filteredLogs.length === 0 ? (
        <div
          style={{
            padding: '48px 24px',
            textAlign: 'center',
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 'var(--radius-card)',
            border: '1px solid var(--border-hairline)',
            color: 'var(--text-muted)'
          }}
        >
          {searchQuery ? `No audit records matching "${searchQuery}".` : 'No audit log records available.'}
        </div>
      ) : activeTab === 'TIMELINE' ? (
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 'var(--radius-card)',
            border: '1px solid var(--border-hairline)',
            padding: '28px 32px',
            boxShadow: 'var(--shadow-card)'
          }}
        >
          {filteredLogs.map((log, idx) => (
            <TimelineEntry
              key={log.id}
              timestamp={log.timestamp}
              title={`${log.eventType} — ${log.system}`}
              description={`${log.details} (Actor: ${log.actor}, Target: ${log.target})`}
              status={log.status === 'CRITICAL' || log.status === 'FAILURE' ? 'critical' : log.status === 'SUCCESS' ? 'healthy' : 'warning'}
              isLast={idx === filteredLogs.length - 1}
            />
          ))}
        </div>
      ) : (
        <div className="editorial-table-container">
          <table className="editorial-table">
            <thead>
              <tr>
                <th>Log ID</th>
                <th>Timestamp</th>
                <th>Event Type</th>
                <th>Actor</th>
                <th>Target</th>
                <th>System</th>
                <th>Outcome</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((log) => (
                <tr key={log.id}>
                  <td className="font-mono" style={{ color: 'var(--accent-primary)', fontWeight: 600, fontSize: '13px' }}>
                    {log.id}
                  </td>
                  <td className="font-mono" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    {log.timestamp}
                  </td>
                  <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    {log.eventType}
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>{log.actor}</td>
                  <td style={{ color: 'var(--text-secondary)' }}>{log.target}</td>
                  <td>
                    <span style={{ fontSize: '12px', fontWeight: 600, padding: '3px 10px', borderRadius: '9999px', backgroundColor: 'var(--accent-primary-light)', color: 'var(--accent-primary)' }}>
                      {log.system}
                    </span>
                  </td>
                  <td>
                    <StatusPill status={log.status === 'CRITICAL' || log.status === 'FAILURE' ? 'critical' : log.status === 'SUCCESS' ? 'healthy' : 'warning'} label={log.status} size="small" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

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

