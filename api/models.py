import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database import Base

def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String,unique=True,nullable=False,index=True,)
    hashed_password: Mapped[str] = mapped_column(String,nullable=False,)
    full_name: Mapped[str] = mapped_column(String,nullable=False,)
    is_active: Mapped[bool] = mapped_column(Boolean,nullable=False,default=True,)
    created_at: Mapped[datetime] = mapped_column(DateTime,server_default=func.now(),)
    sessions: Mapped[list["ConversationSession"]] = relationship(back_populates="user",cascade="all, delete-orphan",)


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"
    id: Mapped[str] = mapped_column(String,primary_key=True,default=_uuid,)
    room_name: Mapped[str] = mapped_column(String,unique=True,nullable=False,index=True,)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),nullable=False,index=True,)
    participant_name: Mapped[str] = mapped_column(String,nullable=False,)
    started_at: Mapped[datetime] = mapped_column(DateTime,server_default=func.now(),)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime,nullable=True,)
    user: Mapped["User"] = relationship(back_populates="sessions",)
    messages: Mapped[list["ConversationMessage"]] = relationship(back_populates="session",cascade="all, delete-orphan",)
    userdata: Mapped["SessionUserData | None"] = relationship(back_populates="session",uselist=False,cascade="all, delete-orphan",single_parent=True,)
    transitions: Mapped[list["AgentTransition"]] = relationship(back_populates="session",cascade="all, delete-orphan",)
    checkout: Mapped["CheckoutRecord | None"] = relationship(back_populates="session",uselist=False,cascade="all, delete-orphan",single_parent=True,)


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(String,primary_key=True,default=_uuid,)
    session_id: Mapped[str] = mapped_column(ForeignKey("conversation_sessions.id", ondelete="CASCADE"),nullable=False,index=True,)
    role: Mapped[str] = mapped_column(String,nullable=False,)
    agent_name: Mapped[str] = mapped_column(String,nullable=False,)
    content: Mapped[str] = mapped_column(Text,nullable=False,)
    timestamp: Mapped[datetime] = mapped_column(DateTime,server_default=func.now(),index=True,)
    session: Mapped["ConversationSession"] = relationship(back_populates="messages",)


class AgentTransition(Base):
    __tablename__ = "agent_transitions"

    id: Mapped[str] = mapped_column(String,primary_key=True,default=_uuid,)
    session_id: Mapped[str] = mapped_column(ForeignKey("conversation_sessions.id", ondelete="CASCADE"),nullable=False,index=True,)
    from_agent: Mapped[str] = mapped_column(String,nullable=False,)
    to_agent: Mapped[str] = mapped_column(String,nullable=False,)
    timestamp: Mapped[datetime] = mapped_column(DateTime,server_default=func.now(),index=True,)
    session: Mapped["ConversationSession"] = relationship(back_populates="transitions",)


class SessionUserData(Base):
    __tablename__ = "session_userdata"
    id: Mapped[str] = mapped_column(String,primary_key=True,default=_uuid,)
    session_id: Mapped[str] = mapped_column(ForeignKey("conversation_sessions.id", ondelete="CASCADE"),unique=True,nullable=False,)
    customer_name: Mapped[str] = mapped_column(String,nullable=False,)
    customer_phone: Mapped[str] = mapped_column(String,nullable=False,index=True,)
    customer_email: Mapped[str] = mapped_column(String,nullable=False,index=True,)
    reservation_time: Mapped[str] = mapped_column(String,nullable=False,)
    order: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON,nullable=True,)
    session: Mapped["ConversationSession"] = relationship(back_populates="userdata",)


class CheckoutRecord(Base):
    __tablename__ = "checkout_records"
    id: Mapped[str] = mapped_column(String,primary_key=True,default=_uuid,)
    session_id: Mapped[str] = mapped_column(ForeignKey("conversation_sessions.id", ondelete="CASCADE"),unique=True,nullable=False,)
    customer_name: Mapped[str] = mapped_column(String,nullable=False,)
    customer_phone: Mapped[str] = mapped_column(String,nullable=False,index=True,)
    order: Mapped[list[dict[str, Any]]] = mapped_column(JSON,nullable=False,)
    expense: Mapped[float] = mapped_column(Float,nullable=False,)
    card_last4: Mapped[str] = mapped_column(String(4),nullable=False,)
    checked_out: Mapped[bool] = mapped_column(Boolean,nullable=False,default=False,)
    created_at: Mapped[datetime] = mapped_column(DateTime,server_default=func.now(),index=True,)
    session: Mapped["ConversationSession"] = relationship(back_populates="checkout",)