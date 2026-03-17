"""Shared auth helpers. Prefixed with _ so Vercel doesn't expose it as an endpoint."""

import os
import json
import time
import hashlib
import secrets
import jwt
from upstash_redis import Redis


def get_redis():
    url = (
        os.environ.get("KV_REST_API_URL")
        or os.environ.get("UPSTASH_REDIS_REST_URL")
        or ""
    )
    token = (
        os.environ.get("KV_REST_API_TOKEN")
        or os.environ.get("UPSTASH_REDIS_REST_TOKEN")
        or ""
    )
    return Redis(url=url, token=token)


def hash_password(password):
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${h}"


def verify_password(password, password_hash):
    try:
        salt, h = password_hash.split("$", 1)
        return hashlib.sha256((salt + password).encode("utf-8")).hexdigest() == h
    except (ValueError, AttributeError):
        return False


def get_jwt_secret():
    return os.environ.get("JWT_SECRET", "change-me-in-production")


def create_token(email, role):
    payload = {
        "email": email,
        "role": role,
        "exp": int(time.time()) + 86400 * 7,  # 7 days
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm="HS256")


def verify_token(token):
    try:
        return jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def get_current_user(headers):
    """Extract and verify JWT from Authorization header, return user dict or None."""
    auth_header = headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]
    payload = verify_token(token)
    if not payload:
        return None

    redis = get_redis()
    user_data = redis.get(f"user:{payload['email']}")
    if not user_data:
        return None

    if isinstance(user_data, str):
        user = json.loads(user_data)
    else:
        user = user_data

    return user


def require_approved(headers):
    """Return user if approved/admin, else None."""
    user = get_current_user(headers)
    if not user:
        return None
    if user.get("role") not in ("approved", "admin"):
        return None
    return user


def send_json(handler, status, data):
    """Helper to send JSON response with CORS headers."""
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.end_headers()
    handler.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))


def handle_options(handler):
    """Handle CORS preflight."""
    handler.send_response(200)
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.end_headers()
