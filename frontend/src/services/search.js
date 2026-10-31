import { api } from './api';

// 30-second TTL in-memory cache to prevent redundant duplicate network requests
let searchCache = {
  timestamp: 0,
  data: {
    employees: [],
    violations: [],
    repairs: [],
    auditLogs: [],
  }
};

/**
 * Invalidate the search cache (e.g. after mutations).
 */
export function invalidateSearchCache() {
  searchCache.timestamp = 0;
}

/**
 * Fetch accessible records across core domains using existing authenticated endpoints.
 * Uses Promise.allSettled so any unauthorized or failing endpoint is safely omitted.
 */
export async function getSearchDataset(force = false) {
  const now = Date.now();
  if (!force && searchCache.timestamp && (now - searchCache.timestamp < 30000)) {
    return searchCache.data;
  }

  const [empRes, vioRes, repRes, audRes] = await Promise.allSettled([
    api.getEmployees(),
    api.getViolations(),
    api.getRepairPlans(),
    api.getAuditLogs(),
  ]);

  const employees = empRes.status === 'fulfilled' ? (empRes.value?.results || empRes.value || []) : [];
  const violations = vioRes.status === 'fulfilled' ? (vioRes.value?.results || vioRes.value || []) : [];
  const repairs = repRes.status === 'fulfilled' ? (repRes.value?.results || repRes.value || []) : [];
  const auditLogs = audRes.status === 'fulfilled' ? (audRes.value?.results || audRes.value || []) : [];

  searchCache = {
    timestamp: now,
    data: {
      employees: Array.isArray(employees) ? employees : [],
      violations: Array.isArray(violations) ? violations : [],
      repairs: Array.isArray(repairs) ? repairs : [],
      auditLogs: Array.isArray(auditLogs) ? auditLogs : [],
    }
  };

  return searchCache.data;
}

/**
 * Perform client-side search across all loaded domain records.
 * Returns grouped results: { employees: [], violations: [], repairs: [], auditLogs: [], totalCount: number }
 */
export function executeSearch(dataset, rawQuery) {
  const query = (rawQuery || '').trim().toLowerCase();
  if (!query) {
    return { employees: [], violations: [], repairs: [], auditLogs: [], totalCount: 0 };
  }

  // 1. Match Employees (name, email, department, ID)
  const matchingEmployees = (dataset?.employees || [])
    .filter(emp => {
      const name = (emp.full_name || '').toLowerCase();
      const email = (emp.email || '').toLowerCase();
      const dept = (emp.department || '').toLowerCase();
      const id = String(emp.id || '').toLowerCase();
      return name.includes(query) || email.includes(query) || dept.includes(query) || id.includes(query);
    })
    .map(emp => ({
      id: `emp-${emp.id}`,
      rawId: emp.id,
      category: 'Employees',
      title: emp.full_name || 'Unknown Employee',
      subtitle: `${emp.email || 'No email'}${emp.department ? ` • ${emp.department}` : ''}`,
      status: emp.status || 'ACTIVE',
      statusVariant: emp.status === 'ACTIVE' ? 'healthy' : 'neutral',
      url: `/employees?search=${encodeURIComponent(emp.email || emp.full_name || '')}`,
    }));

  // 2. Match Violations (ID, rule code, rule name, employee name/email, affected system)
  const matchingViolations = (dataset?.violations || [])
    .filter(v => {
      const idStr = String(v.id || '').toLowerCase();
      const formattedId = v.id ? `vio-${v.id.substring(0, 8).toLowerCase()}` : '';
      const ruleCode = (v.rule_code || (v.rule && v.rule.rule_code) || '').toLowerCase();
      const ruleName = (v.rule_name || (v.rule && v.rule.name) || '').toLowerCase();
      const empName = (v.employee_name || (v.employee && v.employee.full_name) || '').toLowerCase();
      const empEmail = (v.employee_email || (v.employee && v.employee.email) || '').toLowerCase();
      const sys = (v.affected_system || '').toLowerCase();
      return (
        formattedId.includes(query) ||
        idStr.includes(query) ||
        ruleCode.includes(query) ||
        ruleName.includes(query) ||
        empName.includes(query) ||
        empEmail.includes(query) ||
        sys.includes(query)
      );
    })
    .map(v => {
      const formattedId = v.id ? `VIO-${v.id.substring(0, 8).toUpperCase()}` : (v.rule_code || 'VIO');
      const ruleDisplay = v.rule_name || v.rule_code || 'Invariant Violation';
      const emp = v.employee_name || (v.employee && v.employee.full_name) || 'Unknown';
      const sys = v.affected_system || 'Target';
      const actual = v.actual_state ? `: ${v.actual_state}` : '';
      const sev = (v.severity || 'CRITICAL').toUpperCase();
      return {
        id: `vio-${v.id || formattedId}`,
        rawId: v.id,
        category: 'Violations',
        title: `${formattedId}: ${ruleDisplay}`,
        subtitle: `${emp} (${sys}${actual})`,
        status: sev,
        statusVariant: sev === 'CRITICAL' ? 'critical' : sev === 'HIGH' ? 'warning' : 'neutral',
        url: `/violations?search=${encodeURIComponent(formattedId)}`,
      };
    });

  // 3. Match Repair Plans (ID, action, employee name/email, target system, reason)
  const matchingRepairs = (dataset?.repairs || [])
    .filter(p => {
      const idStr = String(p.id || '').toLowerCase();
      const formattedId = p.id ? `rep-${p.id.substring(0, 8).toLowerCase()}` : '';
      const action = (p.action || '').toLowerCase();
      const sys = (p.target_system || '').toLowerCase();
      const empName = (p.employee_name || (p.employee && p.employee.full_name) || '').toLowerCase();
      const empEmail = (p.employee_email || (p.employee && p.employee.email) || '').toLowerCase();
      const reason = (p.reason || '').toLowerCase();
      return (
        formattedId.includes(query) ||
        idStr.includes(query) ||
        action.includes(query) ||
        sys.includes(query) ||
        empName.includes(query) ||
        empEmail.includes(query) ||
        reason.includes(query)
      );
    })
    .map(p => {
      const formattedId = p.id ? `REP-${p.id.substring(0, 8).toUpperCase()}` : 'REP';
      const emp = p.employee_name || (p.employee && p.employee.full_name) || 'Unknown';
      const sys = p.target_system || 'Target';
      const st = (p.status || 'PENDING').toUpperCase();
      let statusVariant = 'neutral';
      if (st === 'SUCCESS' || st === 'COMPLETED' || st === 'APPROVED') statusVariant = 'healthy';
      else if (st === 'PENDING' || st === 'EXECUTING' || st === 'RETRYING') statusVariant = 'warning';
      else if (st === 'FAILED' || st === 'REJECTED') statusVariant = 'critical';

      return {
        id: `rep-${p.id || formattedId}`,
        rawId: p.id,
        category: 'Repair Plans',
        title: `${formattedId}: ${p.action || 'Remediation Plan'}`,
        subtitle: `${emp} • ${sys}`,
        status: st,
        statusVariant,
        url: `/repairs?search=${encodeURIComponent(formattedId)}`,
      };
    });

  // 4. Match Audit Events (ID, event_type, actor, system, target, action)
  const matchingAuditLogs = (dataset?.auditLogs || [])
    .filter(log => {
      const idStr = String(log.id || '').toLowerCase();
      const formattedId = log.id ? `aud-${String(log.id).substring(0, 8).toLowerCase()}` : '';
      const corr = (log.correlation_id || '').toLowerCase();
      const eventType = (log.event_type || '').toLowerCase();
      const actor = (log.actor || '').toLowerCase();
      const sys = (log.system || '').toLowerCase();
      const target = (log.target || log.employee_name || log.employee_email || log.action || '').toLowerCase();
      return (
        formattedId.includes(query) ||
        corr.includes(query) ||
        idStr.includes(query) ||
        eventType.includes(query) ||
        actor.includes(query) ||
        sys.includes(query) ||
        target.includes(query)
      );
    })
    .map(log => {
      const formattedId = log.id ? `AUD-${String(log.id).substring(0, 8).toUpperCase()}` : (log.correlation_id || 'AUD');
      const eventType = log.event_type || 'SYSTEM_EVENT';
      const actor = log.actor || 'SYSTEM';
      const sys = log.system || 'Core';
      const target = log.employee_name || log.employee_email || log.action || log.target || '';
      const outcome = (log.result || 'SUCCESS').toUpperCase();
      const statusVariant = (outcome === 'CRITICAL' || outcome === 'FAILURE') ? 'critical' : (outcome === 'SUCCESS' ? 'healthy' : 'warning');

      return {
        id: `aud-${log.id || formattedId}`,
        rawId: log.id,
        category: 'Audit Events',
        title: `${eventType}`,
        subtitle: `${actor} → ${sys}${target ? ` • ${target}` : ''}`,
        status: outcome,
        statusVariant,
        url: `/audit-logs?search=${encodeURIComponent(formattedId)}`,
      };
    });

  const totalCount =
    matchingEmployees.length +
    matchingViolations.length +
    matchingRepairs.length +
    matchingAuditLogs.length;

  return {
    employees: matchingEmployees.slice(0, 4),
    violations: matchingViolations.slice(0, 4),
    repairs: matchingRepairs.slice(0, 4),
    auditLogs: matchingAuditLogs.slice(0, 4),
    totalCount,
    rawCounts: {
      employees: matchingEmployees.length,
      violations: matchingViolations.length,
      repairs: matchingRepairs.length,
      auditLogs: matchingAuditLogs.length,
    }
  };
}
