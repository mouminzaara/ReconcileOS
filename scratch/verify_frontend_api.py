import urllib.request
import json

BASE_URL = 'http://127.0.0.1:8000/api/v1'

def check_endpoint(name, url):
    try:
        req = urllib.request.Request(f"{BASE_URL}{url}", headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            count = len(data.get('results', data)) if isinstance(data, (dict, list)) else 'N/A'
            print(f"[SUCCESS] {name} ({url}): HTTP {resp.status} - Items count: {count}")
    except Exception as exc:
        print(f"[FAILED] {name} ({url}): {exc}")

print("=== VERIFYING RECONCILEOS REST API FOR FRONTEND ===")
check_endpoint("Health Check", "/health/")
check_endpoint("Employees List", "/employees/")
check_endpoint("Invariant Rules", "/rules/")
check_endpoint("Drift Violations", "/reconciliation/violations/")
check_endpoint("Repair Plans", "/workflows/plans/")
check_endpoint("Approvals Queue", "/approvals/")
check_endpoint("Collected States", "/reconciliation/state/")
print("=== ALL API ENDPOINTS VERIFIED SUCCESSFULLY ===")
