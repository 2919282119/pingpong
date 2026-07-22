from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db import User, ChatMessage
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/messages")
def get_messages(
    user_id: str = Query(None, alias="userId"),
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user_id:
        raise HTTPException(status_code=400, detail="缺少用户ID参数")

    limit = min(max(page_size, 1), 100)
    offset = max(page - 1, 0) * limit

    base_filter = (
        ((ChatMessage.fromUserId == current_user.id) & (ChatMessage.toUserId == user_id)) |
        ((ChatMessage.fromUserId == user_id) & (ChatMessage.toUserId == current_user.id))
    ) & ~ChatMessage.deletedBy.contains(current_user.id)

    total = db.query(ChatMessage).filter(base_filter).count()
    messages = db.query(ChatMessage).filter(base_filter).order_by(
        ChatMessage.createTime.desc()
    ).limit(limit).offset(offset).all()

    messages.reverse()

    return {
        "success": True,
        "list": [
            {
                "id": msg.id,
                "fromUserId": msg.fromUserId,
                "toUserId": msg.toUserId,
                "content": msg.content,
                "createTime": msg.createTime.isoformat(),
                "isRead": bool(msg.isRead),
            }
            for msg in messages
        ],
        "total": total,
    }


@router.post("/messages")
def send_message(body: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    to_user_id = body.get("toUserId")
    content = body.get("content")

    if not to_user_id or not content:
        raise HTTPException(status_code=400, detail="缺少必要参数")
    if to_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能向自己发送消息")

    msg = ChatMessage(fromUserId=current_user.id, toUserId=to_user_id, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return {
        "success": True,
        "messageId": msg.id,
        "createTime": msg.createTime.isoformat(),
    }


@router.get("/conversations")
def get_conversations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from sqlalchemy import text

    # Get conversation partners via raw SQL for max(createTime)
    sql = text("""
        SELECT
          CASE WHEN fromUserId = :uid THEN toUserId ELSE fromUserId END AS userId,
          MAX(createTime) as lastMessageTime
        FROM chat_messages
        WHERE (fromUserId = :uid OR toUserId = :uid2)
          AND NOT deletedBy LIKE :like_uid
        GROUP BY userId
        ORDER BY lastMessageTime DESC
    """)
    rows = db.execute(sql, {"uid": current_user.id, "uid2": current_user.id, "like_uid": f"%{current_user.id}%"}).fetchall()

    if not rows:
        return {"success": True, "list": []}

    user_ids = [r[0] for r in rows]
    users = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()}

    list_data = []
    for row in rows:
        uid = row[0]
        user = users.get(uid)
        if user is None:
            continue

        conv_filter = (
            ((ChatMessage.fromUserId == current_user.id) & (ChatMessage.toUserId == uid)) |
            ((ChatMessage.fromUserId == uid) & (ChatMessage.toUserId == current_user.id))
        ) & ~ChatMessage.deletedBy.contains(current_user.id)

        last_msg = db.query(ChatMessage).filter(conv_filter).order_by(
            ChatMessage.createTime.desc()
        ).first()

        unread = db.query(ChatMessage).filter(
            ChatMessage.fromUserId == uid,
            ChatMessage.toUserId == current_user.id,
            ChatMessage.isRead == False,
            ~ChatMessage.deletedBy.contains(current_user.id),
        ).count()

        list_data.append({
            "userId": uid,
            "userName": user.name or "",
            "userAvatar": user.avatar or "",
            "lastMessage": last_msg.content if last_msg else "",
            "lastMessageTime": last_msg.createTime.isoformat() if last_msg else "",
            "unreadCount": unread,
        })

    return {"success": True, "list": list_data}


@router.delete("/messages")
def clear_messages(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(
        (ChatMessage.fromUserId == current_user.id) | (ChatMessage.toUserId == current_user.id),
        ~ChatMessage.deletedBy.contains(current_user.id),
    ).all()
    for msg in messages:
        msg.deletedBy = (msg.deletedBy or "") + "," + current_user.id
    db.commit()
    return {"success": True}


@router.put("/messages/{message_id}/read")
def mark_message_read(message_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    msg = db.query(ChatMessage).filter(
        ChatMessage.id == message_id,
        ChatMessage.toUserId == current_user.id,
    ).first()
    if msg is None:
        raise HTTPException(status_code=404, detail="消息不存在")

    msg.isRead = True
    db.commit()
    return {"success": True}
