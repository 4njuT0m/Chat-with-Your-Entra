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
