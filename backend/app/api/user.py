from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db import User, UserSettings
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/info")
def get_user_info(current_user: User = Depends(get_current_user)):
    u = current_user
    age = None
    if u.birthdate:
        today = datetime.now()
        age = today.year - u.birthdate.year
        if (today.month, today.day) < (u.birthdate.month, u.birthdate.day):
            age -= 1

    return {
        "success": True,
        "id": u.id,
        "name": u.name or "",
        "avatar": u.avatar or "",
        "gender": u.gender or "",
        "birthdate": str(u.birthdate) if u.birthdate else "",
        "startPlayingYear": u.startPlayingYear or "",
        "playStyle": u.playStyle or "",
        "selfDescription": u.selfDescription or "",
        "bgImg": u.bgImg or "",
        "phone": "",
        "address": u.address or "",
        "latitude": float(u.latitude) if u.latitude else None,
        "longitude": float(u.longitude) if u.longitude else None,
        "age": age,
    }


@router.put("/info")
def update_user_info(body: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    allowed = {"name", "avatar", "bgImg", "gender", "birthdate",
               "startPlayingYear", "playStyle", "selfDescription", "address",
               "latitude", "longitude"}
    for key, val in body.items():
        if key in allowed:
            # MySQL 严格模式下 DATE 列不接受空字符串，未填时存 NULL
            if key == "birthdate" and val == "":
                val = None
            setattr(current_user, key, val)
    db.commit()
    return {"success": True, "userInfo": {
        "id": current_user.id,
        "name": current_user.name or "",
        "avatar": current_user.avatar or "",
        "gender": current_user.gender or "",
        "birthdate": str(current_user.birthdate) if current_user.birthdate else "",
        "startPlayingYear": current_user.startPlayingYear or "",
        "playStyle": current_user.playStyle or "",
        "selfDescription": current_user.selfDescription or "",
        "bgImg": current_user.bgImg or "",
        "address": current_user.address or "",
        "latitude": float(current_user.latitude) if current_user.latitude else None,
        "longitude": float(current_user.longitude) if current_user.longitude else None,
    }}


@router.put("/location")
def update_location(body: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lat = body.get("latitude")
    lng = body.get("longitude")
    if lat is None or lng is None:
        raise HTTPException(status_code=400, detail="缺少经纬度参数")

    lat_f, lng_f = float(lat), float(lng)
    if lat_f < -90 or lat_f > 90 or lng_f < -180 or lng_f > 180:
        raise HTTPException(status_code=400, detail="经纬度参数无效")

    current_user.latitude = lat_f
    current_user.longitude = lng_f

    addr = body.get("address")
    if addr:
        current_user.address = addr
    else:
        from app.services.baidu_map import reverse_geocode
        resolved = reverse_geocode(lat_f, lng_f)
        if resolved:
            current_user.address = resolved

    db.commit()
    return {"success": True, "message": "位置更新成功"}


@router.get("/settings")
def get_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.query(UserSettings).filter(UserSettings.userId == current_user.id).first()
    if s is None:
        s = UserSettings(userId=current_user.id)
        db.add(s)
        db.commit()
    return {
        "success": True,
        "notifications": {
            "invite": bool(s.inviteNotification),
            "message": bool(s.messageNotification),
        }
    }


@router.put("/settings")
def update_settings(body: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notif = body.get("notifications")
    if not notif:
        raise HTTPException(status_code=400, detail="缺少设置参数")

    s = db.query(UserSettings).filter(UserSettings.userId == current_user.id).first()
    if s is None:
        s = UserSettings(userId=current_user.id)
        db.add(s)
    if "invite" in notif:
        s.inviteNotification = bool(notif["invite"])
    if "message" in notif:
        s.messageNotification = bool(notif["message"])
    db.commit()
    return {"success": True, "message": "设置更新成功"}
