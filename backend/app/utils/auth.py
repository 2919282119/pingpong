import os
from datetime import datetime, timedelta

import jwt as pyjwt

JWT_SECRET = os.environ.get("JWT_SECRET", "")
JWT_EXPIRES_IN = os.environ.get("JWT_EXPIRES_IN", "7d")


def create_token(user_id: str) -> str:
    days = int(JWT_EXPIRES_IN.replace("d", ""))
    payload = {
        "userId": user_id,
        "exp": datetime.utcnow() + timedelta(days=days),
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict | None:
    try:
        return pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None
