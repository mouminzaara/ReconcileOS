import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import {
  Shield,
  UserCheck,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  ShieldCheck,
  Zap,
  Lock,
  Server,
  Activity,
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
      {/* Decorative Left Panel */}
      <div className="login-left-panel">
        <div className="login-left-content">
          {/* Back to landing */}
          <Link to="/landing" className="login-back-link">
            <ArrowLeft size={16} />
            <span>Back to ReconcileOS</span>
          </Link>

          {/* Brand Block */}
          <div className="login-brand-block">
            <div className="login-brand-icon">
              <Shield size={28} />
            </div>
            <h1 className="login-brand-title">ReconcileOS</h1>
            <p className="login-brand-tagline">
              Continuous Integrity &amp; Self-Healing Identity Platform
            </p>
          </div>

          {/* Feature Pills */}
          <div className="login-feature-list">
            <div className="login-feature-pill">
              <div className="login-feature-pill-icon">
                <Zap size={16} />
              </div>
              <div>
                <div className="login-feature-pill-title">Automated Drift Detection</div>
                <div className="login-feature-pill-desc">Real-time cross-system reconciliation</div>
              </div>
            </div>

            <div className="login-feature-pill">
              <div className="login-feature-pill-icon">
                <ShieldCheck size={16} />
              </div>
              <div>
                <div className="login-feature-pill-title">Human-in-the-Loop Approvals</div>
                <div className="login-feature-pill-desc">SecOps gated repair execution</div>
              </div>
            </div>

            <div className="login-feature-pill">
              <div className="login-feature-pill-icon">
                <FileText size={16} />
              </div>
              <div>
                <div className="login-feature-pill-title">Tamper-Evident Audit Trail</div>
                <div className="login-feature-pill-desc">SHA-256 cryptographic hash chain</div>
              </div>
            </div>
          </div>

          {/* Floating Decorative Orbs */}
          <div className="login-orb login-orb-1" />
          <div className="login-orb login-orb-2" />
          <div className="login-orb login-orb-3" />
        </div>

        {/* Bottom Trust Bar */}
        <div className="login-trust-bar">
          <div className="login-trust-item">
            <Server size={14} />
            <span>5 Connected Systems</span>
          </div>
          <div className="login-trust-divider" />
          <div className="login-trust-item">
            <Activity size={14} />
            <span>Daemon Active</span>
          </div>
          <div className="login-trust-divider" />
          <div className="login-trust-item">
            <Lock size={14} />
            <span>Zero-Trust Enforcement</span>
          </div>
        </div>
      </div>

      {/* Right Form Panel */}
      <div className="login-right-panel">
        <div className="login-form-wrapper">
          {/* Form Header */}
          <div className="login-form-header">
            <div className="login-form-icon">
              <Lock size={22} />
            </div>
            <h2 className="login-form-title">Security Access Portal</h2>
            <p className="login-form-subtitle">
              Authenticate with your corporate identity to access the Integrity Control Center
            </p>
          </div>

          {/* Error Alert */}
          {error && (
            <div className="login-error-alert">
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="login-form">
            <div className="login-field">
              <label className="login-label" htmlFor="login-email">
                Corporate Identity / Email
              </label>
              <div className="login-input-wrapper">
                <UserCheck size={16} className="login-input-icon" />
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
                <Lock size={16} className="login-input-icon" />
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
              <span>{loading ? 'Authenticating...' : 'Sign In with SimpleJWT'}</span>
              {!loading && <ArrowRight size={18} />}
            </button>
          </form>

          {/* Divider */}
          <div className="login-divider">
            <span>Quick-Fill Role Presets</span>
          </div>

          {/* Quick-Fill Demo Presets */}
          <div className="login-presets">
            <button
              type="button"
              className="preset-btn"
              onClick={() => handlePresetSelect('admin@reconcileos.internal', 'admin123')}
            >
              <span className="preset-btn-info">
                <strong>ADMIN:</strong>
                <span>admin@reconcileos.internal</span>
              </span>
              <StatusPill status="critical" label="Full Control" size="small" />
            </button>

            <button
              type="button"
              className="preset-btn"
              onClick={() => handlePresetSelect('operator@reconcileos.internal', 'operator123')}
            >
              <span className="preset-btn-info">
                <strong>OPERATOR:</strong>
                <span>operator@reconcileos.internal</span>
              </span>
              <StatusPill status="warning" label="Reconcile & Plan" size="small" />
            </button>

            <button
              type="button"
              className="preset-btn"
              onClick={() => handlePresetSelect('viewer@reconcileos.internal', 'viewer123')}
            >
              <span className="preset-btn-info">
                <strong>VIEWER:</strong>
                <span>viewer@reconcileos.internal</span>
              </span>
              <StatusPill status="healthy" label="Read Only" size="small" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
