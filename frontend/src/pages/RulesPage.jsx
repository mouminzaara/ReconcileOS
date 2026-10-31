import React, { useState, useEffect } from 'react';
import { Zap, RefreshCw, AlertCircle, Power, Sparkles, CheckCircle2 } from 'lucide-react';
import { StructuredRuleCard } from '../components/ui/StructuredRuleCard';
import { Button } from '../components/ui/Button';
import { api } from '../services/api';

export function RulesPage() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [toggleLoadingId, setToggleLoadingId] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [draftPrompt, setDraftPrompt] = useState('');
  const [draftLoading, setDraftLoading] = useState(false);

  const showFeedback = (message, type = 'success') => {
    setFeedback({ message, type });
    setTimeout(() => setFeedback(null), 5000);
  };

  const loadRules = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getRules();
      const list = res.results || res;
      if (Array.isArray(list)) {
        const formatted = list.map(r => ({
          id: r.id,
          ruleCode: r.rule_code || r.id,
          name: r.name,
          description: r.description,
          targetSystems: [r.source_system || 'HR', r.target_system || 'VPN'],
          severity: r.severity || 'HIGH',
          isEnabled: r.is_enabled,
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
    setFeedback(null);
    try {
      const res = await api.runReconciliation();
      showFeedback(res.message || 'Rule evaluation completed successfully.');
      await loadRules();
    } catch (err) {
      showFeedback(`Rule evaluation error: ${err.message}`, 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleToggleRule = async (ruleId) => {
    if (toggleLoadingId) return;
    setToggleLoadingId(ruleId);
    setFeedback(null);
    try {
      const res = await api.toggleRule(ruleId);
      showFeedback(res.message || 'Rule status updated.');
      await loadRules();
    } catch (err) {
      showFeedback(`Toggle failed: ${err.message}`, 'error');
      await loadRules();
    } finally {
      setToggleLoadingId(null);
    }
  };

  const handleGenerateDraft = async () => {
    if (!draftPrompt.trim() || draftLoading) return;
    setDraftLoading(true);
    setFeedback(null);
    try {
      const res = await api.generateDraftRule(draftPrompt.trim());
      showFeedback(res.message || 'AI draft rule created. Review and enable it below.');
      setDraftPrompt('');
      await loadRules();
    } catch (err) {
      showFeedback(`AI draft generation failed: ${err.message}`, 'error');
    } finally {
      setDraftLoading(false);
    }
  };

  return (
    <div className="page-content">
      {/* Editorial Header */}
      <div className="page-header" style={{ marginBottom: '40px' }}>
        <div>
          <div className="page-eyebrow">
            <span className="page-eyebrow-dot" />
            Invariant Enforcement
          </div>
          <h1 className="page-title">
            <span>Invariant Rules Engine</span>
          </h1>
          <p className="page-subtitle">
            Formal multi-system integrity invariants enforced deterministically across enterprise applications and access gateways.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <Button variant="secondary" icon={RefreshCw} onClick={loadRules} disabled={loading}>
            Refresh
          </Button>
          <Button variant="primary" icon={Zap} onClick={handleEvaluateAll} disabled={actionLoading || loading}>
            {actionLoading ? 'Evaluating...' : 'Evaluate All Invariants'}
          </Button>
        </div>
      </div>

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
            justifyContent: 'space-between',
            gap: '12px',
            flexWrap: 'wrap'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontWeight: 600 }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
          <Button variant="secondary" size="small" icon={RefreshCw} onClick={loadRules} disabled={loading}>
            Retry
          </Button>
        </div>
      )}

      {feedback && (
        <div
          style={{
            marginBottom: '32px',
            padding: '16px 22px',
            borderRadius: '12px',
            backgroundColor: feedback.type === 'error'
              ? 'var(--status-critical-bg)'
              : 'var(--status-healthy-bg)',
            border: `1px solid ${feedback.type === 'error'
              ? 'var(--status-critical-border)'
              : 'var(--status-healthy-border)'}`,
            color: feedback.type === 'error'
              ? 'var(--status-critical)'
              : 'var(--status-healthy)',
            fontSize: '13px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          {feedback.type === 'error' ? <AlertCircle size={18} /> : <CheckCircle2 size={18} />}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* AI Rule Draft Natural Language Prompt Box */}
      <div
        style={{
          marginBottom: '28px',
          padding: '22px 26px',
          borderRadius: 'var(--radius-card)',
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-hairline)',
          boxShadow: 'var(--shadow-card)',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px'
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-primary)', fontWeight: 600, fontSize: '13px', marginBottom: '4px' }}>
            <Sparkles size={16} />
            <span>AI Rule Synthesis</span>
          </div>
          <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)' }}>
            Describe an identity invariant in natural language. The system synthesizes formal logic into a draft rule requiring administrative review.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            id="draft-prompt-input"
            type="text"
            value={draftPrompt}
            onChange={(e) => setDraftPrompt(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleGenerateDraft(); }}
            placeholder="e.g. Terminated employees must not retain active Slack accounts or VPN credentials"
            disabled={draftLoading}
            className="input-base"
            style={{
              flex: 1,
              minWidth: '280px',
              height: '38px',
              borderRadius: 'var(--radius-input)',
              backgroundColor: '#F8F5FD'
            }}
          />
          <Button
            variant="primary"
            icon={Sparkles}
            onClick={handleGenerateDraft}
            disabled={draftLoading || !draftPrompt.trim()}
          >
            {draftLoading ? 'Synthesizing…' : 'Generate Draft Rule'}
          </Button>
        </div>
      </div>

      {loading && rules.length === 0 && (
        <div style={{ textAlign: 'center', padding: '60px 24px', color: 'var(--text-muted)', fontSize: '14px' }}>
          Loading invariant rules...
        </div>
      )}

      {!loading && !error && rules.length === 0 && (
        <div
          style={{
            textAlign: 'center',
            padding: '60px 24px',
            backgroundColor: '#FFFDF9',
            borderRadius: '16px',
            border: '1px solid rgba(120, 101, 165, 0.12)',
            color: 'var(--text-muted)'
          }}
        >
          No invariant rules configured.
        </div>
      )}

      {rules.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {rules.map((rule) => (
            <div key={rule.ruleCode} style={{ position: 'relative' }}>
              <StructuredRuleCard
                ruleId={rule.ruleCode}
                title={rule.name}
                condition={rule.condition}
                consequence={rule.consequence}
                severity={rule.severity}
                status={rule.status}
                targetSystems={rule.targetSystems}
              />
              <div style={{ position: 'absolute', bottom: '26px', right: '32px' }}>
                <Button
                  variant={rule.isEnabled ? 'secondary' : 'primary'}
                  size="small"
                  icon={Power}
                  onClick={() => handleToggleRule(rule.id)}
                  disabled={toggleLoadingId === rule.id || !!toggleLoadingId}
                >
                  {toggleLoadingId === rule.id
                    ? 'Updating…'
                    : rule.isEnabled
                      ? 'Disable Rule'
                      : 'Enable Rule'}
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
