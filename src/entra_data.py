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

    # Assignments, with the principal (user/group/app) expanded
    assignments = graph_get(
        "/roleManagement/directory/roleAssignments",
        params={"$expand": "principal"},
    )

    rows = []
    for a in assignments:
        principal = a.get("principal") or {}
        rows.append(
            {
                "role": role_names.get(a["roleDefinitionId"], a["roleDefinitionId"]),
                "principal_name": principal.get("displayName"),
                # "#microsoft.graph.user" -> "user"
                "principal_type": (principal.get("@odata.type") or "").split(".")[-1],
                "principal_upn": principal.get("userPrincipalName"),
                "principal_id": a["principalId"],
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
