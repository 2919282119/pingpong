import random
import string
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Date, Text, DECIMAL, ForeignKey, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


def generate_user_id() -> str:
    chars = string.ascii_uppercase + string.digits
    prefix = "".join(random.choices(chars, k=4))
    suffix = f"{random.randint(0, 999):03d}"
    return f"{prefix}{suffix}"


class User(Base):
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, default=generate_user_id)
    email = Column(String(100), unique=True)
    password = Column(String(255))
    name = Column(String(50))
    avatar = Column(String(500))
    bgImg = Column(String(500))
    gender = Column(String(10))
    birthdate = Column(Date)
    startPlayingYear = Column(String(10))
    playStyle = Column(String(50))
    selfDescription = Column(Text)
    address = Column(String(200))
    latitude = Column(DECIMAL(10, 7))
    longitude = Column(DECIMAL(10, 7))
    online = Column(Boolean, default=False)
    lastActiveTime = Column(DateTime)
    createdAt = Column(DateTime, default=datetime.now)
    updatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class UserToken(Base):
    __tablename__ = "user_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    expiresAt = Column(DateTime, nullable=False)
    createdAt = Column(DateTime, default=datetime.now)

    user = relationship("User")


class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fromUserId = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    toUserId = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="pending")
    requestTime = Column(DateTime, default=datetime.now)
    handleTime = Column(DateTime)
    createdAt = Column(DateTime, default=datetime.now)
    updatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (UniqueConstraint("fromUserId", "toUserId"),)


class Friend(Base):
    __tablename__ = "friends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    userId1 = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    userId2 = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    createdAt = Column(DateTime, default=datetime.now)

    __table_args__ = (UniqueConstraint("userId1", "userId2"),)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fromUserId = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    toUserId = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    isRead = Column(Boolean, default=False)
    deletedBy = Column(String(500), nullable=False, server_default="", default="")
    createTime = Column(DateTime, default=datetime.now)

    __table_args__ = (Index("idx_conversation", "fromUserId", "toUserId", "createTime"),)


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    inviteNotification = Column(Boolean, default=True)
    messageNotification = Column(Boolean, default=True)
    createdAt = Column(DateTime, default=datetime.now)
    updatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class VerifyCode(Base):
    __tablename__ = "verify_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), nullable=False)
    code = Column(String(10), nullable=False)
    type = Column(String(20), default="register")
    expiresAt = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    createdAt = Column(DateTime, default=datetime.now)
