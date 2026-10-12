"""Check 1 - Is legacy authentication blocked?

Pass: security defaults are on, OR an enabled Conditional Access policy
blocks "Exchange ActiveSync" and "Other clients" for all users.
"""

from entra_data import get_conditional_access_policies, get_security_defaults

LEGACY_CLIENTS = {"exchangeActiveSync", "other"}
REFERENCE = "https://learn.microsoft.com/en-us/entra/identity/conditional-access/policy-block-legacy-authentication"
GUIDANCE = (
    "Create a Conditional Access policy: Users = All users, exclude emergency access accounts; "
    "Target resources = All resources; Conditions > Client apps = Exchange ActiveSync clients and Other clients; "
    "Grant = Block access. Start in Report-only, review the impact, then turn it On. "
    "Tenants without Conditional Access licences can turn on security defaults instead."
)


def _blocks_legacy_for_all(policy: dict) -> bool:
    conditions = policy.get("conditions") or {}
    users = conditions.get("users") or {}
    client_apps = set(conditions.get("clientAppTypes") or [])
    grant = (policy.get("grantControls") or {}).get("builtInControls") or []
    return (
        LEGACY_CLIENTS.issubset(client_apps)
        and "block" in grant
        and "All" in (users.get("includeUsers") or [])
    )


def run() -> list[dict]:
    defaults_on = bool(get_security_defaults().get("isEnabled"))
    policies = get_conditional_access_policies()

    blocking = [p for p in policies if _blocks_legacy_for_all(p)]
    enabled_blocking = [p["displayName"] for p in blocking if p["state"] == "enabled"]
    report_only = [p["displayName"] for p in blocking if p["state"] == "enabledForReportingButNotEnforced"]

    passed = defaults_on or bool(enabled_blocking)
    return [
        {
            "check": "legacy_auth",
            "title": "Legacy authentication is not blocked" if not passed else "Legacy authentication is blocked",
            "status": "PASS" if passed else "FAIL",
            "severity": "High",
            "evidence": {
                "security_defaults_enabled": defaults_on,
                "enabled_policies_blocking_legacy_auth": enabled_blocking,
                "report_only_policies_blocking_legacy_auth": report_only,
                "all_policies": [
                    {
                        "name": p["displayName"],
                        "state": p["state"],
                        "client_app_types": (p.get("conditions") or {}).get("clientAppTypes"),
                    }
                    for p in policies
                ],
            },
            "microsoft_guidance": GUIDANCE,
            "reference": REFERENCE,
        }
    ]
