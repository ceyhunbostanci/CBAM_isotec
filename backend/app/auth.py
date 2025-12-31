import hashlib
from itsdangerous import URLSafeTimedSerializer, BadSignature
from fastapi import Request
from typing import Optional

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def verify_password(pw: str, pw_hash: str) -> bool:
    return hash_password(pw) == pw_hash

def get_serializer(secret: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret_key=secret, salt="isotec-cbam-session")

def sign_session(secret: str, user_id: int) -> str:
    s = get_serializer(secret)
    return s.dumps({"user_id": user_id})

def read_session(secret: str, token: str, max_age_seconds: int = 60*60*12) -> Optional[int]:
    s = get_serializer(secret)
    try:
        data = s.loads(token, max_age=max_age_seconds)
        return int(data.get("user_id"))
    except (BadSignature, Exception):
        return None

def current_user_id(request: Request, secret: str) -> Optional[int]:
    token = request.cookies.get("session")
    if not token:
        return None
    return read_session(secret, token)
