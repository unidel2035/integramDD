from fastapi import Header, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

class CustomBearer(HTTPBearer):
    def __init__(self):
        super().__init__(scheme_name="BearerAuth") 

security = CustomBearer()

def verify_token(raw_token: str):
    """
    Validates a Bearer token string manually extracted from headers.

    Args:
        raw_token (str): The value of the 'Authorization' header.

    Returns:
        dict: Mock user identity if token is valid.

    Raises:
        HTTPException: If token is missing, malformed, or invalid.
    """
    if not raw_token or not raw_token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed token")

    token = raw_token[len("Bearer "):].strip()

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