"""Stage 1 - Pull data from the Pearson tenant and print a short summary.

Raw data is saved to output/ (this folder is in .gitignore).

Run from the repo folder:
    python src\\pull_entra_data.py
"""

import json
from collections import defaultdict
from pathlib import Path

from entra_data import (
    get_conditional_access_policies,
    get_mfa_registration,
    get_role_assignments,
    get_users,
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def save(name: str, data) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / f"{name}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


def show_users() -> dict:
    """Print the users and return a map of user id -> UPN (used by the CA section)."""
    users = get_users()
    save("users", users)

    guests = [u for u in users if u.get("userType") == "Guest"]
    disabled = [u for u in users if u.get("accountEnabled") is False]

    print(f"===== Users: {len(users)} total, {len(guests)} guests, {len(disabled)} disabled =====")
    for u in users:
        status = "enabled" if u.get("accountEnabled") else "DISABLED"
        print(f"- {u['displayName']:<30} {u['userType'] or '-':<7} {status:<9} {u['userPrincipalName']}")
    print()
    return {u["id"]: u["userPrincipalName"] for u in users}


def show_roles() -> None:
    rows = get_role_assignments()
    save("role_assignments", rows)

    by_role = defaultdict(list)
    for r in rows:
        by_role[r["role"]].append(r)

    print(f"===== Admin roles: {len(rows)} assignments in {len(by_role)} roles =====")
    for role in sorted(by_role):
        print(f"{role} ({len(by_role[role])})")
        for r in by_role[role]:
            who = r["principal_upn"] or r["principal_name"]
            print(f"    - {who}  [{r['principal_type']}]")
    print()


def show_ca_policies(user_names: dict) -> None:
    policies = get_conditional_access_policies()
    save("conditional_access_policies", policies)

    print(f"===== Conditional Access policies: {len(policies)} =====")
    for p in policies:
        conditions = p.get("conditions") or {}
        grant_controls = p.get("grantControls") or {}

        # Grant can be built-in controls (mfa, block, ...) or an authentication strength
        grant = list(grant_controls.get("builtInControls") or [])
        strength = grant_controls.get("authenticationStrength")
        if strength:
            grant.append(f"auth strength: {strength['displayName']}")

        users = conditions.get("users") or {}
        who = [user_names.get(u, u) for u in users.get("includeUsers") or []]
        if users.get("includeRoles"):
            who.append(f"{len(users['includeRoles'])} role(s)")
        if users.get("includeGroups"):
            who.append(f"{len(users['includeGroups'])} group(s)")

        apps = (conditions.get("applications") or {}).get("includeApplications") or []
        client_apps = conditions.get("clientAppTypes") or []

        print(f"- {p['displayName']}")
        print(f"    state: {p['state']} | grant: {', '.join(grant) or '-'}")
        print(f"    users: {', '.join(who) or '-'} | apps: {', '.join(apps) or '-'} | client apps: {', '.join(client_apps) or '-'}")
    if not policies:
        print("No Conditional Access policies found.")
    print()


def show_mfa() -> None:
    try:
        details = get_mfa_registration()
    except RuntimeError as e:
        # Common reason: no Entra ID P1/P2 licence in the tenant
        print("===== MFA registration: NOT AVAILABLE =====")
        print(e)
        print()
        return
    save("mfa_registration", details)

    no_mfa = [d for d in details if not d.get("isMfaRegistered")]
    admins_no_mfa = [d for d in no_mfa if d.get("isAdmin")]

    print(f"===== MFA registration: {len(details)} users, {len(no_mfa)} without MFA, "
          f"{len(admins_no_mfa)} of them admins =====")
    for d in no_mfa:
        flag = "ADMIN" if d.get("isAdmin") else ""
        print(f"- {d['userPrincipalName']:<45} no MFA  {flag}")
    print()


if __name__ == "__main__":
    user_names = show_users()
    show_roles()
    show_ca_policies(user_names)
    show_mfa()
