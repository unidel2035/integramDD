from fastapi import Header, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Validates the Authorization header using a simple bearer token check.

    This is a stub implementation meant to be replaced by proper JWT verification (e.g., via Keycloak).

    Args:
        authorization (str): The 'Authorization' header from the request.

    Raises:
        HTTPException: If the header is missing or invalid.
        HTTPException: If the token is not recognized.

    Returns:
        dict: A dictionary representing the authenticated user's identity.
    """
    token = credentials.credentials
    scheme = credentials.scheme if credentials else ""

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    if token != "secret-token":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token",
        )

    return {
        "user_id": 1,
        "username": "admin",
        "role": "admin",
    }
