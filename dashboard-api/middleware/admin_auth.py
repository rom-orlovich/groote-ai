import os

from fastapi import Header, HTTPException, status


def verify_admin_token(x_admin_token: str = Header(None)) -> None:
    expected_token = os.getenv("ADMIN_SETUP_TOKEN", "")
    if not expected_token or x_admin_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
        )
