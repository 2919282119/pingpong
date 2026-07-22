import logging
from datetime import datetime, timedelta
import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import bcrypt

from app.database import get_db
from app.models.db import User, UserToken, VerifyCode, generate_user_id
from app.utils.auth import create_token
from app.utils.email import send_verify_code_email
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


def _format_user(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name or "",
        "avatar": user.avatar or "",
        "gender": user.gender or "",
        "birthdate": str(user.birthdate) if user.birthdate else "",
        "startPlayingYear": user.startPlayingYear or "",
        "playStyle": user.playStyle or "",
        "selfDescription": user.selfDescription or "",
        "bgImg": user.bgImg or "",
        "address": user.address or "",
        "latitude": float(user.latitude) if user.latitude else None,
        "longitude": float(user.longitude) if user.longitude else None,
    }


@router.post("/register")
def register(body: dict, db: Session = Depends(get_db)):
    email = body.get("email", "").strip()
    password = body.get("password", "")
    nickname = body.get("nickname", "").strip()
    verify_code = body.get("verifyCode", "").strip()
    gender = body.get("gender", "男")

    if not all([email, password, nickname, verify_code]):
        raise HTTPException(status_code=400, detail="请填写完整信息")

    import re
    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")

    if len(password) < 6:
        raise HTTPException(status_code=400, detail="密码长度不能少于6位")

    code_record = db.query(VerifyCode).filter(
        VerifyCode.email == email,
        VerifyCode.code == verify_code,
        VerifyCode.type == "register",
        VerifyCode.used == False,
        VerifyCode.expiresAt > datetime.now(),
    ).order_by(VerifyCode.createdAt.desc()).first()

    if code_record is None:
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱已被注册")

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user_id = generate_user_id()

    user = User(
        id=user_id, email=email, password=hashed,
        name=nickname, gender=gender, online=True,
        lastActiveTime=datetime.now(),
    )
    db.add(user)

    # Create default settings
    from app.models.db import UserSettings
    db.add(UserSettings(userId=user_id))

    code_record.used = True
    db.commit()

    token = create_token(user_id)
    expires_at = datetime.now() + timedelta(days=7)
    db.add(UserToken(userId=user_id, token=token, expiresAt=expires_at))
    db.commit()

    return {"success": True, "token": token, "userInfo": _format_user(user)}


@router.post("/login")
def login(body: dict, db: Session = Depends(get_db)):
    email = body.get("email", "").strip()
    password = body.get("password", "")

    if not email or not password:
        raise HTTPException(status_code=400, detail="请输入邮箱和密码")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    if not user.password or not bcrypt.checkpw(password.encode(), user.password.encode()):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    user.online = True
    user.lastActiveTime = datetime.now()

    token = create_token(user.id)
    expires_at = datetime.now() + timedelta(days=7)
    db.add(UserToken(userId=user.id, token=token, expiresAt=expires_at))
    db.commit()

    return {"success": True, "token": token, "userInfo": _format_user(user)}


@router.post("/sendVerifyCode")
def send_verify_code(body: dict, db: Session = Depends(get_db)):
    email = body.get("email", "").strip()
    type_ = body.get("type", "register")

    if not email:
        raise HTTPException(status_code=400, detail="请输入邮箱")

    import re
    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")

    if type_ == "register":
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(status_code=400, detail="该邮箱已被注册")

    recent = db.query(VerifyCode).filter(
        VerifyCode.email == email,
        VerifyCode.type == type_,
        VerifyCode.createdAt > datetime.now() - timedelta(minutes=1),
    ).first()
    if recent:
        raise HTTPException(status_code=400, detail="验证码发送过于频繁，请稍后再试")

    code = f"{random.randint(100000, 999999)}"
    expires_at = datetime.now() + timedelta(minutes=5)

    db.add(VerifyCode(email=email, code=code, type=type_, expiresAt=expires_at))
    db.commit()

    sent = send_verify_code_email(email, code, type_)
    if sent:
        return {"success": True, "message": "验证码已发送到您的邮箱，请查收"}
    else:
        # Dev fallback
        logger.info("DEV verify code for %s: %s", email, code)
        return {"success": True, "message": "验证码已生成（开发模式）", "code": code}


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    token = getattr(current_user, "_current_token", None)
    if token:
        db.query(UserToken).filter(UserToken.token == token).delete()
    current_user.online = False
    db.commit()
    return {"success": True, "message": "退出成功"}
