"""Stage 2 - Tools the agent can use.

Each tool has two parts:
- a JSON description in TOOLS (this is what the model sees)
- a Python function in TOOL_FUNCTIONS (this is what the script runs)

The model only asks for a tool. run_tool() runs it and returns the result as JSON text.
"""

import json
from functools import lru_cache

from entra_data import (
    get_conditional_access_policies,
    get_mfa_registration,
    get_role_assignments,
    get_users,
)
from graph_client import graph_get


@lru_cache
def _all_users() -> list[dict]:
    """Users are read once per session and reused."""
    return get_users()


@lru_cache
def _role_names() -> dict:
    """Role id -> role name, used to show role names in CA policies."""
    definitions = graph_get(
        "/roleManagement/directory/roleDefinitions",
        params={"$select": "id,displayName"},
    )
    return {d["id"]: d["displayName"] for d in definitions}


# ---------- Python functions (what the script runs) ----------

def list_users(user_type: str = "all") -> list[dict]:
    users = _all_users()
    if user_type in ("Member", "Guest"):
        users = [u for u in users if u.get("userType") == user_type]
    return [
        {
            "name": u["displayName"],
            "upn": u["userPrincipalName"],
            "type": u["userType"],
            "enabled": u["accountEnabled"],
        }
        for u in users
    ]


def list_role_assignments(role_name: str = "") -> list[dict]:
    rows = get_role_assignments()
    if role_name:
        rows = [r for r in rows if role_name.lower() in r["role"].lower()]
    return [
        {
            "role": r["role"],
            "principal_name": r["principal_name"],
            "principal_type": r["principal_type"],
            "principal_upn": r["principal_upn"],
        }
        for r in rows
    ]


def list_conditional_access_policies() -> list[dict]:
    upns = {u["id"]: u["userPrincipalName"] for u in _all_users()}
    roles = _role_names()

    result = []
    for p in get_conditional_access_policies():
        conditions = p.get("conditions") or {}
        users = conditions.get("users") or {}
        grant = p.get("grantControls") or {}
        result.append(
            {
                "name": p["displayName"],
                "state": p["state"],
                "include_users": [upns.get(x, x) for x in users.get("includeUsers") or []],
                "exclude_users": [upns.get(x, x) for x in users.get("excludeUsers") or []],
                "include_roles": [roles.get(x, x) for x in users.get("includeRoles") or []],
                "exclude_roles": [roles.get(x, x) for x in users.get("excludeRoles") or []],
                "include_groups": users.get("includeGroups") or [],
                "apps": (conditions.get("applications") or {}).get("includeApplications") or [],
                "client_app_types": conditions.get("clientAppTypes") or [],
                "locations": conditions.get("locations"),
                "grant_controls": grant.get("builtInControls") or [],
                "authentication_strength": (grant.get("authenticationStrength") or {}).get("displayName"),
            }
        )
    return result


def get_mfa_status(only_without_mfa: bool = False, only_admins: bool = False) -> list[dict]:
    rows = get_mfa_registration()
    if only_without_mfa:
        rows = [r for r in rows if not r.get("isMfaRegistered")]
    if only_admins:
        rows = [r for r in rows if r.get("isAdmin")]
    return [
        {
            "upn": r["userPrincipalName"],
            "is_admin": r.get("isAdmin"),
            "mfa_registered": r.get("isMfaRegistered"),
            "methods": r.get("methodsRegistered"),
        }
        for r in rows
    ]


TOOL_FUNCTIONS = {
    "list_users": list_users,
    "list_role_assignments": list_role_assignments,
    "list_conditional_access_policies": list_conditional_access_policies,
    "get_mfa_status": get_mfa_status,
}


# ---------- Tool descriptions (what the model sees) ----------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_users",
            "description": "List users in the Entra tenant with UPN, user type (Member or Guest) and enabled status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_type": {
                        "type": "string",
                        "enum": ["all", "Member", "Guest"],
                        "description": "Filter by user type. Default: all.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_role_assignments",
            "description": (
                "List active admin role assignments (who has which directory role, e.g. Global Administrator). "
                "Principals can be users, groups or service principals (apps). PIM eligible roles are not included."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "role_name": {
                        "type": "string",
                        "description": "Optional part of a role name to filter on, e.g. 'Global Administrator'. Empty = all roles.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_conditional_access_policies",
            "description": (
                "List all Conditional Access policies with state, included/excluded users and roles, "
                "apps, client app types, locations, grant controls and authentication strength."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_mfa_status",
            "description": (
                "MFA registration status per user from the authentication methods report. "
                "Shows if the user is an admin and which methods are registered. Disabled users are not included."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "only_without_mfa": {
                        "type": "boolean",
                        "description": "true = only users without a registered MFA method.",
                    },
                    "only_admins": {
                        "type": "boolean",
                        "description": "true = only users with an admin role.",
                    },
                },
            },
        },
    },
]


def run_tool(name: str, arguments_json: str) -> str:
    """Run a tool by name. Errors go back to the model as JSON so it can explain them."""
    try:
        args = json.loads(arguments_json or "{}")
        result = TOOL_FUNCTIONS[name](**args)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {e}"})


if __name__ == "__main__":
    # Quick test without the AI: run every tool once and show how many rows it returns
    for tool_name in TOOL_FUNCTIONS:
        output = json.loads(run_tool(tool_name, "{}"))
        size = len(output) if isinstance(output, list) else output
        print(f"{tool_name:<35} -> {size} rows")
