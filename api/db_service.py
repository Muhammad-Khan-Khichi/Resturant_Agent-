"""
db_service.py

Database service layer used by:
    - FastAPI routes
    - Agent hooks / background tasks
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import (
    AgentTransition,
    CheckoutRecord,
    ConversationMessage,
    ConversationSession,
    SessionUserData,
)




async def create_session(
    db: AsyncSession,room_name: str,participant_name: str,user_id: str,) -> ConversationSession:
    """Create a new conversation session."""

    session = ConversationSession(
        room_name=room_name,
        participant_name=participant_name,
        user_id=user_id,
    )

    try:
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    except Exception:
        await db.rollback()
        raise


async def get_session_by_room(db: AsyncSession,room_name: str,) -> ConversationSession | None:
    """Return session by room name."""

    result = await db.execute(
        select(ConversationSession).where(
            ConversationSession.room_name == room_name
        )
    )

    return result.scalar_one_or_none()


async def end_session(db: AsyncSession,room_name: str,) -> None:
    """Mark session as ended."""

    session = await get_session_by_room(db, room_name)

    if not session:
        return

    try:
        session.ended_at = datetime.now(timezone.utc)
        await db.commit()

    except Exception:
        await db.rollback()
        raise



async def save_message(db: AsyncSession,room_name: str, role: str,content: str,agent_name: str | None = None,) -> None:
    """
    Save a single conversation message.
    """

    session = await get_session_by_room(db, room_name)

    if not session:
        return

    try:
        message = ConversationMessage(
            session_id=session.id,
            role=role,
            agent_name=agent_name,
            content=content,
        )

        db.add(message)
        await db.commit()

    except Exception:
        await db.rollback()
        raise


async def get_messages(db: AsyncSession,room_name: str,) -> list[ConversationMessage]:

    session = await get_session_by_room(db, room_name)

    if not session:
        return []

    result = await db.execute(
        select(ConversationMessage)
        .where(
            ConversationMessage.session_id == session.id
        )
        .order_by(ConversationMessage.timestamp)
    )

    return list(result.scalars().all())



async def save_transition(db: AsyncSession, room_name: str,from_agent: str,to_agent: str,) -> None:
    """Save agent handoff."""

    session = await get_session_by_room(db, room_name)

    if not session:
        return

    try:
        transition = AgentTransition(
            session_id=session.id,
            from_agent=from_agent,
            to_agent=to_agent,
        )

        db.add(transition)
        await db.commit()

    except Exception:
        await db.rollback()
        raise


async def get_transitions(db: AsyncSession, room_name: str,) -> list[AgentTransition]:

    session = await get_session_by_room(db, room_name)

    if not session:
        return []

    result = await db.execute(
        select(AgentTransition)
        .where(
            AgentTransition.session_id == session.id
        )
        .order_by(AgentTransition.timestamp)
    )

    return list(result.scalars().all())



async def save_userdata(
    db: AsyncSession,
    room_name: str,
    userdata,
) -> None:
    """
    Create or update SessionUserData.
    """

    session = await get_session_by_room(db, room_name)

    if not session:
        return

    try:
        result = await db.execute(
            select(SessionUserData).where(
                SessionUserData.session_id == session.id
            )
        )

        existing = result.scalar_one_or_none()

        if existing:
            existing.customer_name = userdata.customer_name
            existing.customer_phone = userdata.customer_phone
            existing.customer_email = userdata.customer_email
            existing.reservation_time = userdata.reservation_time
            existing.order = userdata.order

        else:
            db.add(
                SessionUserData(
                    session_id=session.id,
                    customer_name=userdata.customer_name,
                    customer_phone=userdata.customer_phone,
                    customer_email=userdata.customer_email,
                    reservation_time=userdata.reservation_time,
                    order=userdata.order,
                )
            )

        await db.commit()

    except Exception:
        await db.rollback()
        raise



async def save_checkout(
    db: AsyncSession,
    room_name: str,
    userdata,
) -> None:
    """
    Create or update checkout record.
    Stores only last 4 digits of card.
    """

    session = await get_session_by_room(db, room_name)

    if not session:
        return

    card_last4 = None

    if (
        getattr(userdata, "customer_credit_card", None)
        and len(userdata.customer_credit_card) >= 4
    ):
        card_last4 = userdata.customer_credit_card[-4:]

    try:
        result = await db.execute(
            select(CheckoutRecord).where(
                CheckoutRecord.session_id == session.id
            )
        )

        existing = result.scalar_one_or_none()

        if existing:
            existing.customer_name = userdata.customer_name
            existing.customer_phone = userdata.customer_phone
            existing.order = userdata.order
            existing.expense = userdata.expense
            existing.card_last4 = card_last4
            existing.checked_out = bool(
                userdata.checked_out
            )

        else:
            db.add(
                CheckoutRecord(
                    session_id=session.id,
                    customer_name=userdata.customer_name,
                    customer_phone=userdata.customer_phone,
                    order=userdata.order,
                    expense=userdata.expense,
                    card_last4=card_last4,
                    checked_out=bool(
                        userdata.checked_out
                    ),
                )
            )

        await db.commit()

    except Exception:
        await db.rollback()
        raise