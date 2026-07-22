import json
import logging
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

from app.database import SessionLocal
from app.models.db import ChatMessage
from app.utils.auth import decode_token

logger = logging.getLogger(__name__)


class ChatWebSocket:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}  # userId -> ws

    async def handle(self, ws: WebSocket):
        await ws.accept()
        user_id = None

        try:
            while True:
                raw = await ws.receive_text()
                data = json.loads(raw)
                msg_type = data.get("type")

                if msg_type == "auth":
                    user_id = str(data.get("userId"))
                    self.connections[user_id] = ws
                    logger.info("WS user %s connected", user_id)

                elif msg_type == "chat" and user_id:
                    to_user_id = str(data.get("toUserId"))
                    content = data.get("content", "")

                    # Save to DB
                    db = SessionLocal()
                    try:
                        msg = ChatMessage(
                            fromUserId=user_id, toUserId=to_user_id,
                            content=content, isRead=False,
                        )
                        db.add(msg)
                        db.commit()
                        db.refresh(msg)

                        msg_data = {
                            "type": "chat",
                            "message": {
                                "id": msg.id,
                                "fromUserId": user_id,
                                "toUserId": to_user_id,
                                "content": content,
                                "createTime": msg.createTime.isoformat(),
                                "isRead": False,
                            },
                        }

                        # Send to receiver if online
                        receiver_ws = self.connections.get(to_user_id)
                        if receiver_ws and receiver_ws.client_state.name == "CONNECTED":
                            try:
                                await receiver_ws.send_json(msg_data)
                            except Exception:
                                pass

                        # Confirm to sender
                        await ws.send_json(msg_data)
                    finally:
                        db.close()

                elif msg_type == "mark_read" and user_id:
                    message_ids = data.get("messageIds", [])
                    if message_ids:
                        db = SessionLocal()
                        try:
                            db.query(ChatMessage).filter(
                                ChatMessage.id.in_(message_ids),
                                ChatMessage.toUserId == user_id,
                            ).update({"isRead": True})
                            db.commit()
                        finally:
                            db.close()

        except WebSocketDisconnect:
            if user_id and user_id in self.connections:
                del self.connections[user_id]
            logger.info("WS user %s disconnected", user_id)
        except Exception as e:
            logger.error("WS error for user %s: %s", user_id, e)
            if user_id and user_id in self.connections:
                del self.connections[user_id]


chat_ws = ChatWebSocket()
