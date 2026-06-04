"""
Service xu ly nghiep vu dang ky / dang nhap.
"""

import binascii
import hashlib
import hmac
import os

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.auth_repo import create_user, get_user_by_email
from schemas.auth_schema import LoginIn, RegisterIn

PBKDF2_ITERATIONS = 100_000


def _hash_password(password: str) -> str:
    """
    Hash mat khau bang PBKDF2-HMAC-SHA256.
    """
    salt = os.urandom(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    salt_hex = binascii.hexlify(salt).decode("utf-8")
    hash_hex = binascii.hexlify(password_hash).decode("utf-8")
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_hex}${hash_hex}"


def _verify_password(password: str, stored_password_hash: str) -> bool:
    """
    Kiem tra mat khau plaintext voi hash luu trong DB.
    """
    try:
        algorithm, iterations_str, salt_hex, hash_hex = stored_password_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations_str)
        salt = binascii.unhexlify(salt_hex.encode("utf-8"))
        expected_hash = binascii.unhexlify(hash_hex.encode("utf-8"))

        candidate_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(candidate_hash, expected_hash)
    except (ValueError, binascii.Error):
        return False


async def register_user(
    db: AsyncSession,
    payload: RegisterIn,
):
    """
    Dang ky tai khoan moi.
    """
    email = payload.email.strip().lower()

    try:
        existing_user = await get_user_by_email(db=db, email=email)
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email da ton tai.",
            )

        password_hash = _hash_password(payload.password)
        return await create_user(
            db=db,
            email=email,
            password_hash=password_hash,
            full_name=payload.full_name,
            role=payload.role,
            phone=payload.phone,
        )
    except HTTPException:
        raise
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Du lieu dang ky khong hop le.",
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Loi he thong khi tao tai khoan.",
        ) from exc


async def login_user(
    db: AsyncSession,
    payload: LoginIn,
):
    """
    Dang nhap bang email va mat khau.
    """
    email = payload.email.strip().lower()

    try:
        user = await get_user_by_email(db=db, email=email)
        if user is None or not _verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email hoac mat khau khong dung.",
            )
        return user
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Loi he thong khi dang nhap.",
        ) from exc
