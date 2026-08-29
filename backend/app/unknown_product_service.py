from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.enums import (
    InventoryMovementType,
    UnknownProductStatus,
)
from app.inventory_service import process_inventory_movement_with_event
from app.models import UnknownProduct


class UnknownProductNotFoundError(Exception):
    pass


class UnknownProductAlreadyReviewedError(Exception):
    pass


def create_unknown_product(
    db: Session,
    image_path: str,
    movement_type: InventoryMovementType,
    quantity: int,
) -> UnknownProduct:
    unknown_product = UnknownProduct(
        image_path=image_path,
        movement_type=movement_type,
        quantity=quantity,
        status=UnknownProductStatus.PENDING,
    )

    db.add(unknown_product)
    db.flush()

    return unknown_product


def list_unknown_products(
    db: Session,
) -> list[UnknownProduct]:
    return list(
        db.scalars(
            select(UnknownProduct)
            .options(
                selectinload(
                    UnknownProduct.resolved_product
                )
            )
            .order_by(
                UnknownProduct.detected_at.desc(),
                UnknownProduct.id.desc(),
            )
        ).all()
    )


def get_unknown_product_by_id(
    db: Session,
    unknown_product_id: int,
) -> UnknownProduct | None:
    return db.scalar(
        select(UnknownProduct)
        .options(
            selectinload(
                UnknownProduct.resolved_product
            )
        )
        .where(
            UnknownProduct.id == unknown_product_id
        )
    )


def get_pending_unknown_product(
    db: Session,
    unknown_product_id: int,
) -> UnknownProduct:
    unknown_product = get_unknown_product_by_id(
        db,
        unknown_product_id,
    )

    if unknown_product is None:
        raise UnknownProductNotFoundError(
            f"Produto desconhecido {unknown_product_id} não encontrado."
        )

    if unknown_product.status != UnknownProductStatus.PENDING:
        raise UnknownProductAlreadyReviewedError(
            f"Produto desconhecido {unknown_product_id} já foi revisado."
        )

    return unknown_product


def dismiss_unknown_product(
    db: Session,
    unknown_product_id: int,
) -> UnknownProduct:
    unknown_product = get_pending_unknown_product(
        db,
        unknown_product_id,
    )

    unknown_product.status = UnknownProductStatus.DISMISSED
    unknown_product.reviewed_at = datetime.now(timezone.utc).replace(
        tzinfo=None
    )
    unknown_product.resolved_product_id = None

    db.flush()

    return unknown_product


def resolve_unknown_product(
    db: Session,
    unknown_product_id: int,
    resolved_product_id: int,
):
    unknown_product = get_pending_unknown_product(
        db,
        unknown_product_id,
    )

    inventory_item, event = process_inventory_movement_with_event(
        db,
        product_id=resolved_product_id,
        movement_type=unknown_product.movement_type,
        quantity=unknown_product.quantity,
        event_timestamp=unknown_product.detected_at,
    )

    unknown_product.status = UnknownProductStatus.RESOLVED
    unknown_product.reviewed_at = datetime.now(
        timezone.utc
    ).replace(tzinfo=None)
    unknown_product.resolved_product_id = resolved_product_id

    db.flush()

    return unknown_product, inventory_item, event