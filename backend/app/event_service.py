from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.enums import InventoryMovementType
from app.models import Event


def create_event(
    db: Session,
    product_id: int,
    event_type: InventoryMovementType,
    quantity: int,
) -> Event:
    event = Event(
        product_id=product_id,
        event_type=event_type,
        quantity=quantity,
    )

    db.add(event)
    db.flush()

    return event


def list_events(db: Session) -> list[Event]:
    return list(
        db.scalars(
            select(Event)
            .options(selectinload(Event.product))
            .order_by(
                Event.timestamp.desc(),
                Event.id.desc(),
            )
        ).all()
    )