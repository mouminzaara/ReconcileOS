/**
 * ReconcileOS Unified API Service Layer with SimpleJWT Bearer Authentication.
 * Communicates directly with Django REST Framework endpoints.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

export function getStoredToken() {
  return localStorage.getItem('reconcileos_access_token');
}

export function setStoredTokens(access, refresh) {
  if (access) localStorage.setItem('reconcileos_access_token', access);
  if (refresh) localStorage.setItem('reconcileos_refresh_token', refresh);
}

export function clearStoredTokens() {
  localStorage.removeItem('reconcileos_access_token');
  localStorage.removeItem('reconcileos_refresh_token');
  localStorage.removeItem('reconcileos_user');
}

async function fetchJson(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = getStoredToken();

  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401 && !endpoint.includes('/auth/login/')) {
      clearStoredTokens();
      window.dispatchEvent(new Event('auth:unauthorized'));
    }

    if (!response.ok) {
      const errorText = await response.text();
      let errorData;
      try {
        errorData = JSON.parse(errorText);
      } catch {
        errorData = { detail: errorText };
      }
      throw new Error(errorData.detail || errorData.message || `API Error HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Request failed for ${endpoint}:`, error);
    throw error;
  }
}

export const api = {
  // Authentication & SimpleJWT Endpoints
  login: async (username, password) => {
    const data = await fetchJson('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    setStoredTokens(data.access, data.refresh);
    if (data.user) {
      localStorage.setItem('reconcileos_user', JSON.stringify(data.user));
    }
    return data;
  },

  getMe: () => fetchJson('/auth/me/'),

  logout: () => {
    clearStoredTokens();
  },

  // System Health
  getHealth: () => fetchJson('/health/'),

  // Employees API
  getEmployees: () => fetchJson('/employees/'),
  getEmployeeDetail: (id) => fetchJson(`/employees/${id}/`),

  // Connected Systems & Multi-System State
  getCollectedStates: () => fetchJson('/reconciliation/state/'),
  getEmployeeState: (id) => fetchJson(`/reconciliation/state/${id}/`),

  // Invariant Rules
  getRules: () => fetchJson('/rules/'),

  // Reconciliation & Drift Violations
  getViolations: (params = '') => fetchJson(`/reconciliation/violations/${params}`),
  runReconciliation: (employeeId = null) =>
    fetchJson('/reconciliation/run/', {
      method: 'POST',
      body: JSON.stringify(employeeId ? { employee_id: employeeId } : {}),
    }),
  runContinuousMonitor: (autoApprove = false, employeeId = null) =>
    fetchJson('/reconciliation/monitor/', {
      method: 'POST',
      body: JSON.stringify({ auto_approve: autoApprove, employee_id: employeeId }),
    }),

  // Repair Plans & Execution Engine
  getRepairPlans: () => fetchJson('/workflows/plans/'),
  generateRepairPlans: (emailOrId = null) =>
    fetchJson('/workflows/plans/generate/', {
      method: 'POST',
      body: JSON.stringify(emailOrId ? { email: emailOrId } : {}),
    }),
  executeRepairPlan: (planId) =>
    fetchJson(`/workflows/plans/${planId}/execute/`, {
      method: 'POST',
    }),
  verifyRepairPlan: (planId) =>
    fetchJson(`/workflows/plans/${planId}/verify/`, {
      method: 'POST',
    }),

  // Human Approvals Engine
  getApprovals: () => fetchJson('/approvals/'),
  getPendingApprovals: () => fetchJson('/approvals/pending/'),
  approveRepair: (approvalId, comment = 'Approved by Security Admin') =>
    fetchJson(`/approvals/${approvalId}/approve/`, {
      method: 'POST',
      body: JSON.stringify({ comment }),
    }),
  rejectRepair: (approvalId, comment = 'Rejected by Security Admin') =>
    fetchJson(`/approvals/${approvalId}/reject/`, {
      method: 'POST',
      body: JSON.stringify({ comment }),
    }),
};
