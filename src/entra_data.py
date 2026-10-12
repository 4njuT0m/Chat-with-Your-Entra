"""Functions that read data from Entra ID through Microsoft Graph.

Later these functions become the agent's tools (Stage 2).
"""

from graph_client import graph_get


def get_users() -> list[dict]:
    """All users with the fields we need for a security review.

    userType is "Member" for internal users and "Guest" for external users.
    """
    return graph_get(
        "/users",
        params={"$select": "id,displayName,userPrincipalName,userType,accountEnabled"},
    )


def get_role_assignments() -> list[dict]:
    """Active directory role assignments: who has which admin role.

    Returns one row per assignment. The principal can be a user, a group
    or a service principal (an app). PIM "eligible" roles are not included.
    """
    # Role definitions give us the role names (id -> "Global Administrator")
    definitions = graph_get(
        "/roleManagement/directory/roleDefinitions",
        params={"$select": "id,displayName"},
    )
    role_names = {d["id"]: d["displayName"] for d in definitions}

    # Some built-in roles are hidden from the roleDefinitions list.
    # Activated roles (/directoryRoles) also carry the name, keyed by roleTemplateId.
    for r in graph_get("/directoryRoles", params={"$select": "displayName,roleTemplateId"}):
        role_names.setdefault(r["roleTemplateId"], r["displayName"])

    # Assignments, with the principal (user/group/app) expanded
    assignments = graph_get(
        "/roleManagement/directory/roleAssignments",
        params={"$expand": "principal"},
    )

    # Last try for any role still without a name: ask for it directly by id
    for role_id in {a["roleDefinitionId"] for a in assignments} - role_names.keys():
        try:
            role_names[role_id] = graph_get(f"/roleManagement/directory/roleDefinitions/{role_id}")["displayName"]
        except RuntimeError:
            role_names[role_id] = f"Unknown role ({role_id})"

    rows = []
    for a in assignments:
        principal = a.get("principal") or {}
        rows.append(
            {
                "role": role_names[a["roleDefinitionId"]],
                "principal_name": principal.get("displayName"),
                # "#microsoft.graph.user" -> "user"
                "principal_type": (principal.get("@odata.type") or "").split(".")[-1],
                "principal_upn": principal.get("userPrincipalName"),
                "principal_id": a["principalId"],
                "role_id": a["roleDefinitionId"],
                "scope": a.get("directoryScopeId"),
            }
        )
    return rows


def get_conditional_access_policies() -> list[dict]:
    """All Conditional Access policies (enabled, disabled and report-only)."""
    return graph_get("/identity/conditionalAccess/policies")


def get_mfa_registration() -> list[dict]:
    """MFA registration status per user.

    Needs AuditLog.Read.All and an Entra ID P1 or P2 licence in the tenant.
    Disabled users are not included in this report.
    """
    return graph_get("/reports/authenticationMethods/userRegistrationDetails")


def get_security_defaults() -> dict:
    """Security defaults policy. isEnabled = true means Microsoft's baseline protections are on."""
    return graph_get("/policies/identitySecurityDefaultsEnforcementPolicy")


# Application ID of Microsoft Graph itself (the same in every tenant)
GRAPH_APP_ID = "00000003-0000-0000-c000-000000000000"


def get_graph_app_permissions() -> list[dict]:
    """Which apps (service principals) have Microsoft Graph application permissions.

    Graph's own service principal lists every app permission granted to it
    (appRoleAssignedTo). The appRoleId is translated to a name like "User.Read.All".
    """
    graph_sp = graph_get(f"/servicePrincipals(appId='{GRAPH_APP_ID}')", params={"$select": "id,appRoles"})
    permission_names = {r["id"]: r["value"] for r in graph_sp["appRoles"]}

    assignments = graph_get(f"/servicePrincipals(appId='{GRAPH_APP_ID}')/appRoleAssignedTo")
    return [
        {
            "app": a["principalDisplayName"],
            "principal_id": a["principalId"],
            "principal_type": a["principalType"],
            "permission": permission_names.get(a["appRoleId"], a["appRoleId"]),
        }
        for a in assignments
    ]
