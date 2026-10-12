"""Check 4 - Fewer than 5 Global Administrators (Microsoft best practice)."""

from entra_data import get_role_assignments

REFERENCE = "https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/best-practices"
LIMIT = 5
GUIDANCE = (
    "Assign Global Administrator to fewer than five people. Keep two cloud-only emergency access accounts. "
    "Move other admins to the least-privileged role they need, and use PIM for just-in-time access."
)


def run() -> list[dict]:
    gas = [r for r in get_role_assignments() if r["role"] == "Global Administrator"]
    users = [r["principal_upn"] for r in gas if r["principal_type"] == "user"]
    apps = [r["principal_name"] for r in gas if r["principal_type"] == "servicePrincipal"]
    return [
        {
            "check": "global_admin_count",
            "title": f"{len(gas)} Global Administrator assignments (recommended: fewer than {LIMIT})",
            "status": "FAIL" if len(gas) >= LIMIT else "PASS",
            "severity": "Medium",
            "evidence": {"total": len(gas), "users": users, "apps": apps},
            "microsoft_guidance": GUIDANCE,
            "reference": REFERENCE,
        }
    ]
