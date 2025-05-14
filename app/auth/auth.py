from fastapi import Header, HTTPException, status

async def verify_token(authorization: str = Header(...)) -> dict:
    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )

    # Заглушка: валидный токен — это "super-secret-token"
    if token != "super-secret-token":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token"
        )

    return {"user_id": 1, "username": "admin", "role": "admin"}