import React, { useState, useEffect } from 'react';
import { Zap, RefreshCw, AlertCircle } from 'lucide-react';
import { StructuredRuleCard } from '../components/ui/StructuredRuleCard';
import { Button } from '../components/ui/Button';
import { api } from '../services/api';

export function RulesPage() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const loadRules = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getRules();
      const list = res.results || res;
      if (Array.isArray(list)) {
        const formatted = list.map(r => ({
          id: r.rule_code || r.id,
          name: r.name,
          description: r.description,
          targetSystems: [r.source_system || 'HR', r.target_system || 'VPN'],
          severity: r.severity || 'HIGH',
          status: r.is_enabled ? 'ENFORCED' : 'DISABLED',
          condition: r.rule_expression || `${r.source_system || 'HR'}.${r.condition_attribute || 'Status'} == '${r.condition_value || r.expected_source_status || 'TERMINATED'}'`,
          consequence: `${r.target_system || 'VPN'}.${r.expected_attribute || 'Access'} = '${r.expected_value || r.expected_target_status || 'DISABLED'}'`
        }));
        setRules(formatted);
      } else {
        setRules([]);
      }
    } catch (err) {
      console.error('API error loading rules:', err);
      setError(err.message || 'Failed to load invariant rules from backend.');
      setRules([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRules();
  }, []);

  const handleEvaluateAll = async () => {
    setActionLoading(true);
    try {
      await api.runReconciliation();
      await loadRules();
    } catch (err) {
      alert(`Rule evaluation error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <span>Rules Engine</span>
          </h1>
          <p className="page-subtitle">
            Formal multi-system integrity invariants enforced deterministically across apps
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button variant="secondary" icon={RefreshCw} onClick={loadRules} disabled={loading}>
            Refresh
          </Button>
          <Button variant="primary" icon={Zap} onClick={handleEvaluateAll} disabled={actionLoading || loading}>
            Evaluate All Rules
          </Button>
        </div>
      </div>

      {error && (
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
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            flexWrap: 'wrap'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
          <Button variant="secondary" size="small" icon={RefreshCw} onClick={loadRules} disabled={loading}>
            Retry
          </Button>
        </div>
      )}

      {loading && rules.length === 0 && (
        <div style={{ textAlign: 'center', padding: '48px 24px', color: 'var(--text-muted)' }}>
          Loading invariant rules...
        </div>
      )}

      {!loading && !error && rules.length === 0 && (
        <div className="card" style={{ textAlign: 'center', padding: '48px 24px', color: 'var(--text-muted)' }}>
          No invariant rules configured.
        </div>
      )}

      {rules.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px' }}>
          {rules.map((rule) => (
            <StructuredRuleCard
              key={rule.id}
              ruleId={rule.id}
              title={rule.name}
              condition={rule.condition || "HR.Status == 'TERMINATED'"}
              consequence={rule.consequence || "VPN.Access = 'DISABLED'"}
              severity={rule.severity}
              status={rule.status}
              targetSystems={rule.targetSystems}
            />
          ))}
        </div>
      )}
    </div>
  );
}
