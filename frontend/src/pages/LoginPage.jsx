import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import {
  Shield,
  UserCheck,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  Lock,
  Zap,
  ShieldCheck,
  FileText
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { StatusPill } from '../components/ui/StatusPill';
import '../styles/login.css';

export function LoginPage() {
  const [username, setUsername] = useState('admin@reconcileos.internal');
  const [password, setPassword] = useState('admin123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(username, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || 'Invalid credentials. Please verify username and password.');
    } finally {
      setLoading(false);
    }
  };

  const handlePresetSelect = (presetUsername, presetPassword) => {
    setUsername(presetUsername);
    setPassword(presetPassword);
    setError(null);
  };

  return (
    <div className="login-page">
      {/* Ambient background glow */}
      <div className="login-ambient" aria-hidden="true" />

      <div className="login-scaffold">
        {/* Back link */}
        <Link to="/landing" className="login-back-link">
          <ArrowLeft size={14} />
          <span>Back to ReconcileOS</span>
        </Link>

        {/* Two-column composition */}
        <div className="login-columns">
          {/* Left: Brand */}
          <div className="login-brand">
            <div className="login-brand-lockup login-anim login-anim-1">
              <div className="login-brand-icon">
                <Shield size={28} />
              </div>
              <span className="login-brand-wordmark">ReconcileOS</span>
            </div>

            <h1 className="login-brand-headline login-anim login-anim-2">
              Continuous Integrity &amp; Self-Healing Identity Platform
            </h1>

            <p className="login-brand-body login-anim login-anim-3">
              Continuous drift detection and automated remediation across HR, Cloud IAM, GitHub, VPN, and Slack.
            </p>

            <ul className="login-brand-features login-anim login-anim-4">
              <li>
                <Zap size={15} />
                <span>Automated drift detection across five connected systems</span>
              </li>
              <li>
                <ShieldCheck size={15} />
                <span>Human-in-the-loop repair approvals</span>
              </li>
              <li>
                <FileText size={15} />
                <span>SHA-256 tamper-evident audit trail</span>
              </li>
            </ul>
          </div>

          {/* Right: Form Card */}
          <div className="login-card login-anim login-anim-card">
            <div className="login-card-header">
              <h2 className="login-card-title">Welcome back</h2>
              <p className="login-card-subtitle">
                Sign in to your ReconcileOS workspace.
              </p>
            </div>

            {error && (
              <div className="login-error-alert" role="alert">
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="login-form">
              <div className="login-field">
                <label className="login-label" htmlFor="login-email">
                  Work email
                </label>
                <div className="login-input-wrapper">
                  <UserCheck size={15} className="login-input-icon" />
                  <input
                    id="login-email"
                    type="text"
                    className="login-input"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="user@reconcileos.internal"
                    required
                  />
                </div>
              </div>

              <div className="login-field">
                <label className="login-label" htmlFor="login-password">
                  Password
                </label>
                <div className="login-input-wrapper">
                  <Lock size={15} className="login-input-icon" />
                  <input
                    id="login-password"
                    type="password"
                    className="login-input"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                className="login-submit-btn"
                disabled={loading}
              >
                <span>{loading ? 'Signing in…' : 'Sign in'}</span>
                {!loading && <ArrowRight size={15} />}
              </button>
            </form>

            {/* Demo accounts */}
            <div className="login-demo-section">
              <div className="login-demo-label">Demo accounts</div>
              <div className="login-demo-list">
                <button
                  type="button"
                  className="login-demo-row"
                  onClick={() => handlePresetSelect('admin@reconcileos.internal', 'admin123')}
                >
                  <div className="login-demo-row-top">
                    <span className="login-demo-role">Admin</span>
                    <StatusPill status="critical" label="Full Control" size="small" />
                  </div>
                  <span className="login-demo-email">admin@reconcileos.internal</span>
                </button>

                <button
                  type="button"
                  className="login-demo-row"
                  onClick={() => handlePresetSelect('operator@reconcileos.internal', 'operator123')}
                >
                  <div className="login-demo-row-top">
                    <span className="login-demo-role">Operator</span>
                    <StatusPill status="warning" label="Reconcile & Plan" size="small" />
                  </div>
                  <span className="login-demo-email">operator@reconcileos.internal</span>
                </button>

                <button
                  type="button"
                  className="login-demo-row"
                  onClick={() => handlePresetSelect('viewer@reconcileos.internal', 'viewer123')}
                >
                  <div className="login-demo-row-top">
                    <span className="login-demo-role">Viewer</span>
                    <StatusPill status="healthy" label="Read Only" size="small" />
                  </div>
                  <span className="login-demo-email">viewer@reconcileos.internal</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
