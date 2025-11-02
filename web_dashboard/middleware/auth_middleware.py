# web_dashboard/middleware/auth_middleware.py
"""
JWT verification middleware for Supabase authentication.
Validates JWT tokens from HTTP-only cookies and extracts user information.
"""

import logging
import os
from typing import Callable

import jwt
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Load JWT secret from environment
SUPABASE_JWT_SECRET = os.getenv("JWT_SECRET")

# Public endpoints that don't require authentication
# Note: Use exact matches for root path to avoid matching all endpoints
PUBLIC_ENDPOINTS = [
    "/api/health",  # Health check
    "/docs",  # API docs
    "/openapi.json",  # OpenAPI spec
    "/static",  # Static files
    "/ws",  # WebSocket connections (upgrade protocol, no JWT in handshake)
]

# Exact match endpoints (not prefix match)
EXACT_PUBLIC_ENDPOINTS = [
    "/",  # Dashboard homepage (exact match only)
]


async def verify_jwt_middleware(request: Request, call_next: Callable):
    """
    Middleware to verify JWT tokens from cookies.
    Extracts user_id and is_anonymous from token and adds to request.state.
    Skips verification for public endpoints.
    """

    # Get request path
    request_path = request.url.path

    # CRITICAL: Skip auth for OPTIONS requests (CORS preflight)
    # OPTIONS requests are sent by browsers automatically and cannot include auth headers
    if request.method == "OPTIONS":
        logger.debug(f"[AuthMiddleware] Skipping auth for CORS preflight: OPTIONS {request_path}")
        return await call_next(request)

    # Skip auth for public endpoints
    # Check if path starts with any public endpoint (prefix match)
    # OR if path exactly matches an exact-match endpoint
    is_public = (
        any(request_path.startswith(endpoint) for endpoint in PUBLIC_ENDPOINTS)
        or request_path in EXACT_PUBLIC_ENDPOINTS
    )

    if is_public:
        logger.debug(f"[AuthMiddleware] Skipping auth for public endpoint: {request_path}")
        return await call_next(request)

    # Check if JWT_SECRET is configured

    if not SUPABASE_JWT_SECRET:
        # In production, JWT_SECRET is mandatory
        environment = os.getenv("ENVIRONMENT", "development").lower()
        if environment == "production":
            logger.error("[AuthMiddleware] JWT_SECRET not configured in production environment")
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": "Server configuration error. Please contact administrator.",
                        "code": "SERVER_MISCONFIGURED",
                    }
                },
            )

        logger.warning(
            "[AuthMiddleware] JWT_SECRET not configured, skipping auth verification (development mode)"
        )
        # Continue without auth in development
        return await call_next(request)

    # Extract JWT from Authorization header or cookie
    # Priority: Authorization header (frontend sends JWT here), then cookies (fallback)
    access_token = None

    # Check Authorization header first (Bearer token)
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header.split(" ")[1]
        logger.debug("[AuthMiddleware] Token found in Authorization header")
    else:
        # Fallback to cookies (for backward compatibility)
        access_token = request.cookies.get("sb-access-token") or request.cookies.get("access_token")
        if access_token:
            logger.debug("[AuthMiddleware] Token found in cookies")

    if not access_token:
        logger.warning(f"[AuthMiddleware] No authentication token found for {request_path}")
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "message": "No authentication token. Please sign in.",
                    "code": "UNAUTHORIZED",
                }
            },
        )

    try:
        # Verify JWT signature
        # Supabase uses HS256 algorithm
        # First, decode without audience verification to inspect the token
        # This allows us to see what audience claim is present
        try:
            # Try with standard "authenticated" audience first
            payload = jwt.decode(
                access_token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_exp": True},
            )
        except jwt.InvalidAudienceError:
            # Fallback: Supabase anonymous users might have different audience
            # Decode without audience check but still validate signature and expiry
            logger.info("[AuthMiddleware] Standard audience check failed, trying flexible decode")
            payload = jwt.decode(
                access_token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False, "verify_exp": True},
            )
            # Log the actual audience for debugging
            actual_aud = payload.get("aud")
            logger.warning(
                f"[AuthMiddleware] Token has non-standard audience: {actual_aud}. "
                "Consider updating audience verification logic."
            )

        # Extract user information from token
        user_id = payload.get("sub")
        is_anonymous = payload.get("is_anonymous", False)
        role = payload.get("role", "anon")

        # Log successful authentication (keep at INFO for production monitoring)
        logger.info(
            f"[AuthMiddleware] Authenticated: user={user_id[:8]}... role={role} anon={is_anonymous}"
        )

        if not user_id:
            logger.error("[AuthMiddleware] JWT valid but no 'sub' claim found")
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "message": "Invalid token: missing user ID.",
                        "code": "INVALID_TOKEN_CLAIMS",
                    }
                },
            )

        # Add user info to request state
        request.state.user_id = user_id
        request.state.is_anonymous = is_anonymous
        request.state.role = role

        # Continue processing request
        return await call_next(request)

    except jwt.InvalidAudienceError:
        logger.warning(f"[AuthMiddleware] Invalid audience for {request_path}")
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "message": "Invalid token audience.",
                    "code": "INVALID_AUDIENCE",
                }
            },
        )

    except jwt.ExpiredSignatureError:
        logger.warning(f"[AuthMiddleware] Expired token for {request_path}")
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "message": "Token expired. Please sign in again.",
                    "code": "TOKEN_EXPIRED",
                }
            },
        )

    except jwt.InvalidTokenError as e:
        logger.warning(f"[AuthMiddleware] Invalid token for {request_path}: {str(e)}")
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "message": "Invalid authentication token.",
                    "code": "INVALID_TOKEN",
                }
            },
        )

    except Exception as e:
        logger.error(f"[AuthMiddleware] Unexpected error during auth: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": {"message": "Authentication error.", "code": "AUTH_ERROR"}},
        )
