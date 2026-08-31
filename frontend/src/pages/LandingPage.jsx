import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Shield,
  ArrowRight,
  ShieldCheck,
  Zap,
  Lock,
  FileText,
  Users
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { mockStats } from '../data/mockData';
import { IntegrityDriftCard } from '../components/common/IntegrityDriftCard';
import '../styles/landing.css';

export function LandingPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const handleSignInClick = () => {
    if (user) {
      navigate('/dashboard');
    } else {
      navigate('/login');
    }
  };

  return (
    <div className="landing-container">
      {/* Top Navigation */}
      <nav className="landing-nav">
        <Link to="/" className="landing-brand">
          <div className="landing-brand-icon">
            <Shield size={22} />
          </div>
          <span>ReconcileOS</span>
        </Link>

        <ul className="landing-nav-links">
          <li>
            <a href="#product" className="landing-nav-link">Product</a>
          </li>
          <li>
            <a href="#how-it-works" className="landing-nav-link">How it works</a>
          </li>
          <li>
            <a href="#docs" className="landing-nav-link">Docs</a>
          </li>
          <li>
            <a href="#contact" className="landing-nav-link">Contact</a>
          </li>
        </ul>

        <button onClick={handleSignInClick} className="landing-cta-btn">
          {user ? 'Go to Dashboard' : 'Sign in'} <ArrowRight size={16} />
        </button>
      </nav>

      {/* Hero Section */}
      <section className="landing-hero">
        {/* Eyebrow Badge */}
        <div className="eyebrow-badge">
          <span className="eyebrow-dot" />
          <span>Continuous integrity, not one-time automation</span>
        </div>

        {/* Headline */}
        <h1 className="landing-headline">
          Access that stays revoked.<br />
          Automatically.
        </h1>

        {/* Subtitle */}
        <p className="landing-subtitle">
          ReconcileOS continuously watches every connected system, catches access that should have been removed, and repairs it — even if someone undoes the fix three days later.
        </p>

        {/* Hero Actions */}
        <div className="landing-hero-actions">
          <button onClick={handleSignInClick} className="landing-cta-btn" style={{ padding: '12px 28px', fontSize: '0.95rem' }}>
            {user ? 'Enter Control Center' : 'Sign in to Dashboard'} <ArrowRight size={18} />
          </button>
          <a href="#how-it-works" className="landing-secondary-btn">
            Explore Architecture
          </a>
        </div>

        {/* Hero Visual Dashboard Preview Frame */}
        <div className="hero-visual-frame" id="product">
          <div className="browser-header">
            <div className="browser-dot red" />
            <div className="browser-dot yellow" />
            <div className="browser-dot green" />
            <div className="browser-address-bar">
              <Lock size={12} style={{ color: '#7865A5' }} /> https://app.reconcileos.internal/dashboard
            </div>
          </div>

          <div className="dashboard-preview-content">
            {/* Dashboard Stats Row */}
            <div className="grid-4" style={{ marginBottom: '20px' }}>
              <div className="card stat-card" style={{ padding: '14px' }}>
                <div className="stat-header">
                  <span className="stat-title">Tracked Identities</span>
                  <div className="stat-icon-wrapper"><Users size={16} /></div>
                </div>
                <div className="stat-value">{mockStats.totalEmployees}</div>
                <div className="stat-subtext">Active HR Records</div>
              </div>

              <div className="card stat-card danger" style={{ padding: '14px' }}>
                <div className="stat-header">
                  <span className="stat-title">Active Violations</span>
                  <div className="stat-icon-wrapper" style={{ color: 'var(--status-danger)' }}><Shield size={16} /></div>
                </div>
                <div className="stat-value" style={{ color: 'var(--status-danger)' }}>{mockStats.activeViolations}</div>
                <div className="stat-subtext">Drift detected across VPN & GitHub</div>
              </div>

              <div className="card stat-card warning" style={{ padding: '14px' }}>
                <div className="stat-header">
                  <span className="stat-title">Pending Approvals</span>
                  <div className="stat-icon-wrapper" style={{ color: 'var(--status-warning)' }}><Zap size={16} /></div>
                </div>
                <div className="stat-value" style={{ color: 'var(--status-warning)' }}>{mockStats.pendingRepairs}</div>
                <div className="stat-subtext">SecOps Human Review Required</div>
              </div>

              <div className="card stat-card success" style={{ padding: '14px' }}>
                <div className="stat-header">
                  <span className="stat-title">System Health</span>
                  <div className="stat-icon-wrapper" style={{ color: 'var(--status-success)' }}><ShieldCheck size={16} /></div>
                </div>
                <div className="stat-value" style={{ color: 'var(--status-success)' }}>{mockStats.systemHealthPercent}%</div>
                <div className="stat-subtext">Continuous Integrity Enforced</div>
              </div>
            </div>

            {/* Active Integrity Drift Showcase Card */}
            <IntegrityDriftCard
              onRunAudit={() => {}}
              onRunMonitor={() => {}}
              actionLoading={false}
            />

            <div className="dashboard-preview-overlay">
              <button onClick={handleSignInClick} className="landing-cta-btn">
                Launch Live Dashboard <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </div>

        {/* Feature Highlights Section */}
        <div className="landing-features" id="how-it-works">
          <div className="feature-card">
            <div className="feature-icon-box">
              <Zap size={22} />
            </div>
            <h3 className="feature-title">Automated Drift Engine</h3>
            <p className="feature-desc">
              Continuously compares source-of-truth HR status against downstream target systems (VPN, GitHub, Cloud IAM, Slack) to detect authorization drift instantly.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon-box">
              <ShieldCheck size={22} />
            </div>
            <h3 className="feature-title">Human-in-the-Loop Approvals</h3>
            <p className="feature-desc">
              Sensitive remediation actions generate deterministic repair plans requiring explicit SecOps authorization before executing any system mutations.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon-box">
              <FileText size={22} />
            </div>
            <h3 className="feature-title">Tamper-Evident Audit Streams</h3>
            <p className="feature-desc">
              Every evaluation, violation detection, and repair execution creates an immutable SHA-256 cryptographically chained record for compliance.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <p>© 2026 ReconcileOS Platform Inc. Continuous Authorization & Self-Healing Identity Integrity.</p>
      </footer>
    </div>
  );
}
