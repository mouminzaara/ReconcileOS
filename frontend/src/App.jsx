import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { AppLayout } from './components/layout/AppLayout';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { EmployeesPage } from './pages/EmployeesPage';
import { ConnectedSystemsPage } from './pages/ConnectedSystemsPage';
import { RulesPage } from './pages/RulesPage';
import { ViolationsPage } from './pages/ViolationsPage';
import { RepairsPage } from './pages/RepairsPage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { AuditLogsPage } from './pages/AuditLogsPage';
import { SettingsPage } from './pages/SettingsPage';
import { StyleGuidePage } from './pages/StyleGuidePage';
import './styles/layout.css';
import './styles/components.css';
import './styles/login.css';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Landing & Login Routes */}
          <Route path="/landing" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />

          {/* Protected Application Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="style-guide" element={<StyleGuidePage />} />
            <Route path="employees" element={<EmployeesPage />} />
            <Route path="systems" element={<ConnectedSystemsPage />} />
            <Route path="rules" element={<RulesPage />} />
            <Route path="violations" element={<ViolationsPage />} />
            <Route path="repairs" element={<RepairsPage />} />
            <Route
              path="approvals"
              element={
                <ProtectedRoute allowedRoles={['ADMIN', 'OPERATOR']}>
                  <ApprovalsPage />
                </ProtectedRoute>
              }
            />
            <Route path="audit-logs" element={<AuditLogsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
