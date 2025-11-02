#!/usr/bin/env python3
"""
Generate a valid JWT token for testing CLI tools.
Uses the JWT_SECRET from your .env file to create a properly formatted token.
"""

import os
import sys
import time
from pathlib import Path

import jwt
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

JWT_SECRET = os.getenv("JWT_SECRET")

if not JWT_SECRET:
    print("ERROR: JWT_SECRET not found in .env file", file=sys.stderr)
    sys.exit(1)

# Create a test token with all required claims
payload = {
    "sub": "test-user-12345",  # User ID (can be any string for testing)
    "aud": "authenticated",  # CRITICAL: audience claim required by middleware
    "role": "authenticated",  # User role
    "iss": "supabase",  # Issuer
    "iat": int(time.time()),  # Issued at
    "exp": int(time.time()) + 3600,  # Expires in 1 hour
}

token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

print("\n" + "=" * 60)
print("Generated Test JWT Token")
print("=" * 60)
print("\nToken (copy this):")
print(token)
print("\nToken details:")
print(f"  User ID (sub): {payload['sub']}")
print(f"  Audience (aud): {payload['aud']}")
print(f"  Role: {payload['role']}")
print(f"  Expires: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(payload['exp']))}")
print("\nUse this token when running file_stats_cli.py")
print("=" * 60 + "\n")
