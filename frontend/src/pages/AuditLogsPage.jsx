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
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <span>Audit Log</span>
          </h1>
          <p className="page-subtitle">
            Cryptographically chained, tamper-evident record of identity reconciliation events
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <Button
            variant="primary"
            icon={ShieldCheck}
            onClick={handleVerifyChain}
            disabled={verifying || loading}
          >
            {verifying ? 'Verifying Integrity...' : 'Verify Integrity'}
          </Button>
          <Button variant="secondary" icon={RefreshCw} onClick={fetchAuditLogs} disabled={loading || verifying}>
            Refresh Logs
          </Button>
          <Button
            variant={activeTab === 'TIMELINE' ? 'primary' : 'secondary'}
            onClick={() => setActiveTab('TIMELINE')}
          >
            Timeline Stream
          </Button>
          <Button
            variant={activeTab === 'TABLE' ? 'primary' : 'secondary'}
            onClick={() => setActiveTab('TABLE')}
          >
            Data Grid View
          </Button>
        </div>
      </div>

      {verificationResult && (
        verificationResult.error ? (
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
            <span>Verification Error: {verificationResult.message}</span>
          </div>
        ) : verificationResult.isValid ? (
          <div
            style={{
              marginBottom: '20px',
              padding: '14px 18px',
              borderRadius: 'var(--radius-btn)',
              backgroundColor: 'var(--status-healthy-bg)',
              border: '1px solid var(--status-healthy-border)',
              color: 'var(--status-healthy)',
              fontSize: '13px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
              <ShieldCheck size={18} />
              <span>{verificationResult.message}</span>
            </div>
            {verificationResult.details && (
              <div style={{ fontSize: '12px', opacity: 0.9, marginLeft: '26px' }}>
                Verified {verificationResult.details.verified_records} of {verificationResult.details.total_records} record(s) intact.
                {verificationResult.details.head_hash && (
                  <span className="font-mono" style={{ marginLeft: '6px', fontSize: '11px' }}>
                    (Head SHA-256: {verificationResult.details.head_hash.substring(0, 16)}...)
                  </span>
                )}
              </div>
            )}
          </div>
        ) : (
          <div
            style={{
              marginBottom: '20px',
              padding: '14px 18px',
              borderRadius: 'var(--radius-btn)',
              backgroundColor: 'var(--status-critical-bg)',
              border: '1px solid var(--status-critical-border)',
              color: 'var(--status-critical)',
              fontSize: '13px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
              <ShieldAlert size={18} />
              <span>{verificationResult.message}</span>
            </div>
            {verificationResult.details && (
              <div style={{ fontSize: '12px', opacity: 0.9, marginLeft: '26px' }}>
                Reason: {verificationResult.details.reason} (Tampered Record ID: {verificationResult.details.tampered_record_id || 'Unknown'})
              </div>
            )}
          </div>
        )
      )}

      {error && (
        <div
          style={{
            marginBottom: '20px',
            padding: '12px 16px',
            borderRadius: 'var(--radius-btn)',
            backgroundColor: 'var(--status-critical-bg)',
            border: '1px solid var(--status-critical-border)',
            color: 'var(--status-critical)',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="card" style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading audit logs from backend...
        </div>
      ) : logs.length === 0 ? (
        <div className="card" style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
          No audit log records available.
        </div>
      ) : activeTab === 'TIMELINE' ? (
        <div className="card" style={{ padding: '24px 32px' }}>
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
        <div className="plain-divided-container">
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--bg-base)', borderBottom: '1px solid var(--border-hairline)' }}>
                <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Log ID</th>
                <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Timestamp</th>
                <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Event Type</th>
                <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Actor</th>
                <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Target</th>
                <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>System</th>
                <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Outcome</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} style={{ borderBottom: '1px solid var(--border-hairline)' }}>
                  <td className="font-mono" style={{ padding: '12px 16px', color: 'var(--accent-primary)', fontWeight: 600, fontSize: '12px' }}>
                    {log.id}
                  </td>
                  <td className="font-mono" style={{ padding: '12px 16px', fontSize: '12px', color: 'var(--text-muted)' }}>
                    {log.timestamp}
                  </td>
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {log.eventType}
                  </td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{log.actor}</td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{log.target}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ fontSize: '12px', fontWeight: 600, padding: '2px 8px', borderRadius: 'var(--radius-pill)', backgroundColor: 'var(--accent-primary-light)', color: 'var(--accent-primary)' }}>
                      {log.system}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
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

