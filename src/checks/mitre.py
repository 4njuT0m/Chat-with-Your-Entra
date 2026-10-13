"""MITRE ATT&CK techniques for each check.

Each failed finding gets the techniques an attacker could use because of the weakness.
IDs, names and tactics are taken from attack.mitre.org.
"""

TECHNIQUES = {
    "T1078.004": {
        "name": "Valid Accounts: Cloud Accounts",
        "tactics": "Initial Access, Persistence, Privilege Escalation, Stealth",
        "url": "https://attack.mitre.org/techniques/T1078/004/",
    },
    "T1110.003": {
        "name": "Brute Force: Password Spraying",
        "tactics": "Credential Access",
        "url": "https://attack.mitre.org/techniques/T1110/003/",
    },
    "T1098.001": {
        "name": "Account Manipulation: Additional Cloud Credentials",
        "tactics": "Persistence, Privilege Escalation",
        "url": "https://attack.mitre.org/techniques/T1098/001/",
    },
    "T1098.003": {
        "name": "Account Manipulation: Additional Cloud Roles",
        "tactics": "Persistence, Privilege Escalation",
        "url": "https://attack.mitre.org/techniques/T1098/003/",
    },
}

# Which techniques each check is about
CHECK_TECHNIQUES = {
    "legacy_auth": ["T1110.003", "T1078.004"],
    "admin_mfa_registered": ["T1110.003", "T1078.004"],
    "admin_mfa_enforced": ["T1078.004"],
    "sp_graph_permissions": ["T1098.003", "T1098.001"],
    "sp_admin_roles": ["T1098.001", "T1078.004"],
    "global_admin_count": ["T1078.004"],
}


def add_mitre(finding: dict) -> dict:
    """Add a mitre_attack list to a finding."""
    ids = CHECK_TECHNIQUES.get(finding.get("check"), [])
    finding["mitre_attack"] = [{"id": i, **TECHNIQUES[i]} for i in ids]
    return finding
