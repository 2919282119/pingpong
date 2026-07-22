from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db import User, Friend, FriendRequest
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/list")
def get_friends_list(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    friends = db.query(Friend).filter(
        (Friend.userId1 == current_user.id) | (Friend.userId2 == current_user.id)
    ).all()

    if not friends:
        return {"success": True, "list": []}

    friend_ids = []
    for f in friends:
        fid = f.userId2 if f.userId1 == current_user.id else f.userId1
        friend_ids.append(fid)

    users = db.query(User).filter(User.id.in_(friend_ids)).all()
    list_data = []
    for u in users:
        exp_years = None
        if u.startPlayingYear:
            from datetime import datetime
            exp_years = datetime.now().year - int(u.startPlayingYear)

        online = False
        if u.lastActiveTime:
            delta = (__import__("datetime").datetime.now() - u.lastActiveTime).total_seconds()
            online = u.online and delta < 300

        list_data.append({
            "id": u.id,
            "nickname": u.name or "",
            "avatar": u.avatar or "",
            "gender": u.gender or "",
            "experience": exp_years,
            "playStyle": u.playStyle or "",
            "online": online,
        })

    return {"success": True, "list": list_data}


@router.get("/count")
def get_friends_count(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count = db.query(Friend).filter(
        (Friend.userId1 == current_user.id) | (Friend.userId2 == current_user.id)
    ).count()
    return {"success": True, "count": count}


@router.post("/request")
def send_friend_request(body: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    to_user_id = body.get("toUserId")
    if not to_user_id:
        raise HTTPException(status_code=400, detail="缺少目标用户ID")
    if to_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能添加自己为好友")

    existing = db.query(Friend).filter(
        ((Friend.userId1 == current_user.id) & (Friend.userId2 == to_user_id)) |
        ((Friend.userId1 == to_user_id) & (Friend.userId2 == current_user.id))
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="你们已经是好友了")

    pending = db.query(FriendRequest).filter(
        ((FriendRequest.fromUserId == current_user.id) & (FriendRequest.toUserId == to_user_id)) |
        ((FriendRequest.fromUserId == to_user_id) & (FriendRequest.toUserId == current_user.id)),
        FriendRequest.status == "pending",
    ).first()
    if pending:
        raise HTTPException(status_code=400, detail="已存在待处理的好友请求")

    req = FriendRequest(fromUserId=current_user.id, toUserId=to_user_id)
    db.add(req)
    db.commit()
    return {"success": True, "requestId": req.id}


@router.get("/requests")
def get_friend_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    requests = db.query(FriendRequest).filter(
        FriendRequest.toUserId == current_user.id,
        FriendRequest.status == "pending",
    ).order_by(FriendRequest.requestTime.desc()).all()

    list_data = []
    for r in requests:
        from_user = db.query(User).filter(User.id == r.fromUserId).first()
        list_data.append({
            "id": r.id,
            "fromUserId": r.fromUserId,
            "fromUserName": from_user.name if from_user else "",
            "fromUserAvatar": from_user.avatar if from_user else "",
            "requestTime": r.requestTime.isoformat() if r.requestTime else "",
        })

    return {"success": True, "list": list_data}


@router.put("/requests/{request_id}/handle")
def handle_friend_request(request_id: int, body: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    action = body.get("action")
    if action not in ("accept", "reject"):
        raise HTTPException(status_code=400, detail="无效的操作类型")

    fr = db.query(FriendRequest).filter(
        FriendRequest.id == request_id,
        FriendRequest.toUserId == current_user.id,
        FriendRequest.status == "pending",
    ).first()
    if fr is None:
        raise HTTPException(status_code=404, detail="好友请求不存在或已处理")

    from datetime import datetime
    fr.status = "accepted" if action == "accept" else "rejected"
    fr.handleTime = datetime.now()

    if action == "accept":
        uid1, uid2 = sorted([fr.fromUserId, fr.toUserId])
        existing = db.query(Friend).filter(
            Friend.userId1 == uid1, Friend.userId2 == uid2
        ).first()
        if existing is None:
            db.add(Friend(userId1=uid1, userId2=uid2))

    db.commit()
    return {"success": True, "message": "已同意好友请求" if action == "accept" else "已拒绝好友请求"}


@router.get("/check/{user_id}")
def check_friendship(user_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    is_friend = db.query(Friend).filter(
        ((Friend.userId1 == current_user.id) & (Friend.userId2 == user_id)) |
        ((Friend.userId1 == user_id) & (Friend.userId2 == current_user.id))
    ).first() is not None

    pending = db.query(FriendRequest).filter(
        ((FriendRequest.fromUserId == current_user.id) & (FriendRequest.toUserId == user_id)) |
        ((FriendRequest.fromUserId == user_id) & (FriendRequest.toUserId == current_user.id)),
        FriendRequest.status == "pending",
    ).first() is not None

    return {"success": True, "isFriend": is_friend, "hasPendingRequest": pending}
