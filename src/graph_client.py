"""Microsoft Graph client for the Pearson lab tenant.

Gets an app-only token with the client credentials flow
(client ID + client secret from the App Registration) and runs GET requests.

Run this file directly to test the connection:
    python src\\graph_client.py
"""

import os

import msal
import requests
from dotenv import load_dotenv

load_dotenv()

GRAPH_URL = "https://graph.microsoft.com/v1.0"
# ".default" = use all application permissions that an admin granted to the app
SCOPE = ["https://graph.microsoft.com/.default"]

_app = None


def _get_app() -> msal.ConfidentialClientApplication:
    """Create the MSAL app once and reuse it (MSAL keeps the token in memory)."""
    global _app
    if _app is None:
        _app = msal.ConfidentialClientApplication(
            client_id=os.environ["PEARSON_CLIENT_ID"],
            client_credential=os.environ["PEARSON_CLIENT_SECRET"],
            authority=f"https://login.microsoftonline.com/{os.environ['PEARSON_TENANT_ID']}",
        )
    return _app


def get_token() -> str:
    """Return an access token for Microsoft Graph."""
    result = _get_app().acquire_token_for_client(scopes=SCOPE)
    if "access_token" not in result:
        raise RuntimeError(
            f"Could not get a token: {result.get('error')} - {result.get('error_description')}"
        )
    return result["access_token"]


def _check(response: requests.Response) -> dict:
    """Raise a readable error if Graph returns an error, otherwise return the JSON."""
    if response.ok:
        return response.json()
    try:
        error = response.json().get("error", {})
        message = f"{error.get('code')}: {error.get('message')}"
    except ValueError:
        message = response.text
    raise RuntimeError(f"Graph error {response.status_code} on {response.url}\n{message}")


def graph_get(path: str, params: dict | None = None):
    """GET from Microsoft Graph.

    For lists, Graph returns results in pages. This follows "@odata.nextLink"
    until the last page, so the full list comes back.
    """
    headers = {"Authorization": f"Bearer {get_token()}"}
    url = path if path.startswith("https://") else f"{GRAPH_URL}{path}"

    data = _check(requests.get(url, headers=headers, params=params, timeout=30))
    if "value" not in data:
        return data  # a single object, not a list

    items = data["value"]
    while "@odata.nextLink" in data:
        data = _check(requests.get(data["@odata.nextLink"], headers=headers, timeout=30))
        items.extend(data["value"])
    return items


if __name__ == "__main__":
    # Connection test: read the tenant (organization) name
    org = graph_get("/organization", params={"$select": "displayName,id"})[0]
    print(f"Connected to tenant: {org['displayName']}")
    print("Token received and Graph call worked.")
