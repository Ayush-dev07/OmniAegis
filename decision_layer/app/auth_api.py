from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from dataclasses import dataclass
from threading import Lock
from typing import Any

import httpx
from fastapi import APIRouter, Header, HTTPException
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from pydantic import BaseModel, Field


router = APIRouter(prefix="/auth", tags=["auth"])


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(raw: str) -> bytes:
    padding = "=" * ((4 - len(raw) % 4) % 4)
    return base64.urlsafe_b64decode((raw + padding).encode("ascii"))


def _normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        raise HTTPException(status_code=400, detail="Invalid email format")
    return normalized


def _auth_secret() -> str:
    return (
        os.getenv("AUTH_TOKEN_SECRET")
        or os.getenv("SUPABASE_SERVICE_KEY")
        or "dev-insecure-auth-secret-change-me"
    )


def _hash_password(password: str, iterations: int = 210_000) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations, salt_hex, digest_hex = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        ).hex()
        return hmac.compare_digest(candidate, digest_hex)
    except Exception:
        return False


def _create_access_token(
    user_id: str,
    email: str,
    role: str,
    name: str,
    ttl_seconds: int = 60 * 60 * 24 * 7,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "name": name,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = _b64url_encode(payload_bytes)
    sig = hmac.new(_auth_secret().encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    return f"{payload_b64}.{_b64url_encode(sig)}"


def _decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload_b64, sig_b64 = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Malformed token") from exc

    expected_sig = hmac.new(
        _auth_secret().encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256
    ).digest()
    actual_sig = _b64url_decode(sig_b64)
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise HTTPException(status_code=401, detail="Invalid token signature")

    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(status_code=401, detail="Token expired")
    return payload


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authorization must be Bearer token")

    token = parts[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return token


@dataclass
class SupabaseConfig:
    url: str
    service_key: str
    users_table: str = "users"


@dataclass(frozen=True)
class AuthQdrantConfig:
    url: str
    api_key: str
    collection_name: str = "auth_users"


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)
    role: str = Field(default="reviewer", pattern="^(admin|reviewer)$")


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)


class GoogleAuthRequest(BaseModel):
    mode: str = Field(pattern="^(login|signup)$")
    email: str = Field(min_length=3, max_length=320)
    name: str = Field(min_length=1, max_length=120)
    google_sub: str | None = Field(default=None, min_length=1, max_length=255)


class AuthUser(BaseModel):
    user_id: str
    email: str
    role: str
    name: str


class AuthResponse(BaseModel):
    user: AuthUser
    access_token: str
    token_type: str = "bearer"


class _SupabaseUsersClient:
    def __init__(self, config: SupabaseConfig) -> None:
        self._config = config
        self._table_url = f"{config.url.rstrip('/')}/rest/v1/{config.users_table}"

    def _headers(self, *, returning: bool = False) -> dict[str, str]:
        headers = {
            "apikey": self._config.service_key,
            "Authorization": f"Bearer {self._config.service_key}",
            "Content-Type": "application/json",
        }
        if returning:
            headers["Prefer"] = "return=representation"
        return headers

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        select = "user_id,email,role,name,password_hash,provider,google_sub"
        params = {
            "email": f"eq.{email}",
            "select": select,
            "limit": "1",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self._table_url, headers=self._headers(), params=params)

        if response.status_code >= 400:
            raise RuntimeError(f"Supabase query failed: {response.status_code} {response.text}")

        rows = response.json()
        if not rows:
            return None
        return rows[0]

    async def create_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self._table_url,
                headers=self._headers(returning=True),
                json=payload,
            )

        if response.status_code >= 400:
            if response.status_code == 409:
                raise ValueError("User already exists")
            raise RuntimeError(f"Supabase insert failed: {response.status_code} {response.text}")

        rows = response.json()
        if not rows:
            raise RuntimeError("Supabase did not return created user")
        return rows[0]

    async def delete_user_by_id(self, user_id: str) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(
                self._table_url,
                headers=self._headers(),
                params={"user_id": f"eq.{user_id}"},
            )

        if response.status_code >= 400:
            raise RuntimeError(f"Supabase delete failed: {response.status_code} {response.text}")


class _QdrantAuthLinkClient:
    _client: QdrantClient | None = None
    _collection_ready = False
    _lock = Lock()

    @classmethod
    def _config(cls) -> AuthQdrantConfig:
        url = (os.getenv("QDRANT_URL") or "").strip().strip('"')
        api_key = (os.getenv("QDRANT_API_KEY") or "").strip().strip('"')
        collection_name = (os.getenv("QDRANT_USERS_COLLECTION") or "auth_users").strip()

        if not url or not api_key:
            raise HTTPException(status_code=503, detail="QDRANT_URL and QDRANT_API_KEY are required")

        return AuthQdrantConfig(url=url, api_key=api_key, collection_name=collection_name)

    @classmethod
    def _get_client(cls) -> QdrantClient:
        if cls._client is None:
            cfg = cls._config()
            cls._client = QdrantClient(url=cfg.url, api_key=cfg.api_key)
        return cls._client

    @classmethod
    def _ensure_collection(cls) -> AuthQdrantConfig:
        cfg = cls._config()
        if cls._collection_ready:
            return cfg

        with cls._lock:
            if cls._collection_ready:
                return cfg

            client = cls._get_client()
            existing = {collection.name for collection in client.get_collections().collections}
            if cfg.collection_name not in existing:
                client.create_collection(
                    collection_name=cfg.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=1,
                        distance=qmodels.Distance.DOT,
                        on_disk=True,
                    ),
                    hnsw_config=qmodels.HnswConfigDiff(
                        m=8,
                        ef_construct=64,
                        on_disk=True,
                    ),
                )

            cls._collection_ready = True
            return cfg

    @classmethod
    def upsert_user(cls, row: dict[str, Any]) -> None:
        cfg = cls._ensure_collection()
        user_id = str(row["user_id"])
        client = cls._get_client()
        client.upsert(
            collection_name=cfg.collection_name,
            points=[
                qmodels.PointStruct(
                    id=user_id,
                    vector=[1.0],
                    payload={
                        "user_id": user_id,
                        "email": str(row.get("email") or ""),
                        "role": str(row.get("role") or "reviewer"),
                        "name": str(row.get("name") or "User"),
                        "provider": str(row.get("provider") or "password"),
                        "google_sub": row.get("google_sub"),
                    },
                )
            ],
            wait=True,
        )


def _supabase_client() -> _SupabaseUsersClient:
    url = (os.getenv("SUPABASE_URL") or "").strip().strip('"')
    service_key = (os.getenv("SUPABASE_SERVICE_KEY") or "").strip().strip('"')
    users_table = (os.getenv("SUPABASE_USERS_TABLE") or "users").strip()

    if not url or not service_key:
        raise HTTPException(status_code=503, detail="SUPABASE_URL and SUPABASE_SERVICE_KEY are required")

    return _SupabaseUsersClient(
        SupabaseConfig(url=url, service_key=service_key, users_table=users_table),
    )


def _auth_response_from_row(row: dict[str, Any]) -> AuthResponse:
    user = AuthUser(
        user_id=str(row["user_id"]),
        email=_normalize_email(str(row["email"])),
        role=str(row.get("role") or "reviewer"),
        name=str(row.get("name") or "User"),
    )
    token = _create_access_token(user.user_id, user.email, user.role, user.name)
    return AuthResponse(user=user, access_token=token)


@router.post("/signup", response_model=AuthResponse)
async def signup(body: SignupRequest) -> AuthResponse:
    client = _supabase_client()
    email = _normalize_email(body.email)

    existing = await client.get_user_by_email(email)
    if existing is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user_id = str(uuid.uuid4())
    try:
        user_row = await client.create_user(
            {
                "user_id": user_id,
                "email": email,
                "password_hash": _hash_password(body.password),
                "name": body.name.strip(),
                "role": body.role,
                "provider": "password",
            }
        )
        _QdrantAuthLinkClient.upsert_user(user_row)
    except Exception as exc:
        try:
            await client.delete_user_by_id(user_id)
        except Exception:
            pass
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=503, detail="Unable to persist the new account") from exc

    return _auth_response_from_row(user_row)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest) -> AuthResponse:
    client = _supabase_client()
    email = _normalize_email(body.email)

    existing = await client.get_user_by_email(email)
    if existing is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    provider = str(existing.get("provider") or "password")
    password_hash = existing.get("password_hash")

    if provider == "google" and not password_hash:
        raise HTTPException(status_code=400, detail="This account uses Google sign-in")

    if not password_hash or not _verify_password(body.password, str(password_hash)):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return _auth_response_from_row(existing)


@router.post("/google", response_model=AuthResponse)
async def google_auth(body: GoogleAuthRequest) -> AuthResponse:
    client = _supabase_client()
    email = _normalize_email(body.email)
    existing = await client.get_user_by_email(email)

    if body.mode == "login" and existing is None:
        raise HTTPException(status_code=404, detail="No account found for this Google user")

    if body.mode == "signup" and existing is not None:
        raise HTTPException(status_code=409, detail="Account already exists")

    if existing is None:
        role = "admin" if email == "admin@sentinelai.com" else "reviewer"
        user_id = str(uuid.uuid4())
        try:
            created = await client.create_user(
                {
                    "user_id": user_id,
                    "email": email,
                    "password_hash": None,
                    "name": body.name.strip(),
                    "role": role,
                    "provider": "google",
                    "google_sub": body.google_sub,
                }
            )
            _QdrantAuthLinkClient.upsert_user(created)
        except Exception as exc:
            try:
                await client.delete_user_by_id(user_id)
            except Exception:
                pass
            if isinstance(exc, HTTPException):
                raise
            raise HTTPException(status_code=503, detail="Unable to persist the new Google account") from exc
        return _auth_response_from_row(created)

    return _auth_response_from_row(existing)


@router.get("/me", response_model=AuthUser)
async def me(authorization: str | None = Header(default=None)) -> AuthUser:
    token = _extract_bearer_token(authorization)
    payload = _decode_access_token(token)
    return AuthUser(
        user_id=str(payload["sub"]),
        email=_normalize_email(str(payload["email"])),
        role=str(payload.get("role") or "reviewer"),
        name=str(payload.get("name") or "User"),
    )
