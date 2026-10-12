"""Check 3 - Are service principals (apps) over-privileged?

Looks at two things:
- Microsoft Graph application permissions that allow privilege escalation
- Apps that hold directory admin roles (for example Global Administrator)
"""

from entra_data import get_graph_app_permissions, get_role_assignments

REFERENCE = "https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/best-practices"
GUIDANCE = (
    "Apply least privilege. Review each app with its owner first: Microsoft or lab-provisioned apps may need "
    "these permissions, and removing them can break the service. Remove what is not needed: "
    "app permissions under Enterprise applications > the app > Permissions, "
    "admin roles under Roles & admins > the role > Assignments."
)

HIGH_RISK_PERMISSIONS = {
    "RoleManagement.ReadWrite.Directory": "High",   # can assign admin roles, incl. Global Admin
    "AppRoleAssignment.ReadWrite.All": "High",      # can grant itself any app permission
    "Application.ReadWrite.All": "High",            # can add credentials to other apps
    "Directory.ReadWrite.All": "Medium",
    "User.ReadWrite.All": "Medium",
    "Group.ReadWrite.All": "Medium",
    "Policy.ReadWrite.ConditionalAccess": "Medium",
}


def run() -> list[dict]:
    findings = []

    risky = [
        {**p, "risk": HIGH_RISK_PERMISSIONS[p["permission"]]}
        for p in get_graph_app_permissions()
        if p["permission"] in HIGH_RISK_PERMISSIONS
    ]
    findings.append(
        {
            "check": "sp_graph_permissions",
            "title": f"{len(risky)} high-risk Microsoft Graph app permission(s) granted to apps",
            "status": "FAIL" if risky else "PASS",
            "severity": "High" if any(r["risk"] == "High" for r in risky) else "Medium",
            "evidence": {"risky_permissions": risky, "permissions_checked": HIGH_RISK_PERMISSIONS},
            "microsoft_guidance": GUIDANCE,
            "reference": REFERENCE,
        }
    )

    app_roles = [
        {"app": r["principal_name"], "role": r["role"]}
        for r in get_role_assignments()
        if r["principal_type"] == "servicePrincipal"
    ]
    global_admin_apps = [a for a in app_roles if a["role"] == "Global Administrator"]
    findings.append(
        {
            "check": "sp_admin_roles",
            "title": f"{len(app_roles)} admin role assignment(s) held by apps, {len(global_admin_apps)} of them Global Administrator",
            "status": "FAIL" if global_admin_apps else ("WARN" if app_roles else "PASS"),
            "severity": "High" if global_admin_apps else "Medium",
            "evidence": {"apps_with_admin_roles": app_roles},
            "microsoft_guidance": GUIDANCE,
            "reference": REFERENCE,
        }
    )
    return findings
