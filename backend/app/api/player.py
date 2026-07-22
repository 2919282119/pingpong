from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db import User, Friend
from app.utils.distance import calculate_distance
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/nearby")
def get_nearby_players(
    latitude: float = None, longitude: float = None,
    page: int = 1, page_size: int = 20,
    gender: str = None, age_min: int = None, age_max: int = None,
    experience: int = None, play_style: str = None,
    keyword: str = None, min_distance: float = None, max_distance: float = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if latitude is None or longitude is None:
        raise HTTPException(status_code=400, detail="缺少经纬度参数")

    query = db.query(User).filter(User.id != current_user.id, User.latitude.isnot(None), User.longitude.isnot(None))
    if gender:
        query = query.filter(User.gender == gender)
    if play_style:
        query = query.filter(User.playStyle == play_style)
    if keyword:
        query = query.filter(User.name.like(f"%{keyword}%"))

    users = query.all()

    results = []
    for u in users:
        dist = calculate_distance(latitude, longitude, float(u.latitude), float(u.longitude))
        age = None
        if u.birthdate:
            today = datetime.now()
            age = today.year - u.birthdate.year
            if (today.month, today.day) < (u.birthdate.month, u.birthdate.day):
                age -= 1
        exp_years = None
        if u.startPlayingYear:
            exp_years = datetime.now().year - int(u.startPlayingYear)

        if age_min is not None and (age is None or age < age_min):
            continue
        if age_max is not None and (age is not None and age > age_max):
            continue
        if experience is not None and (exp_years is None or exp_years < experience):
            continue
        if min_distance is not None and dist < min_distance:
            continue
        if max_distance is not None and dist > max_distance:
            continue

        results.append({
            "id": u.id,
            "name": u.name or "",
            "avatar": u.avatar or "",
            "gender": u.gender or "",
            "age": age,
            "experience": exp_years,
            "playStyle": u.playStyle or "",
            "distance": dist,
            "introduction": u.selfDescription or "",
            "latitude": float(u.latitude),
            "longitude": float(u.longitude),
        })

    results.sort(key=lambda x: x["distance"])
    total = len(results)
    offset = (page - 1) * page_size
    page_items = results[offset:offset + page_size]

    return {"success": True, "list": page_items, "total": total, "page": page, "pageSize": page_size}


@router.get("/{player_id}")
def get_player_detail(
    player_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    player = db.query(User).filter(User.id == player_id).first()
    if player is None:
        raise HTTPException(status_code=404, detail="球友不存在")

    age = None
    if player.birthdate:
        today = datetime.now()
        age = today.year - player.birthdate.year
        if (today.month, today.day) < (player.birthdate.month, player.birthdate.day):
            age -= 1

    exp_years = None
    if player.startPlayingYear:
        exp_years = datetime.now().year - int(player.startPlayingYear)

    distance = None
    if current_user.latitude and current_user.longitude and player.latitude and player.longitude:
        distance = calculate_distance(
            float(current_user.latitude), float(current_user.longitude),
            float(player.latitude), float(player.longitude),
        )

    is_friend = db.query(Friend).filter(
        ((Friend.userId1 == current_user.id) & (Friend.userId2 == player_id)) |
        ((Friend.userId1 == player_id) & (Friend.userId2 == current_user.id))
    ).first() is not None

    return {
        "success": True,
        "id": player.id,
        "name": player.name or "",
        "avatar": player.avatar or "",
        "bgImg": player.bgImg or "",
        "gender": player.gender or "",
        "age": age,
        "experience": exp_years,
        "playStyle": player.playStyle or "",
        "distance": distance,
        "introduction": player.selfDescription or "",
        "latitude": float(player.latitude) if player.latitude else None,
        "longitude": float(player.longitude) if player.longitude else None,
        "isFriend": is_friend,
    }


@router.get("/{player_id}/location")
def get_player_location(
    player_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    player = db.query(User).filter(User.id == player_id).first()
    if player is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not player.latitude or not player.longitude:
        raise HTTPException(status_code=404, detail="用户未设置位置信息")
    return {
        "success": True,
        "latitude": float(player.latitude),
        "longitude": float(player.longitude),
        "address": player.address or "",
    }
