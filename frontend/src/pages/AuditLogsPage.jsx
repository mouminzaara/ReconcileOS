import React, { useState, useEffect } from 'react';
import { RefreshCw, AlertCircle, ShieldCheck, ShieldAlert } from 'lucide-react';
import { TimelineEntry } from '../components/ui/TimelineEntry';
import { StatusPill } from '../components/ui/StatusPill';
import { Button } from '../components/ui/Button';
import { api } from '../services/api';

export function AuditLogsPage() {
  const [activeTab, setActiveTab] = useState('TIMELINE');
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [error, setError] = useState(null);

  const fetchAuditLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAuditLogs();
      const rawList = res.results || res;
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
      }
    } catch (err) {
      console.warn('API error fetching audit logs:', err);
      setError(err.message || 'Failed to fetch audit logs from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, []);

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
          <Button variant="secondary" icon={RefreshCw} onClick={fetchAuditLogs} disabled={loading || verifying}>
            Refresh
          </Button>
          <div style={{ display: 'flex', gap: '6px', backgroundColor: 'var(--bg-base)', padding: '4px', borderRadius: '9999px', border: '1px solid var(--border-hairline)' }}>
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
              marginBottom: '32px',
              padding: '16px 22px',
              borderRadius: '12px',
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
            <AlertCircle size={18} />
            <span>Verification Error: {verificationResult.message}</span>
          </div>
        ) : verificationResult.isValid ? (
          <div
            style={{
              marginBottom: '32px',
              padding: '20px 24px',
              borderRadius: '16px',
              backgroundColor: '#FFFDF9',
              border: '1px solid var(--status-healthy-border)',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.02)',
              color: 'var(--status-healthy)',
              fontSize: '13px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontWeight: 700, fontSize: '15px' }}>
              <ShieldCheck size={20} />
              <span>{verificationResult.message}</span>
            </div>
            {verificationResult.details && (
              <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginLeft: '30px' }}>
                Verified {verificationResult.details.verified_records} of {verificationResult.details.total_records} record(s) intact.
                {verificationResult.details.head_hash && (
                  <span className="font-mono" style={{ marginLeft: '8px', fontSize: '12px', color: 'var(--accent-primary)' }}>
                    (Head SHA-256: {verificationResult.details.head_hash.substring(0, 20)}...)
                  </span>
                )}
              </div>
            )}
          </div>
        ) : (
          <div
            style={{
              marginBottom: '32px',
              padding: '20px 24px',
              borderRadius: '16px',
              backgroundColor: 'var(--status-critical-bg)',
              border: '1px solid var(--status-critical-border)',
              color: 'var(--status-critical)',
              fontSize: '13px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontWeight: 700, fontSize: '15px' }}>
              <ShieldAlert size={20} />
              <span>{verificationResult.message}</span>
            </div>
            {verificationResult.details && (
              <div style={{ fontSize: '13px', opacity: 0.9, marginLeft: '30px' }}>
                Reason: {verificationResult.details.reason} (Tampered Record ID: {verificationResult.details.tampered_record_id || 'Unknown'})
              </div>
            )}
          </div>
        )
      )}

      {error && (
        <div
          style={{
            marginBottom: '32px',
            padding: '16px 22px',
            borderRadius: '12px',
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
        <div style={{ padding: '60px 24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '14px' }}>
          Loading cryptographic audit chain...
        </div>
      ) : logs.length === 0 ? (
        <div
          style={{
            padding: '60px 24px',
            textAlign: 'center',
            backgroundColor: '#FFFDF9',
            borderRadius: '16px',
            border: '1px solid rgba(120, 101, 165, 0.12)',
            color: 'var(--text-muted)'
          }}
        >
          No audit log records available.
        </div>
      ) : activeTab === 'TIMELINE' ? (
        <div
          style={{
            backgroundColor: '#FFFDF9',
            borderRadius: '16px',
            border: '1px solid rgba(120, 101, 165, 0.12)',
            padding: '40px 48px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.02)'
          }}
        >
          {logs.map((log, idx) => (
            <TimelineEntry
              key={log.id}
              timestamp={log.timestamp}
              title={`${log.eventType} — ${log.system}`}
              description={`${log.details} (Actor: ${log.actor}, Target: ${log.target})`}
              status={log.status === 'CRITICAL' || log.status === 'FAILURE' ? 'critical' : log.status === 'SUCCESS' ? 'healthy' : 'warning'}
              isLast={idx === logs.length - 1}
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
              {logs.map((log) => (
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
    </div>
  );
}

