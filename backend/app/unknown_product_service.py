from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.enums import (
    InventoryMovementType,
    UnknownProductStatus,
)
from app.models import UnknownProduct


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