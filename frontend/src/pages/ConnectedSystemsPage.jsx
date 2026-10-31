import React, { useState, useEffect } from 'react';
import { Server, Users, Shield, GitBranch, Cloud, MessageSquare, RefreshCw, AlertCircle, Info, Zap, Loader } from 'lucide-react';
import { StatusPill } from '../components/ui/StatusPill';
import { Button } from '../components/ui/Button';
import { api } from '../services/api';

const iconMap = {
  Users: Users,
  ShieldAlert: Shield,
  GitBranch: GitBranch,
  Cloud: Cloud,
  MessageSquare: MessageSquare
};

/**
 * Authentic system specifications reflecting genuine backend implementations.
 * Classification:
 * - HR: Database fallback (internal Django Employee model, no live HRIS API)
 * - VPN: Local simulation (VPNAccess ORM model with test failure modes, no live RADIUS/OpenVPN)
 * - GitHub: Database fallback (REST API code exists; active fallback because GITHUB_ACCESS_TOKEN is not set)
 * - Cloud IAM: Local simulation (CloudIAMAccess model with synthetic ARNs, no live AWS STS/IAM)
 * - Slack: Local simulation (SlackAccount model with synthetic User IDs, no live SCIM/Slack API)
 */
const SYSTEM_SPECS = [
  {
    id: 'sys-hr',
    key: 'hr',
    name: 'HR Directory (System of Record)',
    category: 'Identity & Employment Status',
    mode: 'Database fallback',
    modeVariant: 'neutral',
    configStatus: 'Internal Django Employee model (SQLite / PostgreSQL)',
    reachability: 'Not tested',
    reachabilityVariant: 'neutral',
    description: 'Internal database of record for employee identity, departments, and employment lifecycle transitions (ACTIVE, ON_LEAVE, TERMINATED).',
    capabilities: [
      'Source of truth for employee identity and lifecycle state',
      'Provides termination triggers for drift reconciliation',
      'No external HRIS (Workday / BambooHR) API integration configured'
    ],
    icon: 'Users'
  },
  {
    id: 'sys-vpn',
    key: 'vpn',
    name: 'Enterprise VPN Gateway',
    category: 'Network Access Control',
    mode: 'Local simulation',
    modeVariant: 'neutral',
    configStatus: 'Local VPNAccess ORM model with test failure hooks',
    reachability: 'Not tested',
    reachabilityVariant: 'neutral',
    description: 'Simulated downstream network access gateway with programmable transient timeout and connection drop simulation for testing.',
    capabilities: [
      'Enable and disable simulated VPN credentials',
      'Inject simulated gateway timeouts and connection drops for testing',
      'No live OpenVPN Management Interface or RADIUS server connected'
    ],
    icon: 'ShieldAlert'
  },
  {
    id: 'sys-github',
    key: 'github',
    name: 'GitHub Enterprise',
    category: 'Source Code & Organization Access',
    mode: 'Database fallback',
    modeVariant: 'warning',
    configStatus: 'Unconfigured (GITHUB_ACCESS_TOKEN not set; target org: reconcileos-org)',
    reachability: 'Not tested',
    reachabilityVariant: 'neutral',
    description: 'Manages developer organization memberships. Real REST API integration exists in code but currently runs in database fallback mode due to unconfigured token.',
    capabilities: [
      'Inspect and revoke organization membership',
      'Live REST integration supported via GITHUB_ACCESS_TOKEN',
      'Currently operating via local GitHubMembership database records'
    ],
    icon: 'GitBranch'
  },
  {
    id: 'sys-cloud',
    key: 'cloud',
    name: 'Cloud IAM (AWS)',
    category: 'Cloud Infrastructure & IAM Roles',
    mode: 'Local simulation',
    modeVariant: 'neutral',
    configStatus: 'Local CloudIAMAccess ORM model with synthetic ARNs',
    reachability: 'Not tested',
    reachabilityVariant: 'neutral',
    description: 'Simulated cloud IAM role manager with synthetic IAM ARNs (arn:aws:iam::123456789012:user/...) for role assignment and revocation.',
    capabilities: [
      'Assign and revoke simulated Cloud IAM roles (DEVELOPER, ADMIN, NO_ROLE)',
      'Track cloud identity ARNs against employee records',
      'No live AWS STS, IAM, or Cloud provider APIs connected'
    ],
    icon: 'Cloud'
  },
  {
    id: 'sys-slack',
    key: 'slack',
    name: 'Slack Workspace',
    category: 'Corporate Chat & Provisioning',
    mode: 'Local simulation',
    modeVariant: 'neutral',
    configStatus: 'Local SlackAccount ORM model with synthetic User IDs',
    reachability: 'Not tested',
    reachabilityVariant: 'neutral',
    description: 'Simulated corporate workspace account directory with synthetic Slack User IDs (U...) for account provisioning and deactivation.',
    capabilities: [
      'Activate and deactivate simulated Slack accounts',
      'Track corporate communication provisioning state',
      'No live Slack SCIM v2 or Web API integration connected'
    ],
    icon: 'MessageSquare'
  }
];

export function ConnectedSystemsPage() {
  const [systems, setSystems] = useState(SYSTEM_SPECS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [testingKey, setTestingKey] = useState(null);

  const fetchSystemStates = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statesRes, violationsRes, healthRes] = await Promise.allSettled([
        api.getCollectedStates(),
        api.getViolations(),
        api.getConnectorsHealth()
      ]);

      if (statesRes.status === 'rejected') {
        throw statesRes.reason || new Error('Failed to load multi-system telemetry from backend.');
      }

      const statesData = statesRes.value?.results || statesRes.value || [];
      const violationsData = violationsRes.status === 'fulfilled'
        ? (violationsRes.value?.results || violationsRes.value || [])
        : [];
      const healthData = healthRes.status === 'fulfilled'
        ? (healthRes.value?.systems || {})
        : {};

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

      const updated = SYSTEM_SPECS.map((baseSys) => {
        const sysKey = baseSys.key;
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

        // Merge truthful health check data from backend
        const health = healthData[sysKey];
        const reachability = health ? health.reachability : baseSys.reachability;
        const reachabilityVariant = health
          ? (health.status === 'HEALTHY' || health.status === 'SIMULATED_HEALTHY' || health.status === 'DATABASE_FALLBACK_HEALTHY'
            ? 'healthy'
            : health.status === 'ERROR' || health.status === 'CONNECTION_FAILED'
              ? 'critical'
              : health.status === 'TIMEOUT' || health.status === 'SIMULATED_FAILURE'
                ? 'warning'
                : 'neutral')
          : baseSys.reachabilityVariant;

        return {
          ...baseSys,
          monitoredAccounts: monitoredCount,
          driftCount,
          driftStatus: driftCount > 0 ? 'DRIFT_DETECTED' : 'HEALTHY',
          reachability,
          reachabilityVariant,
          latencyMs: health ? health.latency_ms : null,
          healthMessage: health ? health.message : null,
        };
      });

      setSystems(updated);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Failed to fetch connected systems telemetry:', err);
      setError(err.message || 'Failed to load connected systems state.');
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async (sysKey) => {
    setTestingKey(sysKey);
    try {
      const result = await api.checkConnectorHealth(sysKey);
      // Update system reachability in-place
      setSystems(prev => prev.map(sys => {
        if (sys.key !== sysKey) return sys;
        const reachabilityVariant =
          result.status === 'HEALTHY' || result.status === 'SIMULATED_HEALTHY' || result.status === 'DATABASE_FALLBACK_HEALTHY'
            ? 'healthy'
            : result.status === 'ERROR' || result.status === 'CONNECTION_FAILED'
              ? 'critical'
              : result.status === 'TIMEOUT' || result.status === 'SIMULATED_FAILURE'
                ? 'warning'
                : 'neutral';
        return {
          ...sys,
          reachability: result.reachability,
          reachabilityVariant,
          latencyMs: result.latency_ms,
          healthMessage: result.message,
        };
      }));
    } catch (err) {
      setSystems(prev => prev.map(sys => {
        if (sys.key !== sysKey) return sys;
        return {
          ...sys,
          reachability: 'Test Failed',
          reachabilityVariant: 'critical',
          latencyMs: null,
          healthMessage: err.message || 'Connection test failed.',
        };
      }));
    } finally {
      setTestingKey(null);
    }
  };

  useEffect(() => {
    fetchSystemStates();
  }, []);

  return (
    <div className="page-content">
      {/* Editorial Header */}
      <div className="page-header" style={{ marginBottom: '40px' }}>
        <div>
          <div className="page-eyebrow">
            <span className="page-eyebrow-dot" />
            Infrastructure Integrations
          </div>
          <h1 className="page-title">
            <span>Connected Systems & Integrations</span>
          </h1>
          <p className="page-subtitle">
            Downstream target application gateways, connection modes, and honest integration telemetry across enterprise surfaces.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '14px', alignItems: 'center' }}>
          {lastUpdated && (
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }} className="font-mono">
              Synced: {lastUpdated}
            </span>
          )}
          <Button
            variant="secondary"
            icon={RefreshCw}
            onClick={fetchSystemStates}
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh Telemetry'}
          </Button>
        </div>
      </div>

      {/* Integration Truthfulness Notice */}
      <div
        style={{
          marginBottom: '28px',
          padding: '18px 22px',
          borderRadius: 'var(--radius-card)',
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-hairline)',
          boxShadow: 'var(--shadow-card)',
          display: 'flex',
          gap: '16px',
          alignItems: 'flex-start'
        }}
      >
        <div
          style={{
            width: '32px',
            height: '32px',
            borderRadius: 'var(--radius-btn)',
            backgroundColor: 'var(--accent-primary-light)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--accent-primary)',
            flexShrink: 0,
            marginTop: '2px'
          }}
        >
          <Info size={16} />
        </div>
        <div>
          <div style={{ fontWeight: 600, fontSize: '13.5px', color: 'var(--text-primary)', marginBottom: '4px' }}>
            Integration Reality & Governance Notice
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: '1.5' }}>
            ReconcileOS distinguishes between <strong>Live integrations</strong> (authenticated third-party APIs),
            <strong> Local simulations</strong> (ORM models with programmable failure modes), and
            <strong> Database fallbacks</strong> (unconfigured integrations defaulting to local database state).
            Successful database reads do not imply live external reachability.
          </div>
        </div>
      </div>

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
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Systems Enterprise Directory */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {systems.map((sys) => {
          const Icon = iconMap[sys.icon] || Server;
          const isDrift = sys.driftStatus === 'DRIFT_DETECTED';

          return (
            <div
              key={sys.id}
              style={{
                backgroundColor: 'var(--bg-surface)',
                borderRadius: 'var(--radius-card)',
                border: '1px solid var(--border-hairline)',
                padding: '24px 28px',
                boxShadow: 'var(--shadow-card)',
                display: 'flex',
                flexDirection: 'column',
                gap: '20px'
              }}
            >
              {/* Header Row */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div
                    style={{
                      width: '46px',
                      height: '46px',
                      borderRadius: '12px',
                      backgroundColor: 'var(--accent-primary-light)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--accent-primary)',
                      flexShrink: 0
                    }}
                  >
                    <Icon size={22} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '3px' }}>
                      {sys.name}
                    </h3>
                    <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{sys.category}</div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <StatusPill
                    status={sys.modeVariant}
                    label={sys.mode}
                    size="small"
                  />
                  <StatusPill
                    status={isDrift ? 'warning' : 'healthy'}
                    label={isDrift ? `Drift Detected (${sys.driftCount})` : 'Compliant'}
                    size="small"
                  />
                </div>
              </div>

              {/* Description */}
              <p style={{ fontSize: '14px', color: 'var(--text-secondary)', lineHeight: '1.6', margin: 0, maxWidth: '800px' }}>
                {sys.description}
              </p>

              {/* Capabilities and Specs Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px', paddingTop: '8px' }}>
                <div
                  style={{
                    padding: '20px 24px',
                    borderRadius: '12px',
                    backgroundColor: 'var(--bg-base)',
                    border: '1px solid var(--border-hairline)'
                  }}
                >
                  <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '12px' }}>
                    Implementation Capabilities
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px', lineHeight: '1.5' }}>
                    {sys.capabilities.map((cap, i) => (
                      <li key={i}>{cap}</li>
                    ))}
                  </ul>
                </div>

                <div
                  style={{
                    padding: '20px 24px',
                    borderRadius: '12px',
                    backgroundColor: 'var(--bg-base)',
                    border: '1px solid var(--border-hairline)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    gap: '14px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Configuration:</span>
                    <span style={{ fontSize: '12px', color: 'var(--text-primary)', textAlign: 'right', maxWidth: '240px' }} className="font-mono">
                      {sys.configStatus}
                    </span>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>External Reachability:</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {sys.latencyMs != null && (
                        <span className="font-mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          {sys.latencyMs}ms
                        </span>
                      )}
                      <StatusPill
                        status={sys.reachabilityVariant || 'neutral'}
                        label={sys.reachability || 'Not tested'}
                        size="small"
                      />
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Monitored Accounts:</span>
                    <span className="font-mono" style={{ fontWeight: 700, fontSize: '14px', color: 'var(--accent-primary)' }}>
                      {sys.monitoredAccounts !== undefined ? `${sys.monitoredAccounts} records` : '—'}
                    </span>
                  </div>

                  {sys.healthMessage && (
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.5, marginTop: '2px', borderTop: '1px solid var(--border-hairline)', paddingTop: '10px' }}>
                      {sys.healthMessage}
                    </div>
                  )}

                  <Button
                    variant="secondary"
                    size="small"
                    icon={testingKey === sys.key ? Loader : Zap}
                    disabled={testingKey !== null}
                    onClick={() => handleTestConnection(sys.key)}
                  >
                    {testingKey === sys.key ? 'Testing…' : 'Test Connection'}
                  </Button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
