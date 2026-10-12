"""Check 2 - Do admins have MFA?

For every user with an active admin role:
- is MFA registered? (authentication methods report)
- is MFA enforced? (security defaults, or an enabled CA policy that requires MFA
  for all apps and includes the user or one of their roles, without excluding them)
"""

from collections import defaultdict

from entra_data import (
    get_conditional_access_policies,
    get_mfa_registration,
    get_role_assignments,
    get_security_defaults,
)

REFERENCE = "https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/best-practices"
GUIDANCE_ENFORCE = (
    "Create a Conditional Access policy: Users > Directory roles = the admin roles (at least Global Administrator), "
    "exclude emergency access accounts; Target resources = All resources; "
    "Grant = Require multifactor authentication or an authentication strength. Or turn on security defaults."
)
GUIDANCE_REGISTER = (
    "Each admin must register an MFA method. Once MFA is required for them (see the enforcement finding), "
    "they are asked to register at their next sign-in."
)


def _requires_mfa(policy: dict) -> bool:
    grant = policy.get("grantControls") or {}
    return "mfa" in (grant.get("builtInControls") or []) or bool(grant.get("authenticationStrength"))


def _covers(policy: dict, user_id: str, role_ids: set) -> bool:
    """Does this policy apply to this user? (groups are not resolved)"""
    users = (policy.get("conditions") or {}).get("users") or {}
    if user_id in (users.get("excludeUsers") or []) or role_ids & set(users.get("excludeRoles") or []):
        return False
    return (
        "All" in (users.get("includeUsers") or [])
        or user_id in (users.get("includeUsers") or [])
        or bool(role_ids & set(users.get("includeRoles") or []))
    )


def run() -> list[dict]:
    defaults_on = bool(get_security_defaults().get("isEnabled"))
    mfa = {m["id"]: m for m in get_mfa_registration()}
    mfa_policies = [
        p for p in get_conditional_access_policies() if p["state"] == "enabled" and _requires_mfa(p)
    ]

    # All admin roles per user (only users, not apps or groups)
    admins = defaultdict(lambda: {"upn": None, "roles": [], "role_ids": set()})
    for r in get_role_assignments():
        if r["principal_type"] == "user":
            admins[r["principal_id"]]["upn"] = r["principal_upn"]
            admins[r["principal_id"]]["roles"].append(r["role"])
            admins[r["principal_id"]]["role_ids"].add(r["role_id"])

    rows = []
    for user_id, a in admins.items():
        reg = mfa.get(user_id, {})
        covering = [p for p in mfa_policies if _covers(p, user_id, a["role_ids"])]
        all_apps = [
            p["displayName"] for p in covering
            if "All" in ((p.get("conditions") or {}).get("applications") or {}).get("includeApplications", [])
        ]
        rows.append(
            {
                "upn": a["upn"],
                "roles": a["roles"],
                "mfa_registered": reg.get("isMfaRegistered"),
                "methods": reg.get("methodsRegistered"),
                "mfa_policies_covering_user": [p["displayName"] for p in covering],
                "mfa_enforced_for_all_apps": defaults_on or bool(all_apps),
            }
        )

    not_registered = [r["upn"] for r in rows if not r["mfa_registered"]]
    not_enforced = [r["upn"] for r in rows if not r["mfa_enforced_for_all_apps"]]

    return [
        {
            "check": "admin_mfa_registered",
            "title": f"{len(not_registered)} admin(s) have no MFA registered",
            "status": "FAIL" if not_registered else "PASS",
            "severity": "High",
            "evidence": {"admins_without_mfa": not_registered, "admins": rows},
            "microsoft_guidance": GUIDANCE_REGISTER,
            "reference": REFERENCE,
        },
        {
            "check": "admin_mfa_enforced",
            "title": f"MFA is not enforced for {len(not_enforced)} admin(s)",
            "status": "FAIL" if not_enforced else "PASS",
            "severity": "High",
            "evidence": {
                "security_defaults_enabled": defaults_on,
                "enabled_mfa_policies": [p["displayName"] for p in mfa_policies],
                "admins_without_enforced_mfa": not_enforced,
                "note": "Groups in Conditional Access policies are not resolved.",
            },
            "microsoft_guidance": GUIDANCE_ENFORCE,
            "reference": REFERENCE,
        },
    ]
