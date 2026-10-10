"""Stage 1 - Pull data from the Pearson tenant and print a short summary.

Raw data is saved to output/ (this folder is in .gitignore).

Run from the repo folder:
    python src\\pull_entra_data.py
"""

import json
from pathlib import Path

from entra_data import get_users

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def save(name: str, data) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / f"{name}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


def show_users() -> None:
    users = get_users()
    save("users", users)

    guests = [u for u in users if u.get("userType") == "Guest"]
    disabled = [u for u in users if u.get("accountEnabled") is False]

    print(f"===== Users: {len(users)} total, {len(guests)} guests, {len(disabled)} disabled =====")
    for u in users:
        status = "enabled" if u.get("accountEnabled") else "DISABLED"
        print(f"- {u['displayName']:<30} {u['userType'] or '-':<7} {status:<9} {u['userPrincipalName']}")
    print()


if __name__ == "__main__":
    show_users()
