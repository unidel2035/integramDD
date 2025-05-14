async def verify_token(token: str) -> dict:
    # TODO: later use Keycloak JWT verification here
    return {"user_id": 1, "role": "admin"}