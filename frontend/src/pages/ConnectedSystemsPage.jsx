import React, { useState, useEffect } from 'react';
import { Server, Users, Shield, GitBranch, Cloud, MessageSquare, RefreshCw, AlertCircle } from 'lucide-react';
import { StatusPill } from '../components/ui/StatusPill';
import { Button } from '../components/ui/Button';
import { mockConnectedSystems } from '../data/mockData';
import { api } from '../services/api';

const iconMap = {
  Users: Users,
  ShieldAlert: Shield,
  GitBranch: GitBranch,
  Cloud: Cloud,
  MessageSquare: MessageSquare
};

export function ConnectedSystemsPage() {
  const [systems, setSystems] = useState(mockConnectedSystems);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSystemStates = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statesRes, violationsRes] = await Promise.allSettled([
        api.getCollectedStates(),
        api.getViolations()
      ]);

      if (statesRes.status === 'rejected') {
        throw statesRes.reason || new Error('Failed to load multi-system telemetry from backend.');
      }

      const statesData = statesRes.value?.results || statesRes.value || [];
      const violationsData = violationsRes.status === 'fulfilled'
        ? (violationsRes.value?.results || violationsRes.value || [])
        : [];

      const openViolations = Array.isArray(violationsData)
        ? violationsData.filter(v => v.status === 'OPEN')
        : [];

      const hasDriftInState = (key) => {
        return Array.isArray(statesData) && statesData.some(st => {
          if (st.employee_status !== 'TERMINATED') return false;
          const s = st.systems?.[key];
          if (!s) return false;
          if (key === 'vpn') return s.access_status === 'ENABLED';
          if (key === 'github') return s.access_status === 'MEMBER' || s.access_status === 'ACTIVE';
          if (key === 'cloud') return s.access_status && s.access_status !== 'NO_ROLE' && s.access_status !== 'NOT_PROVISIONED' && s.access_status !== 'REVOKED';
          if (key === 'slack') return s.access_status === 'ACTIVE';
          return false;
        });
      };

      const updatedSystems = mockConnectedSystems.map((baseSys) => {
        const sysKey = (baseSys.key || '').toLowerCase();
        let monitoredCount = 0;
        let driftCount = 0;

        if (sysKey === 'hr') {
          monitoredCount = Array.isArray(statesData) ? statesData.length : 0;
          driftCount = openViolations.filter(v => (v.affected_system || '').toLowerCase() === 'hr').length;
        } else {
          monitoredCount = Array.isArray(statesData)
            ? statesData.filter(st => {
                const s = st.systems?.[sysKey];
                if (!s) return false;
                return s.connected === true || (s.access_status && s.access_status !== 'NOT_PROVISIONED');
              }).length
            : 0;

          driftCount = openViolations.filter(v => (v.affected_system || '').toLowerCase() === sysKey).length;
          if (driftCount === 0 && hasDriftInState(sysKey)) {
            driftCount = 1;
          }
        }

        const isDrift = driftCount > 0;

        return {
          ...baseSys,
          activeAccounts: monitoredCount,
          driftCount,
          status: isDrift ? 'DRIFT_DETECTED' : 'HEALTHY',
          lastChecked: 'Just now'
        };
      });

      setSystems(updatedSystems);
    } catch (err) {
      console.error('Failed to fetch connected systems state:', err);
      setError(err.message || 'Failed to load connected systems state.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemStates();
  }, []);

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <span>Connected Systems</span>
          </h1>
          <p className="page-subtitle">
            Downstream target application gateways and telemetry connectors
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <Button
            variant="secondary"
            icon={RefreshCw}
            onClick={fetchSystemStates}
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </Button>
          <Button
            variant="secondary"
            disabled={true}
            title="Gateway connector test API endpoint is not implemented in the backend"
          >
            Test Connectors (Unavailable)
          </Button>
        </div>
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

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
        {systems.map((sys) => {
          const Icon = iconMap[sys.icon] || Server;
          const isDrift = sys.status === 'DRIFT_DETECTED';

          return (
            <div key={sys.id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div
                      style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: 'var(--radius-btn)',
                        backgroundColor: 'var(--accent-primary-light)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--accent-primary)'
                      }}
                    >
                      <Icon size={18} />
                    </div>
                    <div>
                      <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>{sys.name}</h4>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{sys.type}</div>
                    </div>
                  </div>
                  <StatusPill status={isDrift ? 'warning' : 'healthy'} label={isDrift ? 'Drift' : 'Healthy'} size="small" />
                </div>

                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: '1.4' }}>
                  {sys.description}
                </p>
              </div>

              <div style={{ borderTop: '1px solid var(--border-hairline)', paddingTop: '12px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Protocol:</span>
                  <span className="font-mono" style={{ color: 'var(--text-primary)' }}>{sys.protocol}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Latency:</span>
                  <span className="font-mono" style={{ color: 'var(--text-primary)' }}>{sys.latency}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Monitored Accounts:</span>
                  <span className="font-mono" style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>{sys.activeAccounts} accounts</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
