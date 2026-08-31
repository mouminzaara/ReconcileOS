import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Shield,
  LayoutDashboard,
  Users,
  Server,
  BookOpen,
  AlertTriangle,
  Wrench,
  CheckCircle2,
  FileText,
  Settings,
  Activity
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/employees', label: 'Employees', icon: Users },
  { path: '/systems', label: 'Connected Systems', icon: Server },
  { path: '/rules', label: 'Rules', icon: BookOpen },
  { path: '/violations', label: 'Violations', icon: AlertTriangle },
  { path: '/repairs', label: 'Repairs', icon: Wrench },
  { path: '/approvals', label: 'Approvals', icon: CheckCircle2 },
  { path: '/audit-logs', label: 'Audit Logs', icon: FileText },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand-icon-wrapper">
          <Shield size={22} />
        </div>
        <div className="brand-info">
          <span className="brand-title">ReconcileOS</span>
          <span className="brand-subtitle">Integrity Platform</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `nav-item ${isActive ? 'active' : ''}`
              }
              end={item.path === '/'}
            >
              <Icon className="nav-item-icon" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="system-status-box">
          <div className="status-label-group">
            <span className="pulse-dot healthy"></span>
            <div>
              <div className="status-text">Daemon Active</div>
              <div className="status-sub">Scan: Every 5 mins</div>
            </div>
          </div>
          <Activity size={16} style={{ color: 'var(--status-success)' }} />
        </div>
      </div>
    </aside>
  );
}
