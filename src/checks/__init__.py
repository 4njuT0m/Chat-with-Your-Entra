"""Stage 3 - Security checks.

Each check module has a run() function that returns a list of findings.
A finding has: check, title, status (PASS/FAIL/WARN/ERROR), severity, evidence, reference.
The checks collect the evidence. The AI explains the risk and the fix.
"""

from checks import admin_mfa, global_admins, legacy_auth, sp_privileges

CHECKS = {
    "legacy_auth": legacy_auth,
    "admin_mfa": admin_mfa,
    "sp_privileges": sp_privileges,
    "global_admins": global_admins,
}


def run_checks(name: str = "all") -> list[dict]:
    selected = CHECKS if name == "all" else {name: CHECKS[name]}
    findings = []
    for check_name, module in selected.items():
        try:
            findings.extend(module.run())
        except Exception as e:  # one broken check should not stop the audit
            findings.append(
                {"check": check_name, "status": "ERROR", "severity": "-", "title": f"{type(e).__name__}: {e}"}
            )
    return findings
