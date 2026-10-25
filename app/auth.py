"""
auth.py — Clerk JWT validation middleware
Converted from: src/middleware.ts (Clerk auth + role-based access)
"""
from typing import Optional
import httpx
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import settings, ROUTE_ACCESS_MAP

security = HTTPBearer(auto_error=False)

# Cache for Clerk JWKS
_jwks_cache: Optional[dict] = None


async def get_clerk_jwks() -> dict:
    """Fetch Clerk's JSON Web Key Set (JWKS) for token verification."""
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache
    jwks_url = f"{settings.clerk_jwt_issuer}/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        _jwks_cache = response.json()
    return _jwks_cache


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Validate Clerk JWT and return the session claims.
    Equivalent to: clerkMiddleware / auth() in middleware.ts
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = credentials.credentials
    try:
        jwks = await get_clerk_jwks()
        # Decode without verification first to get the key ID
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        # Find the matching key
        key = next(
            (k for k in jwks.get("keys", []) if k.get("kid") == kid), None
        )
        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token key",
            )

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )


def get_user_role(claims: dict = Depends(get_current_user)) -> str:
    """Extract the role from Clerk session claims metadata."""
    metadata = claims.get("metadata", {}) or claims.get("public_metadata", {})
    role = metadata.get("role")
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No role assigned to this user",
        )
    return role


def require_roles(*allowed_roles: str):
    """
    Dependency factory for role-based access control.
    Equivalent to routeAccessMap + middleware logic in middleware.ts

    Usage:
        @router.get("/admin", dependencies=[Depends(require_roles("admin"))])
    """
    def role_checker(role: str = Depends(get_user_role)) -> str:
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required: {allowed_roles}, got: {role}",
            )
        return role

    return role_checker
